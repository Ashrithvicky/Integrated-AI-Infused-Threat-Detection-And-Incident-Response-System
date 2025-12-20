# services/federated/server.py
from flask import Flask, request, jsonify
import numpy as np, json
app = Flask(__name__)
GLOBAL = None
CLIENTS = {}

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    cid = data.get("client_id")
    CLIENTS[cid] = {"last": None}
    return jsonify({"status":"ok","client_id":cid})

@app.route("/submit_update", methods=["POST"])
def submit_update():
    global GLOBAL
    payload = request.json
    cid = payload["client_id"]
    weights = payload["weights"]
    CLIENTS[cid]["last"] = weights
    # average available
    all_w = [v["last"] for v in CLIENTS.values() if v["last"]]
    if not all_w:
        return jsonify({"status":"ok"})
    import numpy as np
    avg = list(np.mean(all_w, axis=0))
    GLOBAL = avg
    return jsonify({"status":"ok","global_updated":True})

@app.route("/get_global", methods=["GET"])
def get_global():
    return jsonify({"global": GLOBAL})

if __name__=="__main__":
    app.run(host="0.0.0.0", port=9000)
