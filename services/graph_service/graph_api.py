# services/graph_service/graph_api.py
"""
Graph API:

- /neighbors/<entity>  -> direct neighbors in entity graph
- /subgraph/<entity>   -> ego subgraph (radius 2)
- /attribution/<entity> -> simple attribution score (PageRank + degree)
- /correlate/<entity>  -> cross-domain correlation (via correlator)
"""

import os
import sys
from flask import Flask, jsonify

# ensure repo root on path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import networkx as nx
from services.graph_service.graph_builder import G, load_graph
from services.correlation.correlator import correlate_entity

app = Flask(__name__)

# load graph at startup
load_graph()


@app.route("/neighbors/<entity>")
def neighbors(entity):
    if entity not in G:
        return jsonify({"node": entity, "neighbors": []})
    neigh = []
    for nbr in G.neighbors(entity):
        neigh.append({
            "id": nbr,
            "edge": G[entity][nbr]
        })
    return jsonify({"node": entity, "neighbors": neigh})


@app.route("/subgraph/<entity>")
def subgraph(entity):
    if entity not in G:
        return jsonify({"node": entity, "subgraph": {}})
    ego = nx.ego_graph(G, entity, radius=2)
    from networkx.readwrite import json_graph
    data = json_graph.node_link_data(ego)
    return jsonify(data)


@app.route("/attribution/<entity>")
def attribution(entity):
    if len(G) == 0 or entity not in G:
        return jsonify({"entity": entity, "attribution_score": 0.0, "pagerank": 0.0, "degree": 0})

    pr = nx.pagerank(G) if len(G) > 0 else {}
    deg = dict(G.degree())
    score = float((pr.get(entity, 0.0) + (deg.get(entity, 0) / (len(G) + 1))) / 2.0)
    return jsonify({
        "entity": entity,
        "attribution_score": score,
        "pagerank": pr.get(entity, 0.0),
        "degree": deg.get(entity, 0)
    })


@app.route("/correlate/<entity>")
def correlate(entity):
    """
    Cross-domain correlation endpoint:
    wraps services.correlation.correlator.correlate_entity
    """
    info = correlate_entity(entity)
    return jsonify(info)


if __name__ == "__main__":
    # default: run on 0.0.0.0:8002
    app.run(host="0.0.0.0", port=8002)
