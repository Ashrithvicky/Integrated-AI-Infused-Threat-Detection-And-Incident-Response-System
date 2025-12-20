# services/ml/fusion/fusion_client.py
"""
Client for the contrastive fusion service (serve_fusion.py).

Usage:
    from services.ml.fusion.fusion_client import get_embedding, embedding_anomaly_score
    emb = get_embedding(modA_vec, modB_vec)
    score = embedding_anomaly_score(emb)
"""

import os
import requests
import numpy as np

FUSION_URL = os.getenv("FUSION_SERVER_URL", "http://localhost:8011/fusion/embed")


def get_embedding(modalityA, modalityB, timeout: float = 3.0):
    """
    modalityA: list[float]
    modalityB: list[float]
    returns: list[float] embedding or [] on error
    """
    try:
        resp = requests.post(
            FUSION_URL,
            json={"modalityA": modalityA, "modalityB": modalityB},
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("embedding", [])
    except Exception as e:
        print("[fusion_client] error calling fusion service:", e)
        return []


def embedding_anomaly_score(embed, centroid=None):
    """
    embed: list[float]
    centroid: optional list[float] as baseline; if None, just use norm of embed
    """
    if not embed:
        return 0.0
    v = np.array(embed, dtype=float)
    if centroid is None:
        dist = np.linalg.norm(v)
    else:
        c = np.array(centroid, dtype=float)
        dist = np.linalg.norm(v - c)
    # simple normalization heuristic 0–1
    score = 1.0 - 1.0 / (1.0 + dist)
    return float(score)
