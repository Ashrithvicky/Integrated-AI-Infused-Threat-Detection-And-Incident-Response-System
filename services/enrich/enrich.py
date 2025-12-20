# services/enrich/enrich.py
"""
Simple enrichment: listens to normalized-events, performs light enrichments (geo/ip reputation stub),
stores enriched event to 'enriched-events' topic and to Redis for quick lookup.
This version is tolerant to Redis being unavailable (uses in-memory fallback).
"""
import json, os
from datetime import datetime
from kafka import KafkaConsumer, KafkaProducer
from dotenv import load_dotenv
load_dotenv()

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")

IN_TOPIC = "normalized-events"
OUT_TOPIC = "enriched-events"

# Try to import redis and connect; if it fails, use an in-memory dict fallback
use_redis = False
redis_client = None
_mem_cache = {}

try:
    import redis
    try:
        redis_client = redis.Redis(host=REDIS_HOST, port=6379, db=0, socket_connect_timeout=1)
        # quick test ping
        redis_client.ping()
        use_redis = True
        print("[redis_client] Connected to Redis at", REDIS_HOST)
    except Exception as e:
        print("[redis_client] Warning: Redis not reachable at {}:6379 — using in-memory fallback".format(REDIS_HOST))
        use_redis = False
except Exception:
    print("[redis_client] redis package not installed — using in-memory fallback")
    use_redis = False

producer = None
consumer = None
kafka_ok = False
try:
    consumer = KafkaConsumer(IN_TOPIC, bootstrap_servers=KAFKA_BOOTSTRAP,
                         value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                         auto_offset_reset='earliest', consumer_timeout_ms=1000)
    producer = KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP,
                         value_serializer=lambda v: json.dumps(v).encode("utf-8"))
    kafka_ok = True
except Exception as e:
    print("Kafka not available for enrich:", e)
    kafka_ok = False

def ip_reputation_stub(ip: str):
    bad_ips = {"9.10.11.12": 0.9}
    return bad_ips.get(ip, 0.0)

def cache_set(key, value, ex=3600):
    """Set key in Redis if available, else in in-memory dict."""
    if use_redis and redis_client:
        try:
            redis_client.set(key, json.dumps(value), ex=ex)
            return
        except Exception as e:
            # failover to in-memory
            _mem_cache[key] = value
    else:
        _mem_cache[key] = value

def cache_get(key):
    if use_redis and redis_client:
        try:
            v = redis_client.get(key)
            if v:
                return json.loads(v.decode("utf-8"))
            return None
        except Exception:
            return _mem_cache.get(key)
    else:
        return _mem_cache.get(key)

def enrich_event(ev, publish_fn=None):
    ip = ev.get("geo", {}).get("ip")
    reput = ip_reputation_stub(ip) if ip else 0.0
    ev["ti"] = {"ip_reputation": reput}
    ev["enrich_ts"] = datetime.utcnow().isoformat() + "Z"
    if publish_fn and kafka_ok is False:
        # In direct mode we call publish_fn (consumer pipeline)
        publish_fn(ev)
    elif kafka_ok and producer:
        # In Kafka mode we send to enriched-events topic
        try:
            producer.send(OUT_TOPIC, ev)
        except Exception as e:
            print("Kafka send failed for enrich:", e)
    # cache last event per entity for quick UI retrieval
    try:
        key = f"last:{ev.get('entity_type')}:{ev.get('entity_id')}"
        cache_set(key, ev, ex=3600)
    except Exception as e:
        print("[enrich] cache set error (falling back to in-memory)", e)
    print("enriched", ev.get("event_type"), ev.get("entity_id"), "rep:", reput)

def run_enricher(consume_fn=None, publish_fn=None):
    print("Enricher started")
    if consume_fn:
        for ev in consume_fn():
            enrich_event(ev, publish_fn)
    elif kafka_ok:
        for msg in consumer:
            enrich_event(msg.value)
    else:
        print("No consume method available for enricher")
