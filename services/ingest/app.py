# services/ingest/app.py
import json, os, time, uuid, random
from datetime import datetime
from kafka import KafkaProducer
from dotenv import load_dotenv
load_dotenv()

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
TOPIC = "raw-events"

# if Kafka not available in dev, ingest can be used by run_local_pipeline directly
try:
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    kafka_ok = True
except Exception as e:
    print("Kafka producer unavailable:", e)
    producer = None
    kafka_ok = False

USERS = ["alice@example.com","bob@example.com","carol@example.com","devops@example.com"]
IPS = ["1.2.3.4","5.6.7.8","9.10.11.12","13.14.15.16"]
EVENT_TYPES = ["ConsoleLogin","S3GetObject","EC2StartInstances","IAMPolicyChange","AuthFailure","ProcessStart"]

def gen_event():
    user = random.choice(USERS)
    ip = random.choice(IPS)
    et = random.choices(EVENT_TYPES, weights=[25,20,10,5,15,25])[0]
    return {
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "source": "simulated",
        "entity_type": "user",
        "entity_id": user,
        "event_type": et,
        "geo": {"ip": ip},
        "raw": {"details": f"Simulated {et} by {user} from {ip}"}
    }

def run_producer(interval=0.12, publish_fn=None):
    print("Starting ingest producer (interval", interval, ")")
    while True:
        ev = gen_event()
        if publish_fn:
            publish_fn(ev)
        elif kafka_ok and producer:
            producer.send(TOPIC, ev)
        else:
            print("No publish method; printing event:", ev)
        time.sleep(interval)

if __name__ == "__main__":
    run_producer()
