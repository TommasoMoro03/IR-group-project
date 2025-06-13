import numpy as np
from typing import List, Tuple


class VectorIndex:
    def __init__(self):
        self.embeddings: List[np.ndarray] = []
        self.document_ids: List[str] = []
        self.embeddings_matrix: np.ndarray = np.empty((0, 0))  # Stacked embeddings
        self.normalized_embeddings_matrix: np.ndarray = np.empty((0, 0))  # Normalized for search

    def add_document(self, doc_id: str, embedding: np.ndarray):
        """Adds a document embedding to the index."""
        if not isinstance(embedding, np.ndarray) or embedding.ndim != 1:
            raise ValueError("Embedding must be a 1D NumPy array.")
        self.document_ids.append(doc_id)
        self.embeddings.append(embedding)

    def build(self):
        """Builds the final embedding matrix and normalizes it for search."""
        if self.embeddings:
            self.embeddings_matrix = np.vstack(self.embeddings)
            norms = np.linalg.norm(self.embeddings_matrix, axis=1, keepdims=True)
            norms[norms == 0] = 1e-9  # avoid division by zero
            self.normalized_embeddings_matrix = self.embeddings_matrix / norms
        else:
            self.embeddings_matrix = np.empty((0, 0))
            self.normalized_embeddings_matrix = np.empty((0, 0))

    def search(self, query_embedding: np.ndarray, k: int = 5) -> List[Tuple[str, float]]:
        """
        Performs vector similarity search for a query.
        Returns a list of (document_id, similarity_score) tuples.
        """
        if not self.normalized_embeddings_matrix.shape[0]:
            return []

        if not isinstance(query_embedding, np.ndarray) or query_embedding.ndim != 1:
            raise ValueError("Query embedding must be a 1D NumPy array.")

        # Normalize query embedding
        query_embedding_norm = query_embedding / np.linalg.norm(query_embedding)

        # Calculate cosine similarity (dot product of normalized vectors)
        similarities = np.dot(query_embedding_norm, self.normalized_embeddings_matrix.T)

        # Get top-k indices by sorting similarities
        top_k_indices = np.argsort(similarities)[::-1][:k]

        results = []
        for idx in top_k_indices:
            if idx < len(self.document_ids):  # Ensure index is valid
                doc_id = self.document_ids[idx]
                score = similarities[idx]
                results.append((doc_id, float(score)))

        return results
