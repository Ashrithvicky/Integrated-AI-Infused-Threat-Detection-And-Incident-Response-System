# services/graph_service/graph_ingest.py
import json, os
from flask import Flask, jsonify
from dotenv import load_dotenv
load_dotenv()
from kafka import KafkaConsumer
import networkx as nx
from threading import Thread

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
TOPIC = "enriched-events"
consumer = None
try:
    consumer = KafkaConsumer(TOPIC, bootstrap_servers=KAFKA_BOOTSTRAP,
                         value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                         auto_offset_reset='earliest', consumer_timeout_ms=1000)
    kafka_ok = True
except Exception as e:
    print("Kafka not available for graph service:", e)
    kafka_ok = False

G = nx.DiGraph()
app = Flask(__name__)

def consume_loop():
    print("Graph ingest listening to", TOPIC)
    while True:
        if kafka_ok:
            for msg in consumer:
                ev = msg.value
                u = ev.get("entity_id")
                ip = ev.get("geo",{}).get("ip")
                if ip:
                    G.add_edge(u, ip, type="used_ip")
                et = ev.get("event_type")
                if et:
                    G.add_edge(u, et, type="event_type")
        else:
            # sleep if no kafka
            import time; time.sleep(2)

Thread(target=consume_loop, daemon=True).start()

@app.route("/neighbors/<entity>")
def neighbors(entity):
    if entity not in G:
        return jsonify({"node": entity, "neighbors": []})
    neigh = []
    for nbr in G.neighbors(entity):
        neigh.append({"id": nbr, "edge": G[entity][nbr]})
    return jsonify({"node": entity, "neighbors": neigh})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8002)
