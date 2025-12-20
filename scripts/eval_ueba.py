# scripts/eval_ueba.py
import os, sys, json, joblib
import numpy as np

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from services.consumer.feature_builder import (
    update_session,
    session_features
)

MODEL_PATH = "services/consumer/models/iforest_v1.pkl"

# Dummy Redis for session tracking
class DummyRedis:
    def __init__(self):
        self.store = {}
    def get(self, k):
        return self.store.get(k)
    def set(self, k, v):
        self.store[k] = v

redis_client = DummyRedis()
model = joblib.load(MODEL_PATH)

print("Loaded UEBA IsolationForest model")

def score_event(ev):
    sess = update_session(redis_client, ev)
    feats = session_features(sess)
    X = np.array([[feats["count"], feats["unique_events"]]])
    score = -model.decision_function(X)[0]
    return score, feats

if __name__ == "__main__":
    with open("examples/cloudtrail_demo_full.json") as f:
        events = json.load(f)

    scores = []

    for ev in events:
        s, feats = score_event(ev)
        scores.append(s)
        print(
            f"Entity={ev.get('userIdentity',{}).get('userName','?')}, "
            f"count={feats['count']}, unique={feats['unique_events']} → score={s:.4f}"
        )

    print("\n=== UEBA Model Summary ===")
    print("Sessions evaluated:", len(scores))
    print("Avg anomaly score:", round(sum(scores)/len(scores), 4))
    print("Max anomaly score:", round(max(scores), 4))
