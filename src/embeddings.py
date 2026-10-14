"""Embeddings: MiniLM local, TF-IDF/char-hash fallback for offline runs."""
import re
import numpy as np

_model = None
_vectorizer = None  # sklearn TfidfVectorizer fitted lazily (Tier1 + fallback)

def embed(texts, model_name="sentence-transformers/all-MiniLM-L6-v2"):
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer(model_name)
        except Exception as e:
            print(f"[embeddings] MiniLM load failed ({e}); using TF-IDF fallback")
            _model = "tfidf-fallback"
    if _model == "tfidf-fallback":
        return _tfidf_embed(texts)
    return np.asarray(_model.encode(texts, normalize_embeddings=True), dtype=np.float32)

def _tfidf_embed(texts):
    from sklearn.feature_extraction.text import TfidfVectorizer
    global _vectorizer
    # Fit on current batch (retrieval still works for small corpora; ingest fits on corpus)
    _vectorizer = TfidfVectorizer(max_features=384).fit(texts)
    m = _vectorizer.transform(texts).toarray().astype(np.float32)
    # L2 normalize; pad/truncate to 384
    n, d = m.shape
    out = np.zeros((n, 384), dtype=np.float32)
    out[:, :min(d, 384)] = m[:, :min(d, 384)]
    norms = np.linalg.norm(out, axis=1, keepdims=True) + 1e-9
    return out / norms

def get_vectorizer():
    from sklearn.feature_extraction.text import TfidfVectorizer
    global _vectorizer
    if _vectorizer is None:
        _vectorizer = TfidfVectorizer(stop_words="english", max_features=8192)
    return _vectorizer

def word_tokens(s):
    return re.findall(r"[a-z0-9]+", s.lower())
