import streamlit as st
import sqlite3
import hashlib
import requests
import re
import time
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer, util
from duckduckgo_search import DDGS
import pypdf
import docx

# --- CONFIGURATION ---
DATABASE_FILE = "submission_archive_v2.db"
# We use a lightweight BERT model optimized for speed and semantic similarity
MODEL_NAME = 'all-MiniLM-L6-v2'


# --- LOAD AI MODEL (Cached for Speed) ---
@st.cache_resource
def load_model():
    return SentenceTransformer(MODEL_NAME)


model = load_model()


# --- FILE PARSING MODULE ---
def extract_text_from_pdf(file):
    try:
        pdf_reader = pypdf.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return str(e)


def extract_text_from_docx(file):
    try:
        doc = docx.Document(file)
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        return str(e)


# --- DATABASE MANAGEMENT ---
def init_db():
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS submissions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  student_name TEXT, 
                  filename TEXT,
                  content TEXT, 
                  content_hash TEXT UNIQUE)''')
    conn.commit()
    conn.close()


def save_to_db(name, filename, content):
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
    try:
        c.execute("INSERT INTO submissions (student_name, filename, content, content_hash) VALUES (?, ?, ?, ?)",
                  (name, filename, content, content_hash))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def fetch_internal_db():
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute("SELECT student_name, filename, content FROM submissions")
    data = c.fetchall()
    conn.close()
    return data


# --- RIGOROUS SEARCH ENGINE ---
def scrape_url_content(url):
    """Visits a URL and extracts the main text content."""
    try:
        # User-Agent is crucial to avoid being blocked by websites
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Kill all script and style elements
        for script in soup(["script", "style"]):
            script.extract()

        text = soup.get_text()
        # Break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines())
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        return text[:10000]  # Limit to first 10k chars to save memory
    except:
        return ""


def deep_web_search(text, num_queries=3):
    """
    1. Extracts search terms.
    2. Searches DuckDuckGo.
    3. VISITS the top results and scrapes content.
    """
    # Create search queries from the most unique sentences
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)
    long_sentences = sorted([s for s in sentences if len(s) > 40], key=len, reverse=True)[:num_queries]

    potential_sources = []

    with DDGS() as ddgs:
        for query in long_sentences:
            try:
                results = list(ddgs.text(query[:200], max_results=2))
                for res in results:
                    potential_sources.append(res['href'])
                time.sleep(0.5)
            except:
                pass

    # Deduplicate URLs
    unique_urls = list(set(potential_sources))
    scraped_data = []

    # Progress bar for scraping
    if unique_urls:
        progress_text = "Visiting detected websites..."
        my_bar = st.progress(0, text=progress_text)

        for i, url in enumerate(unique_urls):
            content = scrape_url_content(url)
            if content:
                scraped_data.append({'source': url, 'content': content, 'type': 'Web'})
            my_bar.progress((i + 1) / len(unique_urls), text=f"Scraping {url}...")

        my_bar.empty()

    return scraped_data


# --- AI SIMILARITY ENGINE ---
def compute_semantic_similarity(source_text, target_text):
    """
    Uses BERT embeddings to find similarity.
    This detects paraphrasing, not just exact word matches.
    """
    # Split texts into chunks to handle long documents (BERT limit is usually 512 tokens)
    # For simplicity here, we truncate or treat as one block depending on length.
    # In a full production system, you'd use a sliding window.

    embedding_1 = model.encode(source_text, convert_to_tensor=True)
    embedding_2 = model.encode(target_text, convert_to_tensor=True)

    score = util.pytorch_cos_sim(embedding_1, embedding_2)
    return score.item()


# --- FRONTEND ---
def main():
    st.set_page_config(page_title="OpenPlag PRO", layout="wide")

    st.title("🦅 OpenPlag PRO")
    st.markdown("### Deep Learning Powered Plagiarism Detection")
    st.info("Supported: .txt, .pdf, .docx | Checks: Local Database + Live Internet")

    init_db()

    with st.sidebar:
        st.header("Admin Panel")
        db_data = fetch_internal_db()
        st.metric("Repository Size", f"{len(db_data)} Docs")
        if st.button("Refresh / Clear DB"):
            import os
            try:
                os.remove(DATABASE_FILE)
                st.rerun()
            except:
                pass

    # --- INPUT SECTION ---
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("1. Upload Document")
        student_name = st.text_input("Student Name")
        uploaded_file = st.file_uploader("Upload File", type=['txt', 'pdf', 'docx'])

    if uploaded_file and student_name:
        # Extract Text
        file_ext = uploaded_file.name.split('.')[-1].lower()
        if file_ext == 'pdf':
            extracted_text = extract_text_from_pdf(uploaded_file)
        elif file_ext == 'docx':
            extracted_text = extract_text_from_docx(uploaded_file)
        else:
            extracted_text = uploaded_file.read().decode("utf-8")

        # Show Preview
        with col2:
            st.subheader("2. Content Preview")
            st.text_area("Extracted Text", extracted_text, height=200)

            check_btn = st.button("🚀 Run Rigorous Check", type="primary")

        if check_btn:
            if len(extracted_text) < 50:
                st.error("Text too short for rigorous analysis.")
            else:
                st.divider()
                st.subheader("3. Analysis Report")

                # A. INTERNAL CHECK
                internal_matches = []
                for db_name, db_file, db_content in db_data:
                    sim_score = compute_semantic_similarity(extracted_text, db_content)
                    if sim_score > 0.4:  # BERT threshold
                        internal_matches.append({'source': f"Internal: {db_name} ({db_file})", 'score': sim_score})

                # B. EXTERNAL CHECK
                web_matches = []
                scraped_sources = deep_web_search(extracted_text)

                for source in scraped_sources:
                    sim_score = compute_semantic_similarity(extracted_text, source['content'])
                    if sim_score > 0.3:  # Web content is noisier, lower threshold
                        web_matches.append({'source': source['source'], 'score': sim_score})

                # C. RESULTS DISPLAY
                all_matches = sorted(internal_matches + web_matches, key=lambda x: x['score'], reverse=True)

                if not all_matches:
                    st.success("✅ Clean! No significant similarity found.")
                    max_score = 0
                else:
                    max_score = all_matches[0]['score']
                    if max_score > 0.8:
                        st.error(f"🚨 CRITICAL: {max_score * 100:.2f}% Similarity Detected")
                    elif max_score > 0.5:
                        st.warning(f"⚠️ MODERATE: {max_score * 100:.2f}% Similarity Detected")

                    st.write("### Top Sources Found:")
                    for match in all_matches[:5]:  # Show top 5
                        st.progress(match['score'], text=f"{match['score'] * 100:.1f}% - {match['source']}")

                # D. SAVE OPTION
                if st.button("💾 Archive this paper"):
                    if save_to_db(student_name, uploaded_file.name, extracted_text):
                        st.success("Archived to repository.")
                    else:
                        st.warning("Already exists in repository.")


if __name__ == "__main__":
    main()