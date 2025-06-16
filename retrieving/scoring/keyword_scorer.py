import re
import math
from collections import Counter, defaultdict
from typing import List, Tuple, Dict
from retrieving.indexing.inverted_index import InvertedIndex
from retrieving.stemming.simple_stemmer import SimpleStemmer
from retrieving.stemming.custom_stemmer import CustomStemmer


class KeywordScorer:
    """
    Implementation of a BM25 scorer using an InvertedIndex.

    k1 and b are the parameters as seen in class, I have provided default values
    but they can be set when calling the class
    """

    def __init__(self, inverted_index: InvertedIndex, k1: float = 1.2, b: float = 0.75):
        self.inv = inverted_index
        self.k1 = k1
        self.b = b
        # here CustomStemmer is called, but it can be changed to SimpleStemmer as well (or potentially another stemming implementation)
        self.stemmer = CustomStemmer()

    def _idf(self, df: int) -> float:
        """
        Calculation of BM25 IDF with +1 smoothing to avoid negatives.
        """
        N = self.inv.N
        return math.log((N - df + 0.5) / (df + 0.5) + 1)

    def score(
        self,
        query: str,
        top_k: int = 5,
        normalize: bool = True
    ) -> List[Tuple[str, float]]:
        """
        Returns top_k (chunk_id, bm25_score) tuples.
        If normalize=True (default), scores are scaled to [0,1] via min‑max on this query.
        """
        query_terms = self.stemmer.stem_text(query)
        query_freqs = Counter(query_terms)

        raw_scores: Dict[str, float] = defaultdict(float)

        for term in query_freqs:
            postings = self.inv.get_postings(term)
            df = self.inv.df(term)
            if df == 0:
                continue

            idf = self._idf(df)
            for chunk_id, tf in postings:
                dl = self.inv.chunk_lengths[chunk_id]
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * dl / self.inv.avg_dl)
                raw_scores[chunk_id] += idf * numerator / denominator

        # ---------- normalisation ---------- #
        if normalize and raw_scores:
            max_s, min_s = max(raw_scores.values()), min(raw_scores.values())
            if max_s != min_s:
                for cid in raw_scores:
                    raw_scores[cid] = (raw_scores[cid] - min_s) / (max_s - min_s)
            else:
                for cid in raw_scores:
                    raw_scores[cid] = 1.0

        ranked = sorted(raw_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return [(cid, float(sc)) for cid, sc in ranked]
