# services/correlation/correlator.py
"""
Cross-domain correlator: uses the entity graph + GNN score to compute
a correlation score for an entity (user, host, IP, etc.).

It inspects neighbors in the graph and calls GNN-based score_node().
"""

import os, sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from services.graph_service.graph_builder import load_graph
from services.ml.graph.gnn_model import score_node

def correlate_entity(entity_id: str):
    G = load_graph()
    if entity_id not in G:
        return {"entity": entity_id, "correlation_score": 0.0, "neighbors": [], "attribution": 0.0}

    neighbors = list(G.neighbors(entity_id))
    attr = score_node(entity_id)
    # simple heuristic: more neighbors + higher attr => higher correlation
    score = attr * (1.0 + 0.1 * len(neighbors))
    return {
        "entity": entity_id,
        "correlation_score": float(score),
        "neighbors": neighbors,
        "attribution": float(attr),
    }

if __name__ == "__main__":
    print(correlate_entity("alice@example.com"))
