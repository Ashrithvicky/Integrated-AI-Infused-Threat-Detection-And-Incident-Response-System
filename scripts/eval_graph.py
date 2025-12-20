# scripts/eval_graph.py
import os, sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from services.graph_service.graph_builder import load_graph
from services.ml.graph.gnn_model import score_node

def main():
    print("\n[Graph Model Evaluation]\n")

    G = load_graph()
    scores = []

    for node in G.nodes():
        s = score_node(node)
        scores.append(s)

    print("Nodes analyzed:", len(scores))
    print("Avg node risk:", round(sum(scores)/len(scores), 4))
    print("Max node risk:", round(max(scores), 4))

if __name__ == "__main__":
    main()
