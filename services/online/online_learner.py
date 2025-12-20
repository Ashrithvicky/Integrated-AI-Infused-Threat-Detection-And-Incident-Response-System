# services/online/online_learner.py
# Online/incremental anomaly detection POC using River (incremental library)
# This file avoids passing unknown constructor args to HalfSpaceTrees to be robust
# across river versions.

from river import anomaly
import numpy as np
import time

# Create an incremental anomaly detector.
# Pass only 'seed' to be safe across river versions.
model = anomaly.HalfSpaceTrees(seed=42)

def feed_stream(rows, sleep: float = 0.0):
    """
    rows: iterable of dicts with keys 'count' and 'unique_events'
    yields anomaly score per item
    """
    for r in rows:
        x = {"count": r["count"], "unique_events": r["unique_events"]}
        score = model.score_one(x)     # anomaly score (higher = more anomalous)
        model.learn_one(x)             # update model incrementally
        yield score
        if sleep:
            time.sleep(sleep)

if __name__ == "__main__":
    # demo using synthetic data
    data = [{"count": int(np.random.poisson(3)), "unique_events": int(np.random.randint(1, 4))} for _ in range(300)]
    for s in feed_stream(data, sleep=0.02):
        print("online score:", s)
