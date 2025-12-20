# scripts/eval_sequence.py
import json
import torch
from services.ml.sequence.serve_transformer import model, EV_TO_ID

def score_sequence(events):
    ids = [EV_TO_ID.get(e, 0) for e in events]
    x = torch.tensor([ids], dtype=torch.long)
    with torch.no_grad():
        return float(model(x).item())

if __name__ == "__main__":
    # Example test sequences
    sequences = [
        ["ConsoleLogin", "ListBuckets"],
        ["ConsoleLogin", "CreateUser", "AttachRolePolicy", "PutBucketPolicy"],
        ["ConsoleLogin", "GetObject", "GetObject"],
        ["ConsoleLogin", "DeleteBucket"]
    ]

    scores = []
    for seq in sequences:
        s = score_sequence(seq)
        scores.append(s)
        print(f"Sequence {seq} -> score={s:.4f}")

    print("\n=== Sequence Model Summary ===")
    print(f"Avg score: {sum(scores)/len(scores):.4f}")
    print(f"Max score: {max(scores):.4f}")
