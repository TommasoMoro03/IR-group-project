from typing import List, Tuple
from retrieving.indexing.inverted_index import InvertedIndex
from retrieving.utils.document_parser import Document
import re


class KeywordScorer:
    def __init__(self, inverted_index: InvertedIndex, documents: List[Document]):
        """
        Initializes the KeywordScorer.
        Args:
            inverted_index: An instance of InvertedIndex already built.
            documents: A list of Document objects from the corpus.
        """
        self.inverted_index = inverted_index
        self.documents_map = {doc.id: doc for doc in documents}

    def _tokenize_query(self, query: str) -> list[str]:
        """
        Simple tokenization for the query.
        Converts to lowercase and extracts alphanumeric words.
        """
        return [token.lower() for token in re.findall(r'\b\w+\b', query)]

    def score(self, query: str, k: int = 5) -> List[Tuple[Document, float]]:
        """
        Scores documents based on keyword matching using the inverted index.
        Args:
            query: The natural language query string.
            k: The number of top documents to return.
        Returns:
            A list of (Document object, score) tuples, sorted by score descending.
        """
        query_tokens = self._tokenize_query(query)

        # Get raw keyword match counts from the inverted index
        # This returns a dict {doc_id: count_of_matching_keywords}
        doc_keyword_counts = self.inverted_index.search(query_tokens)

        # Convert to list of (Document, score) tuples and sort
        results = []
        for doc_id, count in doc_keyword_counts.items():
            # Use the count of matching keywords as the score
            results.append((self.documents_map[doc_id], float(count)))

        # Sort by score in descending order
        results.sort(key=lambda x: x[1], reverse=True)

        return results[:k]