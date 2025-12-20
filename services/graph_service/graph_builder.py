# services/graph_service/graph_builder.py
import networkx as nx, json, os
from kafka import KafkaConsumer
from dotenv import load_dotenv
load_dotenv()

G = nx.DiGraph()
STORE_PATH = os.getenv("GRAPH_STORE_PATH", "data/graph_store.json")
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP","localhost:9092")
TOPIC = os.getenv("GRAPH_IN_TOPIC","enriched-events")

def add_event_to_graph(ev):
    # add nodes and edges (user->ip, user->host, host->process)
    src = ev.get("entity_id")
    et = ev.get("event_type")
    ip = ev.get("geo",{}).get("ip")
    if src and ip:
        G.add_node(src, type="entity")
        G.add_node(ip, type="ip")
        G.add_edge(src, ip, type="used_ip", ts=ev.get("timestamp"))
    if src and et:
        G.add_node(et, type="event_type")
        G.add_edge(src, et, type="did_event", ts=ev.get("timestamp"))
    # persist occasionally
    save_graph()

def save_graph():
    os.makedirs(os.path.dirname(STORE_PATH), exist_ok=True)
    data = nx.node_link_data(G)
    with open(STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_graph():
    global G
    if os.path.exists(STORE_PATH):
        data = json.load(open(STORE_PATH, "r", encoding="utf-8"))
        G = nx.node_link_graph(data)
    return G
