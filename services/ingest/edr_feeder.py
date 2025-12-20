# edr_feeder.py


# --- add at top of file (first 10 lines) ---
import os, sys
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
# ------------------------------------------
"""
Feeder for EDR logs (JSON lines or JSON arrays).
Accepts vendor JSON lines (CrowdStrike, Osquery, Sysmon-like JSON).
Usage:
    python edr_feeder.py --file path\to\edr.json --direct
"""
import argparse, json, os
from kafka import KafkaProducer
from dotenv import load_dotenv
load_dotenv()

try:
    from services.normalizer.normalizer import normalize
    from services.enrich.enrich import enrich_event
    from services.consumer.consumer import process_event
except Exception:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from normalizer import normalize
    from enrich import enrich_event
    from consumer import process_event

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
TOPIC = "raw-events"

def kafka_producer():
    try:
        return KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP,
                             value_serializer=lambda v: json.dumps(v).encode("utf-8"))
    except Exception as e:
        print("Kafka producer unavailable:", e)
        return None

def map_edr_record(rec):
    # Map common EDR fields into canonical event
    # Adjust according to your EDR format
    event_type = rec.get("event_type") or rec.get("action") or rec.get("eventName") or "EDREvent"
    user = rec.get("user") or rec.get("username") or rec.get("principal") or "unknown"
    ip = rec.get("remote_ip") or rec.get("src_ip") or None
    mapped = {
        "event_id": rec.get("id") or rec.get("event_id") or rec.get("uuid"),
        "timestamp": rec.get("timestamp") or rec.get("time"),
        "source": "edr",
        "entity_type": rec.get("entity_type") or "host",
        "entity_id": rec.get("host") or user,
        "event_type": event_type,
        "geo": {"ip": ip} if ip else {},
        "raw": rec
    }
    return mapped

def publish_file(path, mode="direct"):
    prod = None
    if mode == "kafka":
        prod = kafka_producer()
        if prod is None:
            print("Kafka produce unavailable; aborting kafka publish.")
            return

    # support JSON lines or JSON array
    items = []
    with open(path, "r", encoding="utf-8") as f:
        first = f.read(1)
        f.seek(0)
        if first == "[":
            items = json.load(f)
        else:
            # JSON lines
            for line in f:
                line=line.strip()
                if not line: continue
                items.append(json.loads(line))
    c=0
    for rec in items:
        ev = map_edr_record(rec)
        if mode == "kafka":
            prod.send(TOPIC, ev); c+=1
        else:
            norm = normalize(ev); enrich_event(norm, publish_fn=None); process_event(norm); c+=1
    print(f"Published {c} EDR events (mode={mode}).")

if __name__ == "__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--file","-f", required=True)
    p.add_argument("--kafka", action="store_true")
    p.add_argument("--direct", action="store_true")
    args=p.parse_args()
    if args.kafka:
        publish_file(args.file, mode="kafka")
    else:
        publish_file(args.file, mode="direct")
