import torch
from typing import List, Tuple
from retrieving.models.embedding_models import EmbeddingModel
from retrieving.indexing.vector_index import VectorIndex
from ..utils.document_parser import Document

class VectorialScorer:
    def __init__(self, embedding_model: EmbeddingModel, vector_index: VectorIndex, documents: List[Document]):
        self.embedding_model = embedding_model
        self.vector_index = vector_index
        self.documents_map = {doc.id: doc for doc in documents}

    def score(self, query: str, k: int = 5) -> List[Tuple[Document, float]]:
        query_embedding = self.embedding_model.encode([query]).squeeze(0)
        results = self.vector_index.search(query_embedding, k=k)
        # maps the doc_ids to the document objects
        return [(self.documents_map[doc_id], score) for doc_id, score in results]