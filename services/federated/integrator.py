# services/federated/integrator.py
"""
Federated UEBA integrator.

Fetches global weight vector from federated server and converts it
into fusion weights usable by the fusion layer (rule, ueba, seq, ti).
"""

import os
import requests
import numpy as np

FED_SERVER = os.getenv("FED_SERVER", "http://localhost:9000")


def fetch_global():
    try:
        r = requests.get(FED_SERVER + "/get_global", timeout=3)
        r.raise_for_status()
        return r.json().get("global", None)
    except Exception as e:
        print("[federated_integrator] error:", e)
        return None


def get_fusion_weights():
    """
    Returns dict like {"rule": w1, "ueba": w2, "seq": w3, "ti": w4}
    derived from global vector. If no global, returns None.
    """
    g = fetch_global()
    if not g:
        return None

    arr = np.array(g, dtype=float)
    if arr.size == 0:
        return None
    # normalize to 0–1
    arr = (arr - arr.min()) / (arr.ptp() + 1e-6)

    # map first dims to weights
    w = {
        "rule": float(arr[0]) if arr.size > 0 else 0.4,
        "ueba": float(arr[1]) if arr.size > 1 else 0.25,
        "seq": float(arr[2]) if arr.size > 2 else 0.2,
        "ti": float(arr[3]) if arr.size > 3 else 0.15,
    }
    s = sum(w.values()) or 1.0
    for k in w:
        w[k] = w[k] / s
    return w


if __name__ == "__main__":
    print(get_fusion_weights())
