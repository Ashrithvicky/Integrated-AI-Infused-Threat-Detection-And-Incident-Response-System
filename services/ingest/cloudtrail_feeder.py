# services/ingest/cloudtrail_feeder.py


# --- add at top of file (first 10 lines) ---
import os, sys
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
# ------------------------------------------
"""
Feeder for CloudTrail logs (robust, Windows-friendly).
"""

# --- FIX IMPORT PATHS ON WINDOWS ---
import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
# -----------------------------------

import argparse, json
from dotenv import load_dotenv
load_dotenv()

# Now imports work correctly
try:
    from services.normalizer.normalizer import normalize
    from services.enrich.enrich import enrich_event
    from services.consumer.consumer import process_event
except Exception as e:
    print("FATAL: Could not import pipeline modules:", e)
    raise

def read_json_flex(path):
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    text = open(path, "r", encoding="utf-8").read()
    if not text.strip():
        raise ValueError("File is empty")
    text = text.strip()
    try:
        obj = json.loads(text)
        if isinstance(obj, list):
            return obj
        if isinstance(obj, dict):
            if "Records" in obj:
                return obj["Records"]
            return [obj]
    except Exception:
        lines = []
        for ln in text.splitlines():
            ln = ln.strip()
            if not ln:
                continue
            lines.append(json.loads(ln))
        return lines
    raise ValueError("Unrecognized JSON format")

def map_cloudtrail_record(rec):
    ui = rec.get("userIdentity") or {}
    user = ui.get("arn") or ui.get("userName") or ui.get("principalId") or "unknown"
    ip = rec.get("sourceIPAddress")

    return {
        "event_id": rec.get("eventID"),
        "timestamp": rec.get("eventTime"),
        "source": "aws:cloudtrail",
        "entity_type": "user",
        "entity_id": user,
        "event_type": rec.get("eventName", "CloudTrailEvent"),
        "geo": {"ip": ip} if ip else {},
        "raw": rec
    }

def publish_file(path):
    print(f"[feeder] reading {path}")
    try:
        records = read_json_flex(path)
    except Exception as e:
        print("JSON read error:", e)
        return

    print(f"[feeder] loaded {len(records)} record(s)")
    count = 0

    for rec in records:
        event = map_cloudtrail_record(rec)

        try:
            norm = normalize(event)
            enrich_event(norm, publish_fn=None)
            process_event(norm)
            count += 1
        except Exception as e:
            print("[feeder] error:", e)

    print(f"[feeder] processed {count} events.")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--file", "-f", required=True)
    args = p.parse_args()
    publish_file(args.file)
