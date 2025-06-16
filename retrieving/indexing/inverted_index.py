import re
from collections import defaultdict, Counter
from typing import Dict, List, Tuple
import pickle # for serialization
import os

from retrieving.stemming.custom_stemmer import CustomStemmer
from retrieving.utils.models import Chunk
from retrieving.stemming.simple_stemmer import SimpleStemmer


class InvertedIndex:
    """
    word  -> list[(chunk_id, tf)]
    chunk_id -> dl  (document length in tokens)
    N = #chunk   | avg_dl = average document length
    """

    def __init__(self):
        self.index: Dict[str, List[Tuple[str, int]]] = defaultdict(list)
        self.chunk_lengths: Dict[str, int] = {}
        self.N: int = 0
        self.avg_dl: float = 0.0
        self.stemmer = CustomStemmer()

    # ---------- helpers ---------- #
    def _tokenize(self, text: str) -> List[str]:
        tokens = re.findall(r"\b\w+\b", text.lower())
        return self.stemmer.stem_tokens(tokens)

    # ---------- build ---------- #
    def build_index(self, chunks: List[Chunk]) -> None:
        """
        Fills self.index, self.chunk_lengths, self.N, self.avg_dl
        """
        for chunk in chunks:
            tokens = self._tokenize(chunk.text)
            self.chunk_lengths[chunk.id] = len(tokens)

            term_freqs = Counter(tokens)        # tf in this chunk
            for term, tf in term_freqs.items():
                self.index[term].append((chunk.id, tf))

        self.N = len(chunks)
        if self.N:
            self.avg_dl = sum(self.chunk_lengths.values()) / self.N

    # ---------- accessors ---------- #
    def get_postings(self, term: str) -> List[Tuple[str, int]]:
        return self.index.get(term.lower(), [])

    def df(self, term: str) -> int:
        return len(self.index.get(term.lower(), []))

    # ---------- serialization ---------- #
    def save(self, filepath: str):
        """Saves the inverted index to disk using pickle."""
        data = {
            'index': dict(self.index),
            'chunk_lengths': self.chunk_lengths,
            'N': self.N,
            'avg_dl': self.avg_dl
        }
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)
        print(f"Inverted Index saved to {filepath}")

    def load(self, filepath: str):
        """Loads the inverted index from disk using pickle."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Index file not found at {filepath}")

        with open(filepath, 'rb') as f:
            data = pickle.load(f)

        self.index = defaultdict(list, data['index'])  # Convert back to defaultdict
        self.chunk_lengths = data['chunk_lengths']
        self.N = data['N']
        self.avg_dl = data['avg_dl']
        # Re-initialize stemmer, because it's not part of the pickled state
        self.stemmer = CustomStemmer()
        print(f"Inverted Index loaded from {filepath}")
