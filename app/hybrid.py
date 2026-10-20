"""Hybrid search helpers: a small BM25 keyword index + Reciprocal Rank Fusion.

Why: embeddings capture meaning ("timing of events" ~ "dasa"), while BM25 nails exact
rare terms (Sanskrit words like "Vimsottari", "Arudha", "Argala") that small embedding
models often blur. Fusing both rankings gives better retrieval than either alone.
"""
import math
import re
from collections import Counter

_STOP = set(
    "a an the of in to and or is are was were be been for on with as by at it its this that these "
    "those what which who whom how why when where do does did can could should would will shall may "
    "might from into than then there their them they he she his her we you your our i me my not no "
    "about tell explain please book".split()
)


def tokenize(text: str) -> list[str]:
    text = text.lower().replace("’", "'")
    return [w for w in re.findall(r"[a-z0-9]+", text) if w not in _STOP and len(w) > 1]


class BM25:
    """Okapi BM25 over a fixed list of documents (pure Python, no dependencies)."""

    def __init__(self, documents: list[str], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.docs = [tokenize(d) for d in documents]
        self.lengths = [len(d) for d in self.docs]
        self.avg_len = sum(self.lengths) / max(len(self.docs), 1)
        self.term_freqs = [Counter(d) for d in self.docs]
        doc_freq = Counter(term for d in self.docs for term in set(d))
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - df + 0.5) / (df + 0.5)) for t, df in doc_freq.items()}

    def top_k(self, query: str, k: int) -> list[int]:
        terms = [t for t in tokenize(query) if t in self.idf]
        if not terms:
            return []
        scores = []
        for i, tf in enumerate(self.term_freqs):
            s = 0.0
            norm = self.k1 * (1 - self.b + self.b * self.lengths[i] / self.avg_len)
            for t in terms:
                f = tf.get(t)
                if f:
                    s += self.idf[t] * f * (self.k1 + 1) / (f + norm)
            if s > 0:
                scores.append((s, i))
        scores.sort(reverse=True)
        return [i for _, i in scores[:k]]


def reciprocal_rank_fusion(rankings: list[list[int]], k: int = 60) -> list[int]:
    """Merge several ranked lists of ids: score = sum(1 / (k + rank))."""
    fused: dict[int, float] = {}
    for ranking in rankings:
        for rank, doc_id in enumerate(ranking):
            fused[doc_id] = fused.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
    return [doc_id for doc_id, _ in sorted(fused.items(), key=lambda x: -x[1])]
