import re
import math
from collections import Counter, defaultdict
from typing import List, Tuple
from retrieving.indexing.inverted_index import InvertedIndex


class KeywordScorer:
    """
    BM25 scorer (k1, b) using an InvertedIndex.
    """

    def __init__(self, inverted_index: InvertedIndex, k1: float = 1.2, b: float = 0.75):
        self.inv = inverted_index
        self.k1 = k1
        self.b = b

    # ---------- helpers ---------- #
    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"\b\w+\b", text.lower())

    def _idf(self, df: int) -> float:
        """
        BM25 IDF with +1 smoothing to avoid negatives.
        """
        N = self.inv.N
        return math.log((N - df + 0.5) / (df + 0.5) + 1)

    # ---------- main API ---------- #
    def score(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Returns top_k (chunk_id, bm25_score) tuples.
        """
        query_terms = self._tokenize(query)
        query_freqs = Counter(query_terms)

        scores = defaultdict(float)

        for term, qf in query_freqs.items():
            postings = self.inv.get_postings(term)
            df = self.inv.df(term)
            if df == 0:
                continue

            idf = self._idf(df)

            for chunk_id, tf in postings:
                dl = self.inv.chunk_lengths[chunk_id]
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * dl / self.inv.avg_dl)
                scores[chunk_id] += idf * numerator / denominator

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        # convert Decimal→float for JSON‑serialisability
        return [(cid, float(sc)) for cid, sc in ranked]
