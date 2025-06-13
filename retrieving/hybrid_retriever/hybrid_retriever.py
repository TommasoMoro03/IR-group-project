# retrieving/hybrid_retriever/hybrid_retriever.py
from typing import List, Tuple, Dict
from collections import defaultdict
from retrieving.scoring.vectorial_scorer import VectorialScorer
from retrieving.scoring.keyword_scorer import KeywordScorer
from retrieving.utils.document_parser import Document


class HybridRetriever:
    def __init__(self, vectorial_scorer: VectorialScorer, keyword_scorer: KeywordScorer):
        """
        Initializes the HybridRetriever with a vectorial and a keyword scorer.
        Args:
            vectorial_scorer: An instance of VectorialScorer.
            keyword_scorer: An instance of KeywordScorer.
        """
        self.vectorial_scorer = vectorial_scorer
        self.keyword_scorer = keyword_scorer
        self.documents_map = vectorial_scorer.documents_map  # Use the map from one of the scorers

    def retrieve(self, query: str, k: int = 5) -> List[Tuple[Document, float]]:
        """
        Retrieves and ranks documents using a hybrid approach.
        Combines scores from vectorial and keyword-based retrieval using Reciprocal Rank Fusion (RRF).
        Args:
            query: The natural language query string.
            k: The number of top documents to return.
        Returns:
            A list of (Document object, combined_score) tuples, sorted by combined_score descending.
        """
        # Retrieve results from both scorers, fetching more candidates than k
        vector_results = self.vectorial_scorer.score(query, k=k * 2)  # Fetch more to allow for better RRF
        keyword_results = self.keyword_scorer.score(query, k=k * 2)  # Fetch more to allow for better RRF

        combined_scores: Dict[str, float] = defaultdict(float)
        rrf_k_const = 60.0  # A common constant for RRF, adjust as needed

        # Apply Reciprocal Rank Fusion (RRF)
        # Process vectorial results
        for rank, (doc, _) in enumerate(vector_results):
            combined_scores[doc.id] += 1.0 / (rrf_k_const + rank + 1)

        # Process keyword results
        for rank, (doc, _) in enumerate(keyword_results):
            combined_scores[doc.id] += 1.0 / (rrf_k_const + rank + 1)

        # Sort combined results by score
        sorted_results = sorted(
            [(self.documents_map[doc_id], score) for doc_id, score in combined_scores.items()],
            key=lambda x: x[1],
            reverse=True
        )

        return sorted_results[:k]