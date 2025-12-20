# services/consumer/feature_builder.py
'''import json
from datetime import datetime
from services.consumer.redis_client import get_redis_client

# Create a single redis client instance (in-memory fallback if Redis not present)
_redis_client = get_redis_client()

SESSION_WINDOW_SECONDS = 300  # 5 minutes

def session_key(entity_id):
    return f"session:{entity_id}"

def update_session(redis_client, normalized_event):
    """
    This version accepts a redis_client, but we provide a default below for compatibility.
    """
    key = session_key(normalized_event["entity_id"])
    data = redis_client.get(key)
    # if the underlying redis client returns bytes, decode; if it returns None, handle
    if isinstance(data, (bytes, bytearray)):
        try:
            data = data.decode("utf-8")
        except Exception:
            pass
    if data is None:
        session = {"first_ts": datetime.utcnow().isoformat(), "last_ts": datetime.utcnow().isoformat(),
                   "events": [normalized_event["event_type"]], "count": 1}
    else:
        try:
            session = json.loads(data)
        except Exception:
            # if stored value was not json, reset
            session = {"first_ts": datetime.utcnow().isoformat(), "last_ts": datetime.utcnow().isoformat(),
                       "events": [normalized_event["event_type"]], "count": 1}
        session["last_ts"] = datetime.utcnow().isoformat()
        session["events"].append(normalized_event["event_type"])
        session["count"] = session.get("count", 0) + 1
        if len(session["events"]) > 200:
            session["events"] = session["events"][-200:]
    # store with TTL
    redis_client.set(key, json.dumps(session), ex=SESSION_WINDOW_SECONDS)
    return session

def session_features(session):
    return {
        "count": session.get("count", 0),
        "unique_events": len(set(session.get("events", []))),
    }

# compatibility helper: external code can import update_session and pass client
def update_session_default(normalized_event):
    return update_session(_redis_client, normalized_event)
''' 

# services/consumer/feature_builder.py

"""
Session feature builder for UEBA.

- Derives a stable entity_id for a user / IP
- Maintains a simple session in Redis (or in-memory fallback)
- Exposes session_features() -> {"count": N, "unique_events": M}
"""

import json
import time
from typing import Dict, Any

SESSION_WINDOW_SECONDS = 900  # 15 minutes


def session_key(entity_id: str) -> str:
    return f"sess:{entity_id}"


def derive_entity_id(ev: Dict[str, Any]) -> str:
    """
    Try to find a reasonable entity identifier for the event:
    - If ev["entity_id"] exists, use it (already normalized)
    - Else use CloudTrail userIdentity.userName / arn / principalId
    - Else use sourceIPAddress
    - Else fall back to 'unknown'
    """
    if ev.get("entity_id"):
        return str(ev["entity_id"])

    ui = ev.get("userIdentity") or {}
    if isinstance(ui, dict):
        for key in ("userName", "arn", "principalId"):
            v = ui.get(key)
            if v:
                return str(v)

    if ev.get("sourceIPAddress"):
        return str(ev["sourceIPAddress"])

    return "unknown"


def update_session(redis_client, normalized_event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update per-entity session state in Redis (or fallback).
    Returns a session dict:
      { "entity_id": ..., "events": [...], "last_ts": ..., "count": N, "unique_events": M }
    """
    # Ensure entity_id exists
    entity = derive_entity_id(normalized_event)
    normalized_event["entity_id"] = entity  # so downstream code sees it

    key = session_key(entity)

    # Load existing session, if any
    raw = redis_client.get(key)
    if raw:
        try:
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8")
            sess = json.loads(raw)
        except Exception:
            sess = {}
    else:
        sess = {}

    events = sess.get("events") or []
    # Prefer CloudTrail eventName; fallback to generic event_type
    ev_type = normalized_event.get("eventName") or normalized_event.get("event_type") or "UnknownEvent"

    events.append(ev_type)
    now = time.time()

    sess["entity_id"] = entity
    sess["events"] = events
    sess["last_ts"] = now
    sess["count"] = len(events)
    sess["unique_events"] = len(set(events))

    # Store back in Redis; we can live without TTL for your demo
    try:
        redis_client.set(key, json.dumps(sess))
    except TypeError:
        # if DummyRedis.set does not accept extra args, ignore
        redis_client.set(key, json.dumps(sess))

    return sess


def session_features(sess: Dict[str, Any]) -> Dict[str, int]:
    """
    Produce the small feature vector used by IsolationForest / River:
      - count: total events in session
      - unique_events: number of distinct event types
    """
    events = sess.get("events") or []
    return {
        "count": len(events),
        "unique_events": len(set(events)),
    }
