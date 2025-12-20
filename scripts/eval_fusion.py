from services.fusion.fusion import fuse_scores
from random import random

def main():
    print("\n[Fusion Layer Evaluation]\n")

    scores = []

    for _ in range(100):
        ueba = random()
        seq = random()
        graph = random()
        ti = random()

        final = fuse_scores(ueba, seq, graph, ti)
        scores.append(final)

    print("Avg fused risk:", sum(scores) / len(scores))
    print("Max fused risk:", max(scores))

if __name__ == "__main__":
    main()
