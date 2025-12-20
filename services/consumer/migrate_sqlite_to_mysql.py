# migrate_sqlite_to_mysql.py
import sqlite3, json
from mysql_db import insert_or_update_event, ensure_db_schema

ensure_db_schema()
SQLITE_DB = "incidents.db"  # default sqlite DB used in consumer
conn = sqlite3.connect(SQLITE_DB)
c = conn.cursor()
c.execute("SELECT id, entity_id, score, event_json, ts FROM alerts")
rows = c.fetchall()
for r in rows:
    id_, entity_id, score, event_json, ts = r
    try:
        ev = json.loads(event_json)
    except:
        ev = {}
    rec = {
        "id": id_,
        "event_id": ev.get("event_id") or id_,
        "source": ev.get("source") or "migrated",
        "entity_type": ev.get("entity_type") or "user",
        "entity_id": entity_id,
        "event_type": ev.get("event_type") or None,
        "raw": ev.get("raw", {}),
        "normalized": ev,
        "enriched": ev.get("ti", {}),
        "template_id": ev.get("template_id"),
        "ti_score": ev.get("ti", {}).get("ip_reputation"),
        "detection_score": float(score) if score is not None else None,
        "label": "problem" if score and float(score) > 0.7 else "normal",
        "detected": True if score and float(score) > 0.7 else False,
        "model_version": "migrated",
        "alert_ts": ts
    }
    insert_or_update_event(rec)
print("Migration complete.")
