# retrieving/indexing/inverted_index.py
from collections import defaultdict
import re
from typing import List, Dict

class InvertedIndex:
    def __init__(self):
        """Initializes the inverted index."""
        self.index = defaultdict(list)  # Maps term -> list of document_ids
        self.doc_lengths = {}           # Stores document lengths (e.g., for future TF-IDF)

    def _tokenize(self, text: str) -> List[str]:
        """
        Simple text tokenization: lowercase and extract alphanumeric words.
        """
        return [token.lower() for token in re.findall(r'\b\w+\b', text)]

    def add_document(self, doc_id: str, text: str):
        """
        Adds a document's content to the inverted index.
        Args:
            doc_id: Unique identifier for the document.
            text: The cleaned text content of the document.
        """
        tokens = self._tokenize(text)
        self.doc_lengths[doc_id] = len(tokens) # Store document length

        # Add document ID to posting list for each unique token in the document
        unique_tokens_in_doc = set(tokens)
        for token in unique_tokens_in_doc:
            self.index[token].append(doc_id)

    def search(self, query_tokens: List[str]) -> Dict[str, int]:
        """
        Performs a keyword search, returning document IDs and their match counts.
        Args:
            query_tokens: A list of pre-tokenized query terms.
        Returns:
            A dictionary mapping document_id to the count of query keywords
            that match within that document.
        """
        doc_scores = defaultdict(int)
        for token in query_tokens:
            for doc_id in self.index.get(token, []): # Iterate through posting list for the token
                doc_scores[doc_id] += 1 # Increment score for each match
        return doc_scores