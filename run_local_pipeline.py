# run_local_pipeline.py
import importlib, time, threading
from dotenv import load_dotenv
load_dotenv()
import os
DEV_MODE = os.getenv("DEV_MODE", "true").lower() in ("1","true","yes")

# import modules
from services.ingest import app as ingest_app
from services.normalizer import normalizer as normalizer_module
from services.template_miner import miner as miner_module
from services.enrich import enrich as enrich_module
from services.consumer import consumer as consumer_module

# create simple in-memory queues
from queue import Queue
q_raw = Queue(maxsize=1000)
q_norm = Queue(maxsize=1000)
q_enriched = Queue(maxsize=1000)

def ingest_pub(ev):
    q_raw.put(ev)

def norm_publish(ev):
    q_norm.put(ev)

def miner_publish(ev):
    # miner outputs templates; for now we just ignore forwarding
    pass

def enrich_publish(ev):
    q_enriched.put(ev)

def raw_generator():
    # generator that yields events for normalizer
    while True:
        ev = ingest_app.gen_event()
        yield ev
        time.sleep(0.12)

def ingest_thread():
    print("[LOCAL] Starting ingest thread")
    ingest_app.run_producer(publish_fn=ingest_pub)

def normalizer_thread():
    print("[LOCAL] Starting normalizer thread")
    def consume_gen():
        while True:
            ev = q_raw.get()
            yield ev
    normalizer_module.run_normalizer(publish_fn=norm_publish, consume_fn=consume_gen)

def miner_thread():
    print("[LOCAL] Starting miner thread")
    def consume_gen():
        while True:
            ev = q_norm.get()
            yield ev
    miner_module.run_miner(consume_fn=consume_gen, publish_fn=miner_publish)

def enrich_thread():
    print("[LOCAL] Starting enrich thread")
    def consume_gen():
        while True:
            ev = q_norm.get()
            yield ev
    enrich_module.run_enricher(consume_fn=consume_gen, publish_fn=enrich_publish)

def consumer_thread():
    print("[LOCAL] Starting consumer thread")
    def consume_gen():
        while True:
            ev = q_enriched.get()
            yield ev
    consumer_module.run_consumer(consume_fn=consume_gen)

if __name__ == "__main__":
    # Start threads for pipeline
    t_ing = threading.Thread(target=ingest_thread, daemon=True)
    t_norm = threading.Thread(target=normalizer_thread, daemon=True)
    t_miner = threading.Thread(target=miner_thread, daemon=True)
    t_enr = threading.Thread(target=enrich_thread, daemon=True)
    t_cons = threading.Thread(target=consumer_thread, daemon=True)

    t_ing.start()
    t_norm.start()
    t_miner.start()
    t_enr.start()
    t_cons.start()

    print("Local pipeline running. Press Ctrl-C to exit.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down.")
        os._exit(0)


"""
Run a full in-process pipeline for local development.
Wires ingest -> normalizer -> template miner -> enricher -> consumer.process_event
No Kafka required when DEV_MODE=true in .env
"""
