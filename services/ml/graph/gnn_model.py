# services/ml/graph/gnn_model.py
import os, json
import networkx as nx
import numpy as np
import torch
import torch.nn as nn
from sklearn.preprocessing import StandardScaler
from datetime import datetime

GRAPH_STORE = os.getenv("GRAPH_STORE_PATH", "data/graph_store.json")
EMBED_OUT = "services/ml/models/graph/gnn_embeddings.npy"
META_OUT = "services/ml/models/graph/gnn_meta.json"

def load_graph():
    if not os.path.exists(GRAPH_STORE):
        return nx.DiGraph()
    data = json.load(open(GRAPH_STORE,"r",encoding="utf-8"))
    return nx.node_link_graph(data)

def build_adj_embeddings(G):
    nodes = list(G.nodes())
    if len(nodes)==0:
        return nodes, None
    A = nx.to_numpy_array(G, nodelist=nodes, dtype=float)
    # add small self-loop
    A = A + np.eye(A.shape[0])*0.01
    # simple node features: degree in/out
    deg_in = np.array([G.in_degree(n) for n in nodes], dtype=float).reshape(-1,1)
    deg_out = np.array([G.out_degree(n) for n in nodes], dtype=float).reshape(-1,1)
    X = np.hstack([deg_in, deg_out])
    scaler = StandardScaler().fit(X)
    Xs = scaler.transform(X)
    return nodes, A, Xs

class SimpleGCN(nn.Module):
    def __init__(self, in_dim, hid=32, out_dim=16):
        super().__init__()
        self.fc1 = nn.Linear(in_dim, hid)
        self.fc2 = nn.Linear(hid, out_dim)
        self.act = nn.ReLU()
    def forward(self, A, X):
        # A: numpy dense adjacency, X: numpy features
        A_t = torch.tensor(A, dtype=torch.float32)  # N x N
        X_t = torch.tensor(X, dtype=torch.float32)  # N x F
        # simple GCN step: A @ X @ W
        H = A_t @ X_t
        H = self.act(self.fc1(H))
        H = self.fc2(H)  # N x out
        return H.detach().numpy()

def train_and_save(out_emb=EMBED_OUT, out_meta=META_OUT):
    G = load_graph()
    nodes, A, X = build_adj_embeddings(G)
    if A is None:
        print("Graph empty. Nothing to train.")
        return
    model = SimpleGCN(in_dim=X.shape[1], hid=64, out_dim=32)
    # training is optional; here we just run forward for POC
    emb = model(A,X)
    os.makedirs(os.path.dirname(out_emb), exist_ok=True)
    np.save(out_emb, emb)
    with open(out_meta,"w",encoding="utf-8") as f:
        json.dump({"nodes": nodes, "trained_at": datetime.utcnow().isoformat()+"Z"}, f)
    print("Saved GNN embeddings:", out_emb)

def score_node(entity):
    if not os.path.exists(EMBED_OUT) or not os.path.exists(META_OUT):
        train_and_save()
    import numpy as np
    emb = np.load(EMBED_OUT)
    meta = json.load(open(META_OUT,"r",encoding="utf-8"))
    nodes = meta["nodes"]
    if entity not in nodes:
        return 0.0
    idx = nodes.index(entity)
    vec = emb[idx]
    mean = emb.mean(axis=0)
    dist = float(np.linalg.norm(vec-mean))
    # normalize to 0-1 by heuristic
    score = 1.0 - 1.0/(1.0+dist)
    return score

if __name__=="__main__":
    train_and_save()
    print("example score alice:", score_node("alice@example.com"))
