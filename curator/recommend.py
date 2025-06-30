from __future__ import annotations

from typing import List, Dict

import logging

import numpy as np
from sentence_transformers import SentenceTransformer

from . import db


logger = logging.getLogger(__name__)

# Embedding model (384-dim)
MODEL = "sentence-transformers/all-MiniLM-L6-v2"

_model = SentenceTransformer(MODEL)


def embed(text: str) -> np.ndarray:
    """Return normalized 384-dimensional embedding for ``text``."""
    logger.debug("embedding text of length %d", len(text))
    return _model.encode(text, convert_to_numpy=True, normalize_embeddings=True)


def recommend(top_n: int) -> List[dict]:
    """Return ``top_n`` items ranked by similarity to user preferences."""
    logger.info("[i] computing recommendations")
    with db.get_connection() as conn:
        items = conn.execute("SELECT id, title, description FROM items").fetchall()
        rated_rows = conn.execute("SELECT item_id, rating FROM ratings").fetchall()

    # Aggregate ratings per item
    rating_sum: Dict[str, float] = {}
    rating_count: Dict[str, int] = {}
    for row in rated_rows:
        item_id = row["item_id"]
        rating_sum[item_id] = rating_sum.get(item_id, 0.0) + row["rating"]
        rating_count[item_id] = rating_count.get(item_id, 0) + 1

    # Embed all items on demand
    embeddings: Dict[str, np.ndarray] = {}
    for item in items:
        text = f"{item['title']} {item['description'] or ''}".strip()
        embeddings[item["id"]] = embed(text)

    dim = _model.get_sentence_embedding_dimension()
    preference = np.zeros(dim, dtype=float)
    weight_total = 0.0
    for item_id, total_rating in rating_sum.items():
        vec = embeddings.get(item_id)
        if vec is None:
            continue
        weight = total_rating / rating_count[item_id]
        preference += vec * weight
        weight_total += weight
    if weight_total:
        preference /= weight_total
    norm = np.linalg.norm(preference) or 1.0
    preference /= norm

    scored = [(float(np.dot(embeddings[row["id"]], preference)), row) for row in items]
    scored.sort(key=lambda x: x[0], reverse=True)

    logger.info("[i] returning top %d recommendations", top_n)
    return [row for _, row in scored[:top_n]]
