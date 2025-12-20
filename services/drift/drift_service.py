# services/drift/drift_service.py

import os
import sys
import time
import json
from datetime import datetime
from deepdiff import DeepDiff
from dotenv import load_dotenv

load_dotenv()

# Ensure repo root import
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from services.drift.config_snapshot import (
    take_snapshot_from_file,
    save_snapshot,
    read_snapshot,
)
from services.drift.rules_engine import run_policy_checks
from services.normalizer.normalizer import normalize
from services.enrich.enrich import enrich_event
from services.consumer.consumer import process_event

SNAPSHOT_DIR = os.getenv("DRIFT_SNAPSHOT_DIR", "data/drift_snapshots")
SOURCE_FILE = os.getenv("DRIFT_SOURCE_FILE", "examples/config_example.json")
POLL_INTERVAL = int(os.getenv("DRIFT_POLL_SECONDS", "30"))
ALERT_ON_CHANGE = os.getenv("DRIFT_ALERT_ON_CHANGE", "true").lower() in (
    "1",
    "true",
    "yes",
)


def ensure_snapshot_dir():
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)


def latest_snapshot_path():
    return os.path.join(SNAPSHOT_DIR, "latest.json")


def emit_events(diff, new_snapshot, record_id, ts):
    # ConfigDrift event
    cfg_ev = {
        "event_id": record_id,
        "timestamp": ts,
        "source": "config_drift_service",
        "entity_type": "infrastructure",
        "entity_id": new_snapshot.get("source", "config_source"),
        "event_type": "ConfigDrift",
        "raw": {"summary": "Configuration drift detected", "diff": diff},
    }

    norm = normalize(cfg_ev)
    enrich_event(norm, publish_fn=None)
    process_event(norm)
    print("[DRIFT] Emitted ConfigDrift event")

    # Policy violations
    findings = run_policy_checks(new_snapshot.get("content", {}))
    for f in findings:
        pv_ev = {
            "event_id": f"pv-{record_id}-{f.get('issue')}",
            "timestamp": ts,
            "source": "policy_drift_service",
            "entity_type": "infrastructure",
            "entity_id": new_snapshot.get("source", "config_source"),
            "event_type": "PolicyViolation",
            "raw": f,
        }
        norm2 = normalize(pv_ev)
        enrich_event(norm2, publish_fn=None)
        process_event(norm2)
        print(f"[DRIFT] Emitted PolicyViolation: {f.get('issue')}")


def run_forever():
    ensure_snapshot_dir()
    latest_path = latest_snapshot_path()

    print(
        f"[DRIFT] Watching {SOURCE_FILE} | interval={POLL_INTERVAL}s | snapshot_dir={SNAPSHOT_DIR}"
    )

    while True:
        try:
            new_snapshot = take_snapshot_from_file(SOURCE_FILE)
            prev_snapshot = read_snapshot(latest_path)

            if prev_snapshot is None:
                # First run / snapshot recovery
                save_snapshot(new_snapshot, latest_path)
                print("[DRIFT] Baseline snapshot initialized")
                time.sleep(POLL_INTERVAL)
                continue

            prev_content = prev_snapshot.get("content", {})
            new_content = new_snapshot.get("content", {})

            diff = DeepDiff(prev_content, new_content, ignore_order=True).to_dict()
            changed = bool(diff)

            record_id = f"drift-{datetime.utcnow().strftime('%Y%m%dT%H%M%S')}"
            ts = datetime.utcnow().isoformat() + "Z"

            if changed:
                record = {
                    "drift_id": record_id,
                    "timestamp": ts,
                    "changed": True,
                    "diff": diff,
                    "prev_snapshot": prev_snapshot,
                    "new_snapshot": new_snapshot,
                }

                record_path = os.path.join(
                    SNAPSHOT_DIR, f"{record_id}.json"
                )
                with open(record_path, "w", encoding="utf-8") as f:
                    json.dump(record, f, indent=2, default=str)

                if ALERT_ON_CHANGE:
                    emit_events(diff, new_snapshot, record_id, ts)

            # Update baseline snapshot AFTER comparison
            save_snapshot(new_snapshot, latest_path)

        except FileNotFoundError:
            print("[DRIFT] SOURCE_FILE not found:", SOURCE_FILE)
        except Exception as e:
            print("[DRIFT] Error:", e)

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    run_forever()
