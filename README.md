# 🦅 OpenPlag Pro: AI-Powered Open Source Plagiarism Detector

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Framework-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![AI Model](https://img.shields.io/badge/Model-SBERT%20(MiniLM)-green?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

**OpenPlag Pro** is a rigorous, 100% free, open-source alternative to commercial plagiarism checkers like Turnitin. 

Unlike simple "exact match" checkers, OpenPlag Pro uses **Deep Learning (BERT embeddings)** to understand the *semantic meaning* of text, allowing it to detect paraphrasing and "smart" plagiarism. It checks submissions against a **Local Repository** (to prevent peer copying) and the **Live Internet** (using deep web scraping).

---

## 🌟 Key Features

* **🧠 Semantic Analysis:** Uses `sentence-transformers` (SBERT) to detect plagiarism even if words are swapped or sentences are restructured (Paraphrasing detection).
* **🌐 Live Web Search:** Automatic fingerprinting and searching via DuckDuckGo (No API keys required).
* **🕷️ Deep Scraping:** Doesn't just check search snippets—it visits the detected URLs, strips the HTML, and reads the full content for rigorous comparison.
* **📂 Multi-Format Support:** Natively parses `.pdf`, `.docx`, and `.txt` files.
* **🏛️ Internal Repository:** Automatically builds a local SQLite database of all past submissions to detect student-to-student copying.
* **💸 100% Free:** No API costs, no subscription fees. Runs entirely on your local machine.

---

## 🛠️ Tech Stack

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | [Streamlit](https://streamlit.io/) | Interactive Web UI |
| **AI / Logic** | [Sentence-Transformers](https://www.sbert.net/) | Semantic Embeddings & Cosine Similarity |
| **Search** | [DuckDuckGo Search](https://pypi.org/project/duckduckgo-search/) | Searching the web without API keys |
| **Scraping** | BeautifulSoup4 & Requests | Extracting text from live websites |
| **Database** | SQLite3 | Storing past submissions |
| **Parsing** | `pypdf` & `python-docx` | Handling document uploads |

---

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone [https://github.com/your-username/OpenPlag-Pro.git](https://github.com/anshuman-sahoo1999/openplagpro.git)
cd openplagpro
