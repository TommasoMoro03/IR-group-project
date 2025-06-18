# Hybrid Retriever implementation with scraped Web Corpus

## Project Introduction

This repository hosts an Information Retrieval project focused on building a hybrid retriever system.
Our system creates its own document corpus by crawling the web. This custom-built corpus is then leveraged to
retrieve the most relevant documents given a certain user query.

The project demonstrates the end-to-end process of web content acquisition, processing, indexing, and retrieval, combining classic IR principles with modern embedding capabilities.

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
- **Freshness Policy**: Actively identifies pages with high-change-rate patterns (e.g., URLs containing /live/) and re-crawls them periodically.
- **Persistent State**: To allow crawling sessions to be paused and resumed, the crawler implements a persistent state mechanism. Before exiting (either normally or via interruption), it saves the current state of its queues (exploration frontier, high-priority queue) and the set of visited URLs to disk in a \_crawler_state folder. Upon startup, it automatically loads this state, allowing it to continue exactly where it left off without losing progress or the list of live pages to re-crawl.

There is also the option to set a parameter, --new, which allows the user to decide whether to completely refresh the crawling session,deleting the saved .txt files and the JSON file, or to resume the previous session by updating the live pages and continuing the crawl.

### `scraping/`

This directory focuses on processing the raw HTML content fetched by the crawler, turning it into a clean, structured, and non-redundant collection of documents. Its key functionalities are:

- **HTML Parsing**: Uses BeautifulSoup4 to parse HTML and enable DOM navigation.
- **Article Filtering (quality insurance)**: Employs a set of heuristics to distinguish valid articles from other page types (e.g., homepages, category listings). This includes:

  - URL Structure Analysis: Filters for URLs matching a typical article pattern (e.g., containing a date like /YYYY/MM/DD/).

  - Content Length Analysis: Discards pages with a word count below a defined threshold (MIN_ARTICLE_WORDS).

- **Main Content Extraction**: Isolates the primary text of an article by searching for specific HTML containers (e.g., <div class="entry-content">), made by looking at the DOM.

- **Link Extraction**: Extracts all internal and external hyperlinks present on a page to feed back into the crawling module's URL frontier.

- **Duplicate and Update Logic**: Implements a two-tiered system to handle redundant content. It first checks an article's URL against the index. If the URL is new, it then calculates a content checksum (hash) to detect and discard pages with identical content coming from different URLs. For known live pages, instead of discarding, it updates the existing document and its metadata to reflect the latest version (the update is done only if the page has been updated).

### `retrieving/`

This directory contains all components related to the hybrid retriever. It operates on cleaned `.txt` documents and the associated `document_list.json` file, aiming to retrieve the most relevant text chunks for a given query using a hybrid approach.

---

#### Main Components

##### 1. Chunking (`utils/chunking.py`)

Each document is split into overlapping chunks based on token count (default: 512 tokens with 30-token overlap).
The choice of splitting the articles in chunk and work on them instead of the whole articles derives from the fact that the semantic vector
retriever performs very poorly if the texts have different lengths.

##### 2. Embedding and Vector Index (`embedding/embedding_model.py`, `indexing/vector_index.py`)

Each chunk is converted into a dense vector using the **BAAI/bge-small-en-v1.5** embedding model. All vectors are normalized and stored in a matrix. Retrieval is performed using cosine similarity.

##### 3. Inverted Index (`indexing/inverted_index.py`)

A custom inverted index is built from scratch. It maps each stemmed token to the list of chunk IDs where it appears, along with the term frequency. Chunk lengths and average document length are also stored for use in BM25 scoring.

##### 4. Keyword Scoring (`scoring/keyword_scorer.py`)

BM25 is implemented from scratch. Scores are computed for each chunk containing query terms. These scores are **normalized to the [0, 1] range** using min-max scaling to enable weighted combination with vector scores.

##### 5. Stemming (`stemming/`)

Two interchangeable stemmers are available:

- `SimpleStemmer`: a basic rule-based implementation.
- `CustomStemmer`: based on **NLTK’s SnowballStemmer**.

You can switch between them by modifying the import in `inverted_index.py` and `keyword_scorer.py`.

##### 6. Hybrid Retriever (`hybrid_retriever/hybrid_retriever.py`)

The hybrid retriever combines vector and keyword scores using a weighted average:

`final_score = α * vector_score + (1 - α) * keyword_score`

The `alpha` parameter is configurable. Since both score types are normalized, the final score is also in the [0, 1] range.

---

#### Directory Structure

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
└─ retriever.py
```

#### Notes

- The implementation included also a part for data consistency: instead of calculating chunks and indexes every time, if they are present in the disk then they are simply loaded.
- The design is modular: you can independently test vector retrieval, keyword retrieval, or the combined hybrid strategy.

## Installation and Usage

To set up the project locally, follow these steps:

1.  **Create a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    ```
    ```bash
    source venv/bin/activate  # On Windows: `venv\Scripts\activate`
    ```
2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Execute the main file**
    ```bash
     python main.py --new
    ```
    Note that it is possible to run crawler and retriever separately.

## Team Members

- Tommaso Moro
- Margherita Necchi
- Ester De Giosa
