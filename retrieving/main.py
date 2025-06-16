import os
from typing import Dict

from retrieving.embedding.embedding_models import EmbeddingModel
from retrieving.hybrid_retriever.hybrid_retriever import HybridRetriever
from retrieving.indexing.inverted_index import InvertedIndex
from retrieving.indexing.vector_index import VectorIndex
from retrieving.scoring.keyword_scorer import KeywordScorer
from retrieving.scoring.vectorial_scorer import VectorialScorer
from utils.data_loader import load_documents_from_json
from utils.chunking import Chunker
from utils.storage import save_chunks_to_json, load_chunks_from_json
from retrieving.utils.models import Chunk

# --- configuration ---
INDEX_DIR = "data/indices" # directory to save/load indices
CHUNKS_FILE = "data/chunks/chunks.json"
DOCUMENTS_FILE = "document_list.json"
TEXTS_FOLDER = "documents"

# ensure index directory exists
os.makedirs(INDEX_DIR, exist_ok=True)

# -- BUILD OR LOAD CHUNKS --
try:
    # if chunks have already been created then just load them from their json
    chunks = load_chunks_from_json(CHUNKS_FILE)
    print(f"Loaded {len(chunks)} chunks from {CHUNKS_FILE}.")
except FileNotFoundError:
    # otherwise chunks are created
    print(f"No chunks found in {CHUNKS_FILE}.")
    docs = load_documents_from_json(DOCUMENTS_FILE, TEXTS_FOLDER)
    chunker = Chunker(chunk_size=512, overlap=50)
    chunks = chunker.chunk_documents(docs)
    save_chunks_to_json(chunks, CHUNKS_FILE)
    print(f"{len(docs)} documents splitted in {len(chunks)} chunks.")

# creates a map from chunk_id to Chunk object for easy lookup in results
chunk_map: Dict[str, Chunk] = {chunk.id: chunk for chunk in chunks}

# --- initialize Embedding Model (always needed for queries) ---
model = EmbeddingModel()

# --- BUILD OR LOAD INDICES ---

# 1. Vectorial Index
vector_index_path = os.path.join(INDEX_DIR, "vector_index")
vector_index = VectorIndex()
try:
    # same as above, if vector index doesn't exist than create it
    vector_index.load(vector_index_path)
    print("Vector Index loaded from disk.")
except FileNotFoundError:
    print("Vector Index not found on disk. Building from scratch...")
    vector_index.build_index(chunks, model)
    vector_index.save(vector_index_path)
    print("Vector Index built and saved.")

# 2. Inverted Index
inverted_index_path = os.path.join(INDEX_DIR, "inverted_index.pkl")
inverted_index = InvertedIndex()
try:
    inverted_index.load(inverted_index_path)
    print("Inverted Index loaded from disk.")
except FileNotFoundError:
    print("Inverted Index not found on disk. Building from scratch...")
    inverted_index.build_index(chunks)
    inverted_index.save(inverted_index_path)
    print("Inverted Index built and saved.")


# --- Initialize Scorers ---
vector_scorer = VectorialScorer(vector_index, model)
kw_scorer = KeywordScorer(inverted_index)

# --- Initialize Hybrid Retriever ---
# alpha parameter controls vectorial importance (0.0 to 1.0)
# 0=only keywords, 1=only vector
hybrid = HybridRetriever(vector_scorer, kw_scorer, alpha=0.9)


# ----------------- TEST QUERY -----------------
query = "guerra in Iran"
results = hybrid.search(query, top_k=5)

print(f"\n--- Hybrid results for query: '{query}' (alpha={hybrid.alpha}) ---")
if not results:
    print("No results found.")
else:
    for chunk_id, h_score, v_score, k_score in results:
        chunk = chunk_map.get(chunk_id) # gets the full chunk object
        if chunk:
            print(f"Chunk ID: {chunk.id}")
            print(f"  Hybrid Score: {h_score:.3f} | Vector Score: {v_score:.3f} | Keyword Score: {k_score:.3f}")
            print(f"  Title: {chunk.metadata.get('document_title', 'N/A')}")
            print(f"  URL: {chunk.metadata.get('document_url', 'N/A')}")
            print(f"  Text Snippet: '{chunk.text[:200]}...'")
            print("-" * 60)
        else:
            print(f"Chunk ID: {chunk_id} not found in map (Error in lookup). Scores: hybrid={h_score:.3f}, vec={v_score:.3f}, key={k_score:.3f}")

print("\n--- Retrieval process finished ---")
