import re
import math
from collections import Counter, defaultdict
from typing import List, Tuple, Dict
from retrieving.indexing.inverted_index import InvertedIndex
from retrieving.stemming.simple_stemmer import SimpleStemmer
from retrieving.stemming.custom_stemmer import CustomStemmer


class KeywordScorer:
    """
    BM25 scorer (k1, b) using an InvertedIndex.
    """

    def __init__(self, inverted_index: InvertedIndex, k1: float = 1.2, b: float = 0.75):
        self.inv = inverted_index
        self.k1 = k1
        self.b = b
        self.stemmer = CustomStemmer()

    # ---------- helpers ---------- #
    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"\b\w+\b", text.lower())

    def _idf(self, df: int) -> float:
        """
        BM25 IDF with +1 smoothing to avoid negatives.
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
        If normalize=True, scores are scaled to [0,1] via min‑max on this query.
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
