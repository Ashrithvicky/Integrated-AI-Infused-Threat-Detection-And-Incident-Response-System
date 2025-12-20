# edr_ingest.py - stub that reads a local EDR JSON file and publishes to pipeline
import json, time
def run_file(path, publish_fn):
    with open(path) as f:
        for line in f:
            ev = json.loads(line)
            publish_fn(ev)
            time.sleep(0.05)
