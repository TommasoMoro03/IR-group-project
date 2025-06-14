import numpy as np
from typing import List, Tuple
from retrieving.indexing.vector_index import VectorIndex
from retrieving.embedding.embedding_models import EmbeddingModel


class VectorialScorer:
    def __init__(self, index: VectorIndex, embedding_model: EmbeddingModel):
        self.index = index
        self.embedding_model = embedding_model

    def score(self, query: str, k: int = 5) -> List[Tuple[str, float]]:
        """
        Compute similarity scores between the query and indexed chunks.
        Returns top-k results as list of (chunk_id, score).
        """
        query_embedding = self.embedding_model.encode([query])[0]  # shape (dim,)
        results = self.index.search(query_embedding, k=k)
        return results
