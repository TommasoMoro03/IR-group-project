from typing import List, Tuple, Dict
from retrieving.scoring.vectorial_scorer import VectorialScorer
from retrieving.scoring.keyword_scorer import KeywordScorer


class HybridRetriever:
    """
    Combines scores of vectorial scorer and keyword scorer
        hybrid = α * vector_score + (1‑α) * keyword_score
    All scores are on [0, 1]
    """

    def __init__(self, vector_scorer: VectorialScorer, keyword_scorer: KeywordScorer, alpha: float = 0.5):
        assert 0.0 <= alpha <= 1.0, "alpha must be in [0,1]"
        self.vs = vector_scorer
        self.ks = keyword_scorer
        self.alpha = alpha

    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float, float, float]]:
        """
        Returns list of (chunk_id, hybrid_score, vector_score, keyword_score)
        """
        vec_results = dict(self.vs.score(query, k=top_k * 2))          # id -> score (0‑1)
        key_results = dict(self.ks.score(query, top_k * 2, normalize=True))

        all_ids = set(vec_results) | set(key_results)
        hybrid_scores: Dict[str, Tuple[float, float, float]] = {}

        for cid in all_ids:
            v = vec_results.get(cid, 0.0)
            k = key_results.get(cid, 0.0)
            h = self.alpha * v + (1 - self.alpha) * k
            hybrid_scores[cid] = (h, v, k)

        ranked = sorted(hybrid_scores.items(), key=lambda x: x[1][0], reverse=True)[:top_k]
        return [(cid, h, v, k) for cid, (h, v, k) in ranked]
