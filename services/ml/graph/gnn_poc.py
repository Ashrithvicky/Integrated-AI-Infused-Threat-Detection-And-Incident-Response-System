# services/ml/graph/gnn_poc.py
# POC: compute node embeddings via adjacency matrix SVD (toy), use for anomaly scoring
import networkx as nx, numpy as np, os, json
from sklearn.decomposition import TruncatedSVD

GRAPH_STORE = "data/graph_store.json"
EMBED_OUT = "services/ml/models/graph/node_embeddings.npy"

def load_graph():
    if not os.path.exists(GRAPH_STORE):
        return nx.DiGraph()
    import json
    from networkx.readwrite import json_graph
    data = json.load(open(GRAPH_STORE,"r",encoding="utf-8"))
    G = json_graph.node_link_graph(data)
    return G

from networkx.readwrite import json_graph
def compute_embeddings(dim=32):
    G = load_graph()
    nodes = list(G.nodes())
    if len(nodes) == 0:
        print("Graph empty; no embeddings")
        return nodes, None
    idx = {n:i for i,n in enumerate(nodes)}
    # Use numpy adjacency matrix (dense) for small graphs; safe cross-version
    A = nx.to_numpy_array(G, nodelist=nodes, dtype=float)
    # If A is singular or too small, adjust n_components
    n_comp = min(dim, max(1, A.shape[0]-1))
    from sklearn.decomposition import TruncatedSVD
    svd = TruncatedSVD(n_components=n_comp)
    emb = svd.fit_transform(A)
    os.makedirs(os.path.dirname(EMBED_OUT), exist_ok=True)
    np.save(EMBED_OUT, emb)
    with open(EMBED_OUT+".meta","w",encoding="utf-8") as f:
        json.dump(nodes, f)
    print("Saved embeddings", EMBED_OUT)
    return nodes, emb


def score_node(entity):
    nodes, emb = compute_embeddings(dim=16)
    if entity not in nodes:
        return 0.0
    idx = nodes.index(entity)
    vec = emb[idx]
    # anomaly score = distance to mean
    mean = emb.mean(axis=0)
    dist = np.linalg.norm(vec-mean)
    return float(dist)

if __name__=="__main__":
    compute_embeddings()
    print("sample score:", score_node("alice@example.com"))
