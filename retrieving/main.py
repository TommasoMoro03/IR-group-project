# retrieving/test.py

import os
import sys
from typing import List

import numpy as np

# Add the 'retrieving' directory to PYTHONPATH to allow imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Import all necessary classes
from retrieving.utils.data_loader import load_documents_from_json
from retrieving.models.embedding_models import EmbeddingModel
from retrieving.indexing.vector_index import VectorIndex
from retrieving.indexing.inverted_index import InvertedIndex
from retrieving.scoring.vectorial_scorer import VectorialScorer
from retrieving.scoring.keyword_scorer import KeywordScorer
from retrieving.hybrid_retriever.hybrid_retriever import HybridRetriever
from retrieving.utils.document_parser import Document  # Import Document class for type hinting


def run_full_retrieval_test():
    print("--- Starting Full Hybrid Retrieval Test ---")

    # 1. Load documents from mock JSON
    data_filepath = os.path.join(current_dir, 'data', 'mock_documents.json')
    documents: List[Document] = load_documents_from_json(data_filepath)
    print(f"Loaded {len(documents)} mock documents.")

    # 2. Initialize Embedding Model
    print("Loading BAAI/bge-small-en-v1.5 embedding model...")
    try:
        embedding_model = EmbeddingModel(model_name="BAAI/bge-small-en-v1.5")
        print("Embedding model loaded successfully.")
    except Exception as e:
        print(f"Error loading embedding model: {e}")
        print("Ensure you have an internet connection and necessary libraries (torch, transformers) installed.")
        return

    # 3. Build Indices
    print("Building Vector Index and Inverted Index...")
    vector_index = VectorIndex()
    inverted_index = InvertedIndex()

    doc_texts = [doc.text for doc in documents]
    doc_embeddings = embedding_model.encode(doc_texts)

    for i, doc in enumerate(documents):
        vector_index.add_document(doc.id, doc_embeddings[i])
        inverted_index.add_document(doc.id, doc.text)

    vector_index.build()  # Finalize vector index construction
    print("Indices built successfully.")

    # 4. Initialize Scorers
    vectorial_scorer = VectorialScorer(embedding_model, vector_index, documents)
    keyword_scorer = KeywordScorer(inverted_index, documents)

    # 5. Initialize Hybrid Retriever
    hybrid_retriever = HybridRetriever(vectorial_scorer, keyword_scorer)

    # 6. Define Query
    query = "efficient inverted index for document search"
    print(f"\nProcessing query: '{query}'")

    # --- Test individual scorers and print scores ---

    print("\n--- Vectorial Scorer Results (Top 3) ---")
    vec_results = vectorial_scorer.score(query, k=3)
    for i, (doc, score) in enumerate(vec_results):
        print(f"{i + 1}. Document ID: {doc.id}, Vector Score: {score:.4f}")
        print(f"   Text Snippet: '{doc.text[:70]}...'")

    print("\n--- Keyword Scorer Results (Top 3) ---")
    kw_results = keyword_scorer.score(query, k=3)
    for i, (doc, score) in enumerate(kw_results):
        print(f"{i + 1}. Document ID: {doc.id}, Keyword Score: {score:.4f}")
        print(f"   Text Snippet: '{doc.text[:70]}...'")

    # --- Run Hybrid Retrieval ---
    print("\n--- Hybrid Retriever Final Results (Top 3) ---")
    final_results = hybrid_retriever.retrieve(query, k=3)

    for i, (doc, score) in enumerate(final_results):
        print(f"{i + 1}. Document ID: {doc.id}, Combined Score (RRF): {score:.4f}")
        print(f"   Text Snippet: '{doc.text[:100]}...'")
        print(f"   Metadata: {doc.metadata}")
        print("-" * 30)

    print("\n--- Full Hybrid Retrieval Test Completed ---")


if __name__ == "__main__":
    run_full_retrieval_test()