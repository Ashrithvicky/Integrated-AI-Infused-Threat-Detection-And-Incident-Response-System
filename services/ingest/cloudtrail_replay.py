'''
Docstring for services.ingest.cloudtrail_replay
''''''# services/ingest/cloudtrail_replay.py
"""
Replay AWS CloudTrail logs into the detection pipeline.

Usage (from repo root, venv activated, PYTHONPATH="."):

    python services/ingest/cloudtrail_replay.py examples/cloudtrail_sample.json
"""
'''

'''
import os
import sys
import json
import time
import uuid
import logging
from typing import Any, Dict, List

# ----- logging -----
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("cloudtrail_replay")

# ----- make sure we can import project modules -----
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

try:
    from services.normalizer.normalizer import normalize
    from services.enrich.enrich import enrich_event
    from services.consumer.consumer import process_event
except Exception:
    # fallback if run differently
    from normalizer.normalizer import normalize
    from enrich.enrich import enrich_event
    from consumer.consumer import process_event


def load_cloudtrail_records(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # CloudTrail usually uses { "Records": [ ... ] }
    if isinstance(data, dict) and "Records" in data:
        return data["Records"]
    # or plain list of records
    if isinstance(data, list):
        return data

    raise ValueError(f"Unrecognized CloudTrail JSON structure in {path}")


def cloudtrail_record_to_event(rec: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a single CloudTrail record into our generic event dict."""

    user_identity = rec.get("userIdentity") or {}
    event_name = rec.get("eventName")
    event_time = rec.get("eventTime")
    aws_region = rec.get("awsRegion")
    source_ip = rec.get("sourceIPAddress")
    user_type = (user_identity.get("type") or "").lower()

    # figure out an entity_id (user, role, root, etc.)
    username = user_identity.get("userName")
    if not username:
        username = (
            user_identity.get("arn")
            or user_identity.get("principalId")
            or "unknown"
        )

    # entity_type based on identity type
    if user_type == "root":
        entity_type = "root"
    elif "role" in user_type:
        entity_type = "role"
    else:
        entity_type = "user"

    event_id = rec.get("eventID") or str(uuid.uuid4())

    ev = {
        "event_id": event_id,
        "timestamp": event_time,
        "source": "aws_cloudtrail",
        "entity_type": entity_type,
        "entity_id": username,
        "event_type": event_name,
        "raw": rec,
        # a few extras that our normalizer/enricher can use
        "cloud": {
            "region": aws_region,
            "source_ip": source_ip,
            "user_type": user_type,
        },
    }
    return ev


def replay_file(path: str, delay: float = 0.2):
    records = load_cloudtrail_records(path)
    log.info("Loaded %d CloudTrail records from %s", len(records), path)

    alerts = 0
    total = 0
    for rec in records:
        total += 1
        ev = cloudtrail_record_to_event(rec)

        try:
            # 1) normalize
            norm = normalize(ev)

            # 2) enrich (TI, etc.) – using in-process mode (no Kafka)
            enrich_event(norm, publish_fn=None)

            # 3) send into consumer (UEBA + fusion + DB + alerts)
            result = process_event(norm)

            if result.get("label") == "problem":
                alerts += 1
                log.info(
                    "ALERT: entity=%s event=%s score=%.3f label=%s",
                    norm.get("entity_id"),
                    norm.get("event_type"),
                    result.get("final_score", 0.0),
                    result.get("label"),
                )
            else:
                log.debug(
                    "OK: entity=%s event=%s score=%.3f",
                    norm.get("entity_id"),
                    norm.get("event_type"),
                    result.get("final_score", 0.0),
                )
        except Exception as e:
            log.exception("Error processing record: %s", e)

        # small delay to simulate stream (optional)
        if delay > 0:
            time.sleep(delay)

    log.info("Replay complete: %d records, %d alerts", total, alerts)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python services/ingest/cloudtrail_replay.py <cloudtrail_json>")
        sys.exit(1)

    json_path = sys.argv[1]
    if not os.path.exists(json_path):
        print(f"File not found: {json_path}")
        sys.exit(1)

    # Allow optional delay override
    delay_sec = 0.2
    if len(sys.argv) >= 3:
        try:
            delay_sec = float(sys.argv[2])
        except ValueError:
            pass

    replay_file(json_path, delay=delay_sec)
'''
'''
import json, time, sys
from services.consumer.consumer import process_event

if len(sys.argv) < 2:
    print("Usage: python cloudtrail_replay.py <file.json> [delay]")
    sys.exit(1)

path = sys.argv[1]
delay = float(sys.argv[2]) if len(sys.argv) > 2 else 0.2

events = json.load(open(path))

print(f"Loaded {len(events)} CloudTrail records")

for ev in events:
    print("Processing:", ev.get("eventName"), ev.get("userIdentity",{}).get("userName"))
    process_event(ev)
    time.sleep(delay)

print("Replay finished.")

'''

# services/ingest/cloudtrail_replay.py
import json
import sys
import time

from services.consumer.consumer import process_event


def load_events(path: str):
    data = json.load(open(path, "r", encoding="utf-8"))
    # Support either:
    #  - array of events
    #  - {"Records": [ ... ]} style
    if isinstance(data, dict) and "Records" in data:
        return data["Records"]
    if isinstance(data, list):
        return data
    raise ValueError("Unsupported JSON format for CloudTrail replay")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python services/ingest/cloudtrail_replay.py <file.json> [delay_seconds]")
        sys.exit(1)

    path = sys.argv[1]
    delay = float(sys.argv[2]) if len(sys.argv) > 2 else 0.2

    events = load_events(path)
    print(f"Loaded {len(events)} CloudTrail records from {path}")

    for ev in events:
        ev_name = ev.get("eventName") or ev.get("event_type")
        user = (ev.get("userIdentity") or {}).get("userName") or ev.get("entity_id")
        print(f"Processing event: {ev_name} user={user}")
        out = process_event(ev)
        print(" -> result:", out.get("label"), "score", out.get("final_score"))
        time.sleep(delay)

    print("Replay finished.")
