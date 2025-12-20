# services/template-miner/miner.py
"""
Template miner: prefer Drain3 if installed; otherwise use a lightweight fallback.
This file is safe to import even if drain3 is not installed.
"""
import json, os, re
from datetime import datetime

# Try to import Drain3; if not available, use fallback
try:
    from drain3.auto_template import TemplateMiner
    from drain3.template_miner_config import TemplateMinerConfig
    DRAIN3_OK = True
except Exception:
    DRAIN3_OK = False

# Try Kafka availability
try:
    from kafka import KafkaConsumer, KafkaProducer
    KAFKA_OK = True
except Exception:
    KAFKA_OK = False

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
IN_TOPIC = "normalized-events"
OUT_TOPIC = "templates"

# Drain3 setup
miner = None
if DRAIN3_OK:
    conf = TemplateMinerConfig()
    miner = TemplateMiner(conf)

# Simple fallback template miner using regex to remove numeric tokens, paths, uuids, timestamps
UUID_RE = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
NUM_RE = re.compile(r"\b\d+\b")
TS_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")

def fallback_template(text: str) -> dict:
    t = text
    t = UUID_RE.sub("<UUID>", t)
    t = TS_RE.sub("<TS>", t)
    t = IP_RE.sub("<IP>", t)
    t = NUM_RE.sub("<NUM>", t)
    t = re.sub(r"\s+", " ", t).strip()
    tid = abs(hash(t)) % (10**9)
    return {"clusterId": str(tid), "template": t}

def mine_and_emit(event, publish_fn=None):
    content = event.get("raw", {}).get("details", "") or event.get("event_type", "")
    if DRAIN3_OK and miner is not None:
        templ = miner.add_log_message(content)
        out = {
            "template_id": templ.get("clusterId"),
            "template": templ.get("template"),
            "event_id": event.get("event_id"),
            "entity_id": event.get("entity_id")
        }
    else:
        templ = fallback_template(content)
        out = {
            "template_id": templ["clusterId"],
            "template": templ["template"],
            "event_id": event.get("event_id"),
            "entity_id": event.get("entity_id")
        }

    if publish_fn:
        publish_fn(out)
    elif KAFKA_OK:
        try:
            producer = KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP,
                                     value_serializer=lambda v: json.dumps(v).encode("utf-8"))
            producer.send(OUT_TOPIC, out)
        except Exception as e:
            print("template-miner kafka send error:", e)
            print("template:", out)
    else:
        print("template (fallback):", out)

def run_miner(consume_fn=None, publish_fn=None):
    print("Template miner started - Drain3 OK:", DRAIN3_OK)
    if consume_fn:
        for ev in consume_fn():
            mine_and_emit(ev, publish_fn)
    elif KAFKA_OK:
        consumer = KafkaConsumer(IN_TOPIC, bootstrap_servers=KAFKA_BOOTSTRAP,
                                 value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                                 auto_offset_reset='earliest')
        for msg in consumer:
            mine_and_emit(msg.value)
    else:
        print("No consume method available for template miner")
