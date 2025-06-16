# Retrieval-Augmented Generation (RAG) System with Dynamic Web Corpus

## Project Introduction

This repository hosts an Information Retrieval project focused on building a Retrieval-Augmented Generation (RAG) system. Unlike traditional IR systems that operate on static datasets, our system dynamically creates its own document corpus by crawling the web. This custom-built corpus is then leveraged to answer natural language queries by a Language Model (LLM), providing contextually relevant and accurate responses.

The project demonstrates the end-to-end process of web content acquisition, processing, indexing, and retrieval, combining classic IR principles with modern LLM capabilities.

## Project Structure

The repository is organized into three main directories, reflecting the logical flow of our system:

```bash
.
├── crawling/
├── scraping/
└── retrieving/
```

### `crawling/`

This directory contains the core logic for our web crawler. Its responsibilities include:

- **URL Frontier Management**: Implements a dual-queue system to manage the crawling frontier. It uses a standard queue for broad exploration and a high-priority queue for pages requiring frequent updates (e.g., live blogs).
- **HTTP Requests**: Handles fetching web pages from the internet using the requests library.
- **Politeness**: Ensures adherence to robots.txt directives and implements a configurable time delay between requests to avoid overloading web servers.
- **Robustness**: Incorporates heuristics to prevent common "spider traps," including a limit on crawling depth (MAX_DEPTH) and a cap on the total number of pages to process (MAX_PAGES_TO_CRAWL).
- **Freshness Policy**: Actively identifies pages with high-change-rate patterns (e.g., URLs containing /live/) and re-crawls them periodically to ensure the corpus remains up-to-date.

### `scraping/`

This directory focuses on processing the raw HTML content fetched by the crawler, turning it into a clean, structured, and non-redundant collection of documents. Its key functionalities are:

- **HTML Parsing**: Uses BeautifulSoup4 to parse HTML and enable DOM navigation.
- **Article Filtering**: Employs a set of heuristics to distinguish valid articles from other page types (e.g., homepages, category listings). This includes:

  - URL Structure Analysis: Filters for URLs matching a typical article pattern (e.g., containing a date like /YYYY/MM/DD/).

  - Content Length Analysis: Discards pages with a word count below a defined threshold (MIN_ARTICLE_WORDS).

- **Main Content Extraction**: Isolates the primary text of an article by searching for specific HTML containers (e.g., <div class="entry-content">) and implements fallback strategies for robustness.
- **Link Extraction:** Identifying and extracting all internal and external hyperlinks present on a page to feed back into the `crawling` module's URL frontier.
- **Duplicate Detection**: Prevents re-processing of the same article by checking the URL of each candidate page against the existing document_list.json index.

### `retrieving/`

This directory contains all components related to the retrieval phase of the RAG pipeline. It operates on cleaned `.txt` documents and the associated `document_list.json` file, aiming to retrieve the most relevant text chunks for a given query using a hybrid approach.

---

### Main Components

#### 1. Chunking (`utils/chunking.py`)

Each document is split into overlapping chunks based on token count (default: 512 tokens with 30-token overlap).

#### 2. Embedding and Vector Index (`embedding/embedding_model.py`, `indexing/vector_index.py`)

Each chunk is converted into a dense vector using the **BAAI/bge-small-en-v1.5** embedding model. All vectors are normalized and stored in a matrix. Retrieval is performed using cosine similarity.

#### 3. Inverted Index (`indexing/inverted_index.py`)

A custom inverted index is built from scratch. It maps each stemmed token to the list of chunk IDs where it appears, along with the term frequency. Chunk lengths and average document length are also stored for use in BM25 scoring.

#### 4. Keyword Scoring (`scoring/keyword_scorer.py`)

BM25 is implemented from scratch. Scores are computed for each chunk containing query terms. These scores are **normalized to the [0, 1] range** using min-max scaling to enable weighted combination with vector scores.

#### 5. Stemming (`stemming/`)

Two interchangeable stemmers are available:

- `SimpleStemmer`: a basic rule-based implementation.
- `CustomStemmer`: based on **NLTK’s PorterStemmer**.

You can switch between them by modifying the import in `inverted_index.py` and `keyword_scorer.py`.

#### 6. Hybrid Retriever (`hybrid_retriever/hybrid_retriever.py`)

The hybrid retriever combines vector and keyword scores using a weighted average:

`final_score = α * vector_score + (1 - α) * keyword_score`

The `alpha` parameter is configurable. Since both score types are normalized, the final score is also in the [0, 1] range.

---

### Directory Structure

```bash
retrieving/
├─ embedding/
│ └─ embedding_model.py
├─ indexing/
│ ├─ inverted_index.py
│ └─ vector_index.py
├─ scoring/
│ ├─ keyword_scorer.py
│ └─ vectorial_scorer.py
├─ stemming/
│ ├─ simple_stemmer.py
│ └─ custom_stemmer.py
├─ hybrid_retriever/
│ └─ hybrid_retriever.py
├─ utils/
│ ├─ chunking.py
│ ├─ data_loader.py
│ └─ models.py
│ └─ storage.py
└─ main.py
```

### Notes

- The entire indexing and scoring logic is implemented from scratch (no external IR libraries are used).
- The design is modular: you can independently test vector retrieval, keyword retrieval, or the combined hybrid strategy.

## Key Features

- **Dynamic Corpus Generation:** Builds its own dataset through controlled web crawling.
- **Intelligent Content Extraction:** Focuses on relevant main content, minimizing noise.
- **Duplicate Content Handling:** Avoids redundancy by detecting and managing duplicate and near-duplicate pages.
- **Hybrid Retrieval System:** Combines the strengths of modern vectorial search with traditional keyword-based methods for robust retrieval.
- **Natural Language Querying:** Utilizes RAG to answer free-form text queries effectively.

## Setup and Installation

To set up the project locally, follow these steps:

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/TommasoMoro03/IR-group-project.git](https://github.com/TommasoMoro03/IR-group-project.git)
    cd IR-group-project
    ```
2.  **Create a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: `venv\Scripts\activate`
    ```
3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

Instructions on how to run the crawler, process the data, and interact with the RAG system will be provided here.

1.  **Configure Crawler:** (e.g., specify seed URLs, domain limits)
2.  **Run Crawler:** `python crawling/main_crawler.py`
3.  **Process Scraped Data:** `python scraping/process_data.py`
4.  **Build Retriever Index:** `python retrieving/build_index.py`
5.  **Start RAG System:** `python retrieving/run_rag.py`

## Team Members

- Tommaso Moro
- Margherita Necchi
- Ester De Giosa
