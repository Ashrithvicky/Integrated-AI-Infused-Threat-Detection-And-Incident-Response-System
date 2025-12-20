# services/drift/config_snapshot.py
import json, os, time
from datetime import datetime

def load_json_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_snapshot(snapshot_obj, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(snapshot_obj, f, indent=2, default=str)

def take_snapshot_from_file(source_path):
    """
    Reads a JSON file (cloud API output or local config) and returns snapshot object with metadata.
    """
    obj = load_json_file(source_path)
    return {
        "snapshot_ts": datetime.utcnow().isoformat()+"Z",
        "source": source_path,
        "content": obj
    }

def read_snapshot(path):
    if not os.path.exists(path):
        return None
    return load_json_file(path)
