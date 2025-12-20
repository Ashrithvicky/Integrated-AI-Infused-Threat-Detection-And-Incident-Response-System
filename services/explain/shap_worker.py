# services/explain/shap_worker.py
"""
SHAP worker: compute feature importance for a single event.

Usage:
    expl = compute_shap_for_features(model_path, {"count": 3, "unique_events": 2})
"""

import os
import joblib
import numpy as np
import shap

def load_model(model_path: str):
    if not os.path.exists(model_path):
        raise FileNotFoundError(model_path)
    return joblib.load(model_path)

def compute_shap_for_features(model_path: str, features: dict):
    model = load_model(model_path)
    keys = list(features.keys())
    vals = np.array([features[k] for k in keys], dtype=float).reshape(1, -1)

    # background: small zero vector (POC)
    background = np.zeros_like(vals)
    explainer = shap.Explainer(model, background)

    sv = explainer(vals)
    shap_vals = sv.values[0].tolist()
    return {"features": keys, "shap_values": shap_vals}

if __name__ == "__main__":
    example_feats = {"count": 3, "unique_events": 2}
    mp = os.getenv("EXPLAIN_MODEL_PATH", "services/ml/models/iforest_v1.pkl")
    if os.path.exists(mp):
        print(compute_shap_for_features(mp, example_feats))
    else:
        print("Model path not found:", mp)
