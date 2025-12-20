# services/consumer/db.py  (replace whole file)
"""
DB wrapper used by the consumer API.
Provides get_alerts(limit) which returns a JSON-serializable list of dicts.
"""

import json
import logging
from decimal import Decimal
from datetime import datetime, date
from typing import Any

from services.consumer.mysql_db import get_conn

log = logging.getLogger("consumer.db")


def _serialize_value(v: Any):
    """Convert DB-returned value to JSON-serializable primitive where needed."""
    if v is None:
        return None
    if isinstance(v, (str, int, float, bool)):
        return v
    if isinstance(v, Decimal):
        try:
            return float(v)
        except Exception:
            return str(v)
    if isinstance(v, (datetime, date)):
        return v.isoformat(sep=" ")
    # attempt to parse JSON strings, otherwise string-ify
    if isinstance(v, str):
        try:
            return json.loads(v)
        except Exception:
            return v
    try:
        return json.loads(v) if isinstance(v, str) else v
    except Exception:
        return str(v)

# services/consumer/db.py  (update _normalize_row or add helper inside file)

def _extract_ip_from_event(obj):
    # common keys used by CloudTrail / enriched events
    for key in ("sourceIPAddress", "source_ip", "sourceIpAddress", "clientIp", "ip_address", "ip"):
        if isinstance(obj, dict) and key in obj and obj[key]:
            return obj[key]
    # nested common places
    if isinstance(obj, dict):
        # userIdentity / requestParameters often contain nested IPs (best-effort)
        for sub in ("requestParameters", "request_parameters", "request"):
            subobj = obj.get(sub)
            if isinstance(subobj, dict):
                for key in ("sourceIPAddress", "source_ip", "ip"):
                    if key in subobj and subobj[key]:
                        return subobj[key]
    return None

def _normalize_row(row: dict):
    # existing code you had to parse explain_json etc...
    r = dict(row)

    # parse JSON text columns -> same as before
    json_map = {
        "explain_json": "explain",
        "explain_shap_json": "explain_shap",
        "raw_json": "raw",
        "normalized_json": "normalized",
        "enriched_json": "enriched",
    }
    for col, target in json_map.items():
        if col in r:
            val = r.pop(col)
            if val is None:
                r[target] = None
            elif isinstance(val, (dict, list)):
                r[target] = val
            else:
                try:
                    r[target] = json.loads(val)
                except Exception:
                    r[target] = val

    # If there is a raw/normalized/enriched json, try to pick an IP from it
    ip = None
    for candidate_field in ("raw", "normalized", "enriched"):
        candidate = r.get(candidate_field)
        if isinstance(candidate, dict):
            ip = _extract_ip_from_event(candidate)
            if ip:
                break

    # Prefer IP if found, otherwise fallback to DB 'source' column (region)
    if ip:
        r["source"] = ip
    else:
        # normalize the existing source to string (it may be bytes/None)
        r["source"] = _serialize_value(r.get("source"))

    # convert other columns for JSON safety (dates -> strings, decimals -> floats)
    for k, v in list(r.items()):
        r[k] = _serialize_value(v)

    return r


'''def _normalize_row(row: dict):
    """
    Normalize a single DB row:
      - rename json columns (explain_json -> explain)
      - parse JSON text into dicts when possible
      - convert datetime/Decimal -> str/float
      - ensure frontend expected keys exist
    """
    json_map = {
        "explain_json": "explain",
        "explain_shap_json": "explain_shap",
        "raw_json": "raw",
        "normalized_json": "normalized",
        "enriched_json": "enriched",
    }

    r = dict(row)  # copy

    # convert known json columns to expected names
    for col, target in json_map.items():
        if col in r:
            val = r.pop(col)
            if val is None:
                r[target] = None
            elif isinstance(val, (dict, list)):
                r[target] = val
            else:
                try:
                    r[target] = json.loads(val)
                except Exception:
                    r[target] = val

    # also support older column names if present
    if "explain" in r and "explain" not in r:
        pass

    # convert all other fields to JSON-safe
    for k, v in list(r.items()):
        r[k] = _serialize_value(v)

    # ensure keys frontend expects are present (avoid undefined)
    for expected in ("identifier_type", "severity", "detection_score", "ti_score", "correlation_score", "alert_ts"):
        if expected not in r:
            r[expected] = None

    return r '''


def get_alerts(limit: int = 200):
    """
    Return latest alerts. Try 'alerts' table first (newer schema), fallback to 'events'.
    Returns JSON-serializable list of dicts. If DB connection fails, returns [] (and logs).
    """
    conn = None
    cur = None
    try:
        conn = get_conn()
    except Exception as e:
        log.exception("DB connection failed in get_alerts: %s", e)
        return []  # frontend won't get 500 — it sees empty list

    try:
        cur = conn.cursor(dictionary=True)

        # try alerts (newer schema)
        try:
            cur.execute(
                """
                SELECT id, event_id, entity_id, entity_type, event_type, source,
                       detection_score, ti_score, correlation_score, label, alert_ts,
                       explain_json, explain_shap_json, raw_json, normalized_json,
                       identifier_type, severity
                FROM alerts
                ORDER BY alert_ts DESC, id DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cur.fetchall()
            if rows:
                return [_normalize_row(r) for r in rows]
        except Exception as e:
            log.debug("alerts select failed or alerts empty: %s", e)

        # fallback to events table (older schema)
        try:
            cur.execute(
                """
                SELECT id, event_id, entity_id, entity_type, event_type, source,
                       detection_score, ti_score, correlation_score, label, alert_ts,
                       raw_json, normalized_json, enriched_json, identifier_type, severity, updated_ts
                FROM events
                ORDER BY updated_ts DESC, id DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cur.fetchall()
            return [_normalize_row(r) for r in rows]
        except Exception as e:
            log.exception("events select failed: %s", e)
            return []
    finally:
        try:
            if cur:
                cur.close()
        except Exception:
            pass
        try:
            if conn:
                conn.close()
        except Exception:
            pass

# services/consumer/mysql_db.py  <- add these functions near the bottom

import logging
from datetime import datetime, timedelta

log = logging.getLogger("consumer.mysql_db")

def _safe_execute_scalar(conn, sql, params=()):
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        r = cur.fetchone()
        return r[0] if r and len(r) > 0 else None
    finally:
        cur.close()

def get_recent_counts(window_minutes=60):
    """
    Return quick counts:
      - events in last window_minutes
      - avg detection score in last window_minutes
      - last event timestamp
      - alerts counts by severity
    """
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor(dictionary=True)

        # last event time
        cur.execute("SELECT MAX(ingest_ts) as last_event FROM events")
        last_event_row = cur.fetchone()
        last_event = last_event_row.get("last_event") if last_event_row else None

        # events in window
        cur.execute(
            "SELECT COUNT(*) as ev_count FROM events WHERE ingest_ts >= NOW() - INTERVAL %s MINUTE",
            (window_minutes,),
        )
        ev_count = cur.fetchone()[0] if cur.rowcount >= 0 else 0

        # avg detection score in window
        cur.execute(
            "SELECT AVG(detection_score) as avg_score FROM events WHERE ingest_ts >= NOW() - INTERVAL %s MINUTE",
            (window_minutes,),
        )
        avg_row = cur.fetchone()
        avg_score = float(avg_row[0]) if avg_row and avg_row[0] is not None else 0.0

        # alerts by severity
        cur.execute("SELECT severity, COUNT(*) as c FROM alerts GROUP BY severity")
        sev_rows = cur.fetchall()
        alerts_by_sev = {}
        for r in sev_rows:
            # where cursor returns tuple (severity, count) or dict depending on cursor setup
            if isinstance(r, dict):
                alerts_by_sev[r.get("severity") or "unknown"] = int(r.get("c", 0))
            else:
                alerts_by_sev[r[0] or "unknown"] = int(r[1])

        # total alerts
        cur.execute("SELECT COUNT(*) FROM alerts")
        total_alerts = cur.fetchone()[0] if cur.rowcount >= 0 else 0

        cur.close()
        conn.close()

        return {
            "last_event_ts": last_event,
            "events_last_window": int(ev_count),
            "avg_detection_score": float(avg_score),
            "alerts_by_severity": alerts_by_sev,
            "alerts_total": int(total_alerts),
        }
    except Exception as e:
        log.exception("get_recent_counts failed: %s", e)
        try:
            if cur:
                cur.close()
            if conn:
                conn.close()
        except Exception:
            pass
        return {
            "last_event_ts": None,
            "events_last_window": 0,
            "avg_detection_score": 0.0,
            "alerts_by_severity": {},
            "alerts_total": 0,
        }
