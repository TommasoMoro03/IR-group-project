import numpy as np
from typing import List, Tuple
from retrieving.utils.models import Chunk
from retrieving.embedding.embedding_models import EmbeddingModel
import os
import pickle


class VectorIndex:
    """
    In‑memory vector index for dense retrieval based on cosine similarity.
    """

    def __init__(self):
        self.embeddings: List[np.ndarray] = [] # list of individual embedding vectors
        self.document_ids: List[str] = [] # matching list of document (chunk) IDs
        self.embeddings_matrix: np.ndarray = np.empty((0, 0)) # final stacked matrix
        self.normalized_embeddings_matrix: np.ndarray = np.empty((0, 0)) # L2-normalized matrix for similarity

    def add_document(self, doc_id: str, embedding: np.ndarray):
        """Adds a single document embedding and its id."""
        if not isinstance(embedding, np.ndarray) or embedding.ndim != 1:
            raise ValueError("Embedding must be a 1‑D NumPy array.")
        self.document_ids.append(doc_id)
        self.embeddings.append(embedding)

    def build(self):
        """Finalizes the index by stacking and normalizing embeddings."""
        if self.embeddings:
            self.embeddings_matrix = np.vstack(self.embeddings)
            norms = np.linalg.norm(self.embeddings_matrix, axis=1, keepdims=True)
            norms[norms == 0] = 1e-9  # avoid division by zero
            self.normalized_embeddings_matrix = self.embeddings_matrix / norms
        else:
            # empty index
            self.embeddings_matrix = np.empty((0, 0))
            self.normalized_embeddings_matrix = np.empty((0, 0))

    def search(self, query_embedding: np.ndarray, k: int = 5) -> List[Tuple[str, float]]:
        """
        Returns the top‑k most similar chunks (tuples (chunk_id, cosine_similarity)) using cosine similarity.
        """
        if self.normalized_embeddings_matrix.size == 0:
            return []

        if not isinstance(query_embedding, np.ndarray) or query_embedding.ndim != 1:
            raise ValueError("Query embedding must be a 1‑D NumPy array.")

        # normalization of embeddings and calculation of vector similarities
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        similarities = np.dot(query_norm, self.normalized_embeddings_matrix.T)

        # retrieves just the k top chunks
        top_k_indices = np.argsort(similarities)[::-1][:k]
        results = [
            (self.document_ids[idx], float(similarities[idx]))
            for idx in top_k_indices
        ]
        return results

    def build_index(
        self,
        chunks: List[Chunk],
        embedding_model: EmbeddingModel,
        batch_size: int = 32,
    ):
        """
        Encodes all chunks using the given embedding model, and builds the index.
        Even if it's probably useless in this case, dividing the list of chunks in batches can be useful to avoid memory saturation
        """
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i : i + batch_size]
            texts = [c.text for c in batch_chunks]
            vectors = embedding_model.encode(texts, is_query=False)

            for chunk, vec in zip(batch_chunks, vectors):
                self.add_document(chunk.id, vec)

        self.build()

    # ---------- serialization part ---------- #
    def save(self, filepath_prefix: str):
        """
        Saves the vector index to disk.
        Saves embeddings matrix as .npy and document IDs as a pickle file.
        """
        np.save(f"{filepath_prefix}_embeddings.npy", self.embeddings_matrix)
        with open(f"{filepath_prefix}_ids.pkl", 'wb') as f:
            pickle.dump(self.document_ids, f)
        print(f"Vector Index saved to {filepath_prefix}_embeddings.npy and {filepath_prefix}_ids.pkl")

    def load(self, filepath_prefix: str):
        """
        Loads the vector index from disk.
        Loads embeddings matrix from .npy and document IDs from a pickle file.
        """
        embeddings_path = f"{filepath_prefix}_embeddings.npy"
        ids_path = f"{filepath_prefix}_ids.pkl"

        if not os.path.exists(embeddings_path) or not os.path.exists(ids_path):
            raise FileNotFoundError(f"Vector index files not found at {filepath_prefix}_*")

        self.embeddings_matrix = np.load(embeddings_path)
        with open(ids_path, 'rb') as f:
            self.document_ids = pickle.load(f)

        norms = np.linalg.norm(self.embeddings_matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1e-9
        self.normalized_embeddings_matrix = self.embeddings_matrix / norms

        print(f"Vector Index loaded from {filepath_prefix}_embeddings.npy and {filepath_prefix}_ids.pkl")
