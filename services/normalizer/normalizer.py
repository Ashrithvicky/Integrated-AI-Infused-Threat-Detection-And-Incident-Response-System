# services/normalizer/normalizer.py
import json, os
from datetime import datetime
from kafka import KafkaConsumer, KafkaProducer
from dotenv import load_dotenv
load_dotenv()

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
IN_TOPIC = "raw-events"
OUT_TOPIC = "normalized-events"

# try Kafka, but allow other modes
consumer = None
producer = None
try:
    consumer = KafkaConsumer(IN_TOPIC, bootstrap_servers=KAFKA_BOOTSTRAP,
                             value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                             auto_offset_reset='earliest', consumer_timeout_ms=1000)
    producer = KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP,
                             value_serializer=lambda v: json.dumps(v).encode("utf-8"))
    kafka_ok = True
except Exception as e:
    print("Kafka not available in normalizer:", e)
    kafka_ok = False

def normalize(raw_event: dict) -> dict:
    normalized = {
        "event_id": raw_event.get("event_id"),
        "timestamp": raw_event.get("timestamp"),
        "ingest_ts": datetime.utcnow().isoformat() + "Z",
        "source": raw_event.get("source"),
        "entity_type": raw_event.get("entity_type"),
        "entity_id": raw_event.get("entity_id"),
        "event_type": raw_event.get("event_type"),
        "geo": raw_event.get("geo", {}),
        "raw": raw_event.get("raw", {})
    }
    if normalized["event_type"] in ("IAMPolicyChange", "EC2StartInstances"):
        normalized["severity_hint"] = "high"
    elif normalized["event_type"] == "AuthFailure":
        normalized["severity_hint"] = "medium"
    else:
        normalized["severity_hint"] = "low"
    return normalized

def run_normalizer(publish_fn=None, consume_fn=None):
    print("Normalizer started")
    if consume_fn:
        # in-process pipeline: read events from in-memory generator
        for raw in consume_fn():
            norm = normalize(raw)
            if publish_fn:
                publish_fn(norm)
            else:
                print("Norm:", norm)
    elif kafka_ok:
        for msg in consumer:
            raw = msg.value
            norm = normalize(raw)
            producer.send(OUT_TOPIC, norm)
            print("normalized", norm["event_type"], norm["entity_id"])
    else:
        print("No consume method available for normalizer")

if __name__ == "__main__":
    run_normalizer()
