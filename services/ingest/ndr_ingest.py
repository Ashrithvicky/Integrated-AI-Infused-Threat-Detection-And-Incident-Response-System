# ndr_ingest.py - stub that reads netflow-like lines and publishes normalized flows
import random, time
def gen_flow():
    return {"event_id":str(time.time()), "timestamp":time.time(), "source":"netflow", "entity_type":"ip", "entity_id":f"{random.randint(1,255)}.{random.randint(1,255)}.1.1", "event_type":"netflow", "raw":{}}
def run(publish_fn):
    while True:
        publish_fn(gen_flow())
        time.sleep(0.05)
