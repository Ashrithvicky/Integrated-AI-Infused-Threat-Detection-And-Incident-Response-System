# services/consumer/seq_client.py
# helper to query sequence server from consumer code
import requests, os
SEQ_URL = os.getenv("SEQ_SERVER_URL", "http://localhost:8003/sequence/score")

def score_sequence(events):
    try:
        res = requests.post(SEQ_URL, json={"events": events}, timeout=5)
        return res.json().get("score", 0.0)
    except Exception as e:
        print("Seq client error", e)
        return 0.0
