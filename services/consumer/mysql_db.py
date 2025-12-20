# services/consumer/mysql_db.py
'''import os
import json
import logging
import mysql.connector
from mysql.connector import errorcode
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger("consumer.mysql_db")
log.setLevel(logging.DEBUG)

# environment-driven DB config (fall back to common names)
MYSQL_HOST = os.getenv("MYSQL_HOST") or os.getenv("DB_HOST", "localhost")
MYSQL_USER = os.getenv("MYSQL_USER") or os.getenv("DB_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASS") or os.getenv("DB_PASS", "")
MYSQL_DB = os.getenv("MYSQL_DB") or os.getenv("DB_NAME", "threatsys")
MYSQL_PORT = int(os.getenv("MYSQL_PORT") or os.getenv("DB_PORT", 3306))
MODEL_PATH = os.getenv("MODEL_PATH", "./services/ml/models/iforest_v1.pkl")

def get_conn():
    """Return a new mysql.connector connection using configured env vars."""
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB,
            port=MYSQL_PORT,
            autocommit=True,
        )
        return conn
    except Exception as e:
        log.exception("get_conn failed connecting to %s@%s:%s/%s: %s", MYSQL_USER, MYSQL_HOST, MYSQL_PORT, MYSQL_DB, e)
        raise

def _get_admin_conn():
    """Connection without selecting database (used for create DB)."""
    return mysql.connector.connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, port=MYSQL_PORT, autocommit=True)

def ensure_db_schema():
    """
    Ensure DB + tables exist and add columns if missing.
    Safe to call on startup.
    """
    try:
        admin_conn = _get_admin_conn()
        cur = admin_conn.cursor()
        # create DB if not exists
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DB}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        admin_conn.database = MYSQL_DB
        cur.close()
        admin_conn.close()
    except Exception as e:
        log.exception("Failed creating database %s: %s", MYSQL_DB, e)
        # continue, maybe DB already exists or user lacks privilege

    conn = get_conn()
    cur = conn.cursor()

    # create events table (idempotent)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
      id VARCHAR(128) PRIMARY KEY,
      ingest_ts DATETIME DEFAULT CURRENT_TIMESTAMP,
      event_id VARCHAR(128),
      source VARCHAR(128),
      entity_type VARCHAR(64),
      entity_id VARCHAR(256),
      event_type VARCHAR(128),
      raw_json LONGTEXT,
      normalized_json LONGTEXT,
      enriched_json LONGTEXT,
      template_id VARCHAR(128),
      ti_score DOUBLE,
      detection_score DOUBLE,
      correlation_score DOUBLE DEFAULT 0.0,
      identifier_type VARCHAR(128),
      severity VARCHAR(16),
      label ENUM('normal','problem') DEFAULT 'normal',
      detected BOOLEAN DEFAULT FALSE,
      model_version VARCHAR(64),
      alert_ts DATETIME NULL,
      feedback VARCHAR(512),
      updated_ts DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      INDEX idx_entity (entity_id),
      INDEX idx_event_type (event_type),
      INDEX idx_label (label)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    # create alerts table (idempotent)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
      id BIGINT NOT NULL AUTO_INCREMENT,
      event_id VARCHAR(128),
      entity_id VARCHAR(256),
      entity_type VARCHAR(64),
      event_type VARCHAR(128),
      source VARCHAR(128),
      detection_score DOUBLE,
      ti_score DOUBLE,
      correlation_score DOUBLE,
      label ENUM('normal','problem') DEFAULT 'problem',
      alert_ts DATETIME DEFAULT CURRENT_TIMESTAMP,
      explain_json LONGTEXT,
      explain_shap_json LONGTEXT,
      raw_json LONGTEXT,
      normalized_json LONGTEXT,
      identifier_type VARCHAR(128),
      severity VARCHAR(16),
      PRIMARY KEY (id),
      INDEX idx_event_id (event_id),
      INDEX idx_entity_id (entity_id),
      INDEX idx_label_alerts (label)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    # ensure columns exist - safe to run even if they already exist
    def _safe_alter(col_sql):
        try:
            cur.execute("ALTER TABLE events ADD COLUMN " + col_sql)
        except Exception:
            pass

    # ensure some common columns (idempotent)
    _safe_alter("correlation_score DOUBLE DEFAULT 0.0")
    _safe_alter("identifier_type VARCHAR(128)")
    _safe_alter("severity VARCHAR(16)")
    _safe_alter("source VARCHAR(128)")
    _safe_alter("entity_id VARCHAR(256)")

    cur.close()
    conn.close()
    log.info("ensure_db_schema done (DB=%s host=%s)", MYSQL_DB, MYSQL_HOST)

def insert_or_update_event(record: dict):
    """
    Insert or update into events table. This function will write identifier_type and severity too.
    """
    sql = """
    INSERT INTO events (
      id, event_id, source, entity_type, entity_id, event_type,
      raw_json, normalized_json, enriched_json, template_id,
      ti_score, detection_score, correlation_score,
      identifier_type, severity,
      label, detected, model_version, alert_ts
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    ON DUPLICATE KEY UPDATE
      raw_json=VALUES(raw_json),
      normalized_json=VALUES(normalized_json),
      enriched_json=VALUES(enriched_json),
      template_id=VALUES(template_id),
      ti_score=VALUES(ti_score),
      detection_score=VALUES(detection_score),
      correlation_score=VALUES(correlation_score),
      identifier_type=VALUES(identifier_type),
      severity=VALUES(severity),
      label=VALUES(label),
      detected=VALUES(detected),
      model_version=VALUES(model_version),
      alert_ts=VALUES(alert_ts),
      updated_ts = CURRENT_TIMESTAMP;
    """
    params = (
        record.get("id"),
        record.get("event_id"),
        record.get("source"),
        record.get("entity_type"),
        record.get("entity_id"),
        record.get("event_type"),
        json.dumps(record.get("raw") or {}),
        json.dumps(record.get("normalized") or {}),
        json.dumps(record.get("enriched") or {}),
        record.get("template_id"),
        record.get("ti_score"),
        record.get("detection_score"),
        record.get("correlation_score") if record.get("correlation_score") is not None else 0.0,
        record.get("identifier_type"),
        record.get("severity"),
        record.get("label", "normal"),
        bool(record.get("detected", False)),
        record.get("model_version"),
        record.get("alert_ts"),
    )
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, params)
    cur.close()
    conn.close()

def insert_alert_from_rec(record: dict, explain: dict | None = None, explain_shap: dict | None = None):
    sql = """
    INSERT INTO alerts (
      event_id, entity_id, entity_type, event_type, source,
      detection_score, ti_score, correlation_score, label, alert_ts,
      explain_json, explain_shap_json, raw_json, normalized_json,
      identifier_type, severity
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """
    params = (
        record.get("event_id"),
        record.get("entity_id"),
        record.get("entity_type"),
        record.get("event_type"),
        record.get("source"),
        record.get("detection_score"),
        record.get("ti_score"),
        record.get("correlation_score"),
        record.get("label"),
        record.get("alert_ts"),
        json.dumps(explain or {}),
        json.dumps(explain_shap or {}),
        json.dumps(record.get("raw") or {}),
        json.dumps(record.get("normalized") or {}),
        record.get("identifier_type"),
        record.get("severity"),
    )
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(sql, params)
    cur.close()
    conn.close()


def fetch_some_alerts(limit: int = 10):
    """Helper used for debugging: returns raw alerts rows (no JSON parsing)."""
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id, event_id, entity_id, identifier_type, severity, detection_score, alert_ts FROM alerts ORDER BY alert_ts DESC LIMIT %s", (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


# add this to services/consumer/mysql_db.py

from datetime import datetime, timedelta
from typing import Dict

def get_recent_counts(hours: int = 1) -> Dict:
    """
    Return a dictionary of recent counts/metrics for the last `hours`.
    Used by the /system-health endpoint.
    Keys returned:
      - last_event_ts: ISO string of most recent event.alert_ts or ingest_ts
      - events_last_hour: count of events in last `hours`
      - avg_detection_score_last_hour: average detection_score over last `hours`
      - alerts_total: total rows in alerts table
      - alerts_by_severity: {low, medium, high} counts from alerts table
      - last_hour_window_hours: the hours argument passed back for clarity
    """
    conn = None
    cur = None
    try:
        conn = get_conn()
        cur = conn.cursor(dictionary=True)

        # most recent event timestamp (prefer alert_ts then ingest_ts/updated_ts)
        cur.execute(
            "SELECT MAX(COALESCE(alert_ts, updated_ts, ingest_ts)) as last_ts FROM events"
        )
        row = cur.fetchone()
        last_ts = row.get("last_ts") if row else None
        last_ts_str = last_ts.isoformat(sep=" ") if last_ts else None

        # compute timeframe
        since = datetime.utcnow() - timedelta(hours=hours)
        since_str = since.strftime("%Y-%m-%d %H:%M:%S")

        # events in timeframe
        cur.execute(
            "SELECT COUNT(1) as cnt, AVG(IFNULL(detection_score,0)) as avg_score FROM events WHERE COALESCE(alert_ts, updated_ts, ingest_ts) >= %s",
            (since_str,),
        )
        r = cur.fetchone() or {}
        events_last_hour = int(r.get("cnt") or 0)
        avg_score = float(r.get("avg_score") or 0.0)

        # total alerts and by severity (from alerts table if exists, else derive from events)
        try:
            cur.execute("SELECT COUNT(1) as cnt FROM alerts")
            alerts_total = int(cur.fetchone().get("cnt") or 0)
            cur.execute(
                "SELECT severity, COUNT(1) as cnt FROM alerts GROUP BY severity"
            )
            rows = cur.fetchall() or []
            alerts_by_sev = {r.get("severity") or "unknown": int(r.get("cnt") or 0) for r in rows}
        except Exception:
            # fallback to events table
            cur.execute("SELECT COUNT(1) as cnt FROM events WHERE label='problem'")
            alerts_total = int(cur.fetchone().get("cnt") or 0)
            cur.execute("SELECT severity, COUNT(1) as cnt FROM events WHERE label='problem' GROUP BY severity")
            rows = cur.fetchall() or []
            alerts_by_sev = {r.get("severity") or "unknown": int(r.get("cnt") or 0) for r in rows}

        return {
            "last_event_ts": last_ts_str,
            "events_last_hour": events_last_hour,
            "avg_detection_score_last_hour": round(avg_score, 6),
            "alerts_total": alerts_total,
            "alerts_by_severity": alerts_by_sev,
            "last_hour_window_hours": hours,
        }
    except Exception as e:
        # be quiet but useful for debugging
        try:
            if cur:
                cur.close()
            if conn:
                conn.close()
        except Exception:
            pass
        raise
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
'''
'''
# services/consumer/mysql_db.py
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

import mysql.connector
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger("consumer.mysql_db")
log.setLevel(logging.DEBUG)
# configure a simple handler if not configured by app
if not log.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    ch.setFormatter(formatter)
    log.addHandler(ch)

# environment-driven DB config (fall back to common names)
MYSQL_HOST = os.getenv("MYSQL_HOST") or os.getenv("DB_HOST", "localhost")
MYSQL_USER = os.getenv("MYSQL_USER") or os.getenv("DB_USER", "threatuser")
MYSQL_PASSWORD = os.getenv("MYSQL_PASS") or os.getenv("DB_PASS", "")
MYSQL_DB = os.getenv("MYSQL_DB") or os.getenv("DB_NAME", "threatsys")
MYSQL_PORT = int(os.getenv("MYSQL_PORT") or os.getenv("DB_PORT", 3306))
MODEL_PATH = os.getenv("MODEL_PATH", "./services/ml/models/iforest_v1.pkl")

def get_conn():
    """Return a new mysql.connector connection using configured env vars."""
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB,
            port=MYSQL_PORT,
            autocommit=True,
        )
        return conn
    except Exception as e:
        log.exception("get_conn failed connecting to %s@%s:%s/%s: %s", MYSQL_USER, MYSQL_HOST, MYSQL_PORT, MYSQL_DB, e)
        raise

def _get_admin_conn():
    """Connection without selecting database (used for create DB)."""
    return mysql.connector.connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, port=MYSQL_PORT, autocommit=True)

def ensure_db_schema():
    """
    Ensure DB + tables exist and add columns if missing.
    Safe to call on startup.
    """
    try:
        admin_conn = _get_admin_conn()
        cur = admin_conn.cursor()
        # create DB if not exists
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DB}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        admin_conn.database = MYSQL_DB
        cur.close()
        admin_conn.close()
    except Exception as e:
        log.exception("Failed creating database %s: %s", MYSQL_DB, e)
        # continue, maybe DB already exists or user lacks privilege

    conn = get_conn()
    cur = conn.cursor()

    # create events table (idempotent)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
      id VARCHAR(128) PRIMARY KEY,
      ingest_ts DATETIME DEFAULT CURRENT_TIMESTAMP,
      event_id VARCHAR(128),
      source VARCHAR(128),
      entity_type VARCHAR(64),
      entity_id VARCHAR(256),
      event_type VARCHAR(128),
      raw_json LONGTEXT,
      normalized_json LONGTEXT,
      enriched_json LONGTEXT,
      template_id VARCHAR(128),
      ti_score DOUBLE,
      detection_score DOUBLE,
      correlation_score DOUBLE DEFAULT 0.0,
      identifier_type VARCHAR(128),
      severity VARCHAR(16),
      label ENUM('normal','problem') DEFAULT 'normal',
      detected BOOLEAN DEFAULT FALSE,
      model_version VARCHAR(64),
      alert_ts DATETIME NULL,
      feedback VARCHAR(512),
      updated_ts DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      INDEX idx_entity (entity_id),
      INDEX idx_event_type (event_type),
      INDEX idx_label (label)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    # create alerts table (idempotent)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
      id BIGINT NOT NULL AUTO_INCREMENT,
      event_id VARCHAR(128),
      entity_id VARCHAR(256),
      entity_type VARCHAR(64),
      event_type VARCHAR(128),
      source VARCHAR(128),
      detection_score DOUBLE,
      ti_score DOUBLE,
      correlation_score DOUBLE,
      label ENUM('normal','problem') DEFAULT 'problem',
      alert_ts DATETIME DEFAULT CURRENT_TIMESTAMP,
      explain_json LONGTEXT,
      explain_shap_json LONGTEXT,
      raw_json LONGTEXT,
      normalized_json LONGTEXT,
      identifier_type VARCHAR(128),
      severity VARCHAR(16),
      PRIMARY KEY (id),
      INDEX idx_event_id (event_id),
      INDEX idx_entity_id (entity_id),
      INDEX idx_label_alerts (label)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    # ensure columns exist - safe to run even if they already exist
    def _safe_alter(col_sql):
        try:
            cur.execute("ALTER TABLE events ADD COLUMN " + col_sql)
        except Exception:
            pass

    _safe_alter("correlation_score DOUBLE DEFAULT 0.0")
    _safe_alter("identifier_type VARCHAR(128)")
    _safe_alter("severity VARCHAR(16)")
    _safe_alter("source VARCHAR(128)")
    _safe_alter("entity_id VARCHAR(256)")

    cur.close()
    conn.close()
    log.info("ensure_db_schema done (DB=%s host=%s)", MYSQL_DB, MYSQL_HOST)

def insert_or_update_event(record: dict):
    """
    Insert or update into events table. This function will write identifier_type and severity too.
    Defensive: verify placeholder count and log params when mismatched.
    """
    sql = """
    INSERT INTO events (
      id, event_id, source, entity_type, entity_id, event_type,
      raw_json, normalized_json, enriched_json, template_id,
      ti_score, detection_score, correlation_score,
      identifier_type, severity,
      label, detected, model_version, alert_ts
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    ON DUPLICATE KEY UPDATE
      raw_json=VALUES(raw_json),
      normalized_json=VALUES(normalized_json),
      enriched_json=VALUES(enriched_json),
      template_id=VALUES(template_id),
      ti_score=VALUES(ti_score),
      detection_score=VALUES(detection_score),
      correlation_score=VALUES(correlation_score),
      identifier_type=VALUES(identifier_type),
      severity=VALUES(severity),
      label=VALUES(label),
      detected=VALUES(detected),
      model_version=VALUES(model_version),
      alert_ts=VALUES(alert_ts),
      updated_ts = CURRENT_TIMESTAMP;
    """
    params = (
        record.get("id"),
        record.get("event_id"),
        record.get("source"),
        record.get("entity_type"),
        record.get("entity_id"),
        record.get("event_type"),
        json.dumps(record.get("raw") or {}),
        json.dumps(record.get("normalized") or {}),
        json.dumps(record.get("enriched") or {}),
        record.get("template_id"),
        record.get("ti_score"),
        record.get("detection_score"),
        record.get("correlation_score") if record.get("correlation_score") is not None else 0.0,
        record.get("identifier_type"),
        record.get("severity"),
        record.get("label", "normal"),
        bool(record.get("detected", False)),
        record.get("model_version"),
        record.get("alert_ts"),
    )

    placeholder_count = sql.count("%s")
    if placeholder_count != len(params):
        log.error("SQL placeholder count mismatch in insert_or_update_event: placeholders=%s params=%s", placeholder_count, len(params))
        log.error("SQL: %s", sql)
        log.error("PARAMS: %s", params)
        raise ValueError(f"SQL placeholders ({placeholder_count}) != params ({len(params)})")

    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
    except Exception:
        log.exception("insert_or_update_event failed executing SQL. params=%s", params)
        raise
    finally:
        try: cur.close()
        except Exception: pass
        try: conn.close()
        except Exception: pass

def insert_alert_from_rec(record: dict, explain: dict | None = None, explain_shap: dict | None = None):
    sql = """
    INSERT INTO alerts (
      event_id, entity_id, entity_type, event_type, source,
      detection_score, ti_score, correlation_score, label, alert_ts,
      explain_json, explain_shap_json, raw_json, normalized_json,
      identifier_type, severity
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """
    params = (
        record.get("event_id"),
        record.get("entity_id"),
        record.get("entity_type"),
        record.get("event_type"),
        record.get("source"),
        record.get("detection_score"),
        record.get("ti_score"),
        record.get("correlation_score"),
        record.get("label"),
        record.get("alert_ts"),
        json.dumps(explain or {}),
        json.dumps(explain_shap or {}),
        json.dumps(record.get("raw") or {}),
        json.dumps(record.get("normalized") or {}),
        record.get("identifier_type"),
        record.get("severity"),
    )

    placeholder_count = sql.count("%s")
    if placeholder_count != len(params):
        log.error("insert_alert_from_rec placeholder mismatch: %s vs %s", placeholder_count, len(params))
        log.error("SQL: %s", sql)
        log.error("PARAMS: %s", params)
        raise ValueError("SQL placeholders != params length")

    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
    except Exception:
        log.exception("insert_alert_from_rec failed. params=%s", params)
        raise
    finally:
        try: cur.close()
        except Exception: pass
        try: conn.close()
        except Exception: pass

def fetch_some_alerts(limit: int = 10):
    """Helper used for debugging: returns raw alerts rows (no JSON parsing)."""
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id, event_id, entity_id, identifier_type, severity, detection_score, alert_ts FROM alerts ORDER BY alert_ts DESC LIMIT %s", (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

# services/consumer/mysql_db.py
from datetime import datetime, timedelta
from typing import Dict, Any
import os
import logging

log = logging.getLogger("consumer.mysql_db")

def get_recent_counts(window_minutes: int = 60) -> Dict[str, Any]:
    """
    Return metrics for system-health:
      {
        "alerts_total": int | None,
        "alerts_by_severity": {str: int},
        "events_last_window": int | None,
        "avg_detection_score_last_window": float,
        "last_event_ts": "YYYY-MM-DD HH:MM:SS" | None
      }

    Safe to call even if alerts/events tables are missing.
    """
    try:
        conn = get_conn()
        cur = conn.cursor(dictionary=True)

        # compute timestring for window
        now = datetime.utcnow()
        since_dt = now - timedelta(minutes=window_minutes)
        # MySQL expects local-format string 'YYYY-MM-DD HH:MM:SS'
        since_str = since_dt.strftime("%Y-%m-%d %H:%M:%S")

        # 1) last event timestamp (prefer alert_ts then updated_ts/ingest_ts)
        try:
            cur.execute("SELECT MAX(COALESCE(alert_ts, updated_ts, ingest_ts)) AS last_ts FROM events")
            row = cur.fetchone()
            last_ts = row.get("last_ts") if row else None
            last_ts_str = last_ts.strftime("%Y-%m-%d %H:%M:%S") if last_ts else None
        except Exception as e:
            log.debug("couldn't get last event ts: %s", e)
            last_ts_str = None

        # 2) events in window and avg detection score
        events_last_window = None
        avg_score = 0.0
        try:
            cur.execute(
                "SELECT COUNT(1) AS cnt, AVG(COALESCE(detection_score,0)) AS avg_score FROM events "
                "WHERE COALESCE(alert_ts, updated_ts, ingest_ts) >= %s",
                (since_str,),
            )
            r = cur.fetchone() or {}
            events_last_window = int(r.get("cnt") or 0)
            avg_score = float(r.get("avg_score") or 0.0)
        except Exception as e:
            log.debug("couldn't compute events window/avg: %s", e)
            events_last_window = None
            avg_score = 0.0

        # 3) alerts total and by severity (prefer alerts table; fallback to events labeled 'problem')
        alerts_total = None
        alerts_by_severity = {}
        try:
            cur.execute("SELECT COUNT(1) AS cnt FROM alerts")
            alerts_total = int(cur.fetchone().get("cnt") or 0)
            cur.execute("SELECT IFNULL(severity,'unknown') AS severity, COUNT(1) AS cnt FROM alerts GROUP BY severity")
            rows = cur.fetchall() or []
            alerts_by_severity = {r.get("severity") or "unknown": int(r.get("cnt") or 0) for r in rows}
        except Exception:
            # fallback to events labelled 'problem', if alerts table missing
            try:
                cur.execute("SELECT COUNT(1) AS cnt FROM events WHERE label='problem'")
                alerts_total = int(cur.fetchone().get("cnt") or 0)
                cur.execute("SELECT IFNULL(severity,'unknown') AS severity, COUNT(1) AS cnt FROM events WHERE label='problem' GROUP BY severity")
                rows = cur.fetchall() or []
                alerts_by_severity = {r.get("severity") or "unknown": int(r.get("cnt") or 0) for r in rows}
            except Exception as e:
                log.debug("couldn't compute alerts: %s", e)
                alerts_total = None
                alerts_by_severity = {}

        cur.close()
        conn.close()

        return {
            "alerts_total": alerts_total,
            "alerts_by_severity": alerts_by_severity,
            "events_last_window": events_last_window,
            "avg_detection_score_last_window": round(avg_score, 6),
            "last_event_ts": last_ts_str,
            "window_minutes": window_minutes,
        }
    except Exception as e:
        log.exception("get_recent_counts failed: %s", e)
        # return safe defaults
        return {
            "alerts_total": None,
            "alerts_by_severity": {},
            "events_last_window": None,
            "avg_detection_score_last_window": 0.0,
            "last_event_ts": None,
            "window_minutes": window_minutes,
            "error": str(e),
        }
'''


# services/consumer/mysql_db.py
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

import mysql.connector
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger("consumer.mysql_db")
log.setLevel(logging.DEBUG)
if not log.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    ch.setFormatter(formatter)
    log.addHandler(ch)

# environment-driven DB config (fallbacks included)
MYSQL_HOST = os.getenv("MYSQL_HOST") or os.getenv("DB_HOST", "localhost")
MYSQL_USER = os.getenv("MYSQL_USER") or os.getenv("DB_USER", "threatuser")
MYSQL_PASSWORD = os.getenv("MYSQL_PASS") or os.getenv("DB_PASS", "")
MYSQL_DB = os.getenv("MYSQL_DB") or os.getenv("DB_NAME", "threatsys")
MYSQL_PORT = int(os.getenv("MYSQL_PORT") or os.getenv("DB_PORT", 3306))
MODEL_PATH = os.getenv("MODEL_PATH", "./services/ml/models/iforest_v1.pkl")


def get_conn():
    """Return a new mysql.connector connection using configured env vars."""
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB,
            port=MYSQL_PORT,
            autocommit=True,
        )
        return conn
    except Exception as e:
        log.exception("get_conn failed connecting to %s@%s:%s/%s: %s", MYSQL_USER, MYSQL_HOST, MYSQL_PORT, MYSQL_DB, e)
        raise


def _get_admin_conn():
    """Connection without selecting database (used for create DB)."""
    return mysql.connector.connect(host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, port=MYSQL_PORT, autocommit=True)


def ensure_db_schema():
    """
    Ensure DB + tables exist and add columns if missing.
    Safe to call on startup.
    """
    try:
        admin_conn = _get_admin_conn()
        cur = admin_conn.cursor()
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DB}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        admin_conn.database = MYSQL_DB
        cur.close()
        admin_conn.close()
    except Exception as e:
        log.exception("Failed creating database %s: %s", MYSQL_DB, e)

    conn = get_conn()
    cur = conn.cursor()
    # events table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
      id VARCHAR(128) PRIMARY KEY,
      ingest_ts DATETIME DEFAULT CURRENT_TIMESTAMP,
      event_id VARCHAR(128),
      source VARCHAR(128),
      entity_type VARCHAR(64),
      entity_id VARCHAR(256),
      event_type VARCHAR(128),
      raw_json LONGTEXT,
      normalized_json LONGTEXT,
      enriched_json LONGTEXT,
      template_id VARCHAR(128),
      ti_score DOUBLE,
      detection_score DOUBLE,
      correlation_score DOUBLE DEFAULT 0.0,
      identifier_type VARCHAR(128),
      severity VARCHAR(16),
      label ENUM('normal','problem') DEFAULT 'normal',
      detected BOOLEAN DEFAULT FALSE,
      model_version VARCHAR(64),
      alert_ts DATETIME NULL,
      feedback VARCHAR(512),
      updated_ts DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      INDEX idx_entity (entity_id),
      INDEX idx_event_type (event_type),
      INDEX idx_label (label)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)
    # alerts table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
      id BIGINT NOT NULL AUTO_INCREMENT,
      event_id VARCHAR(128),
      entity_id VARCHAR(256),
      entity_type VARCHAR(64),
      event_type VARCHAR(128),
      source VARCHAR(128),
      detection_score DOUBLE,
      ti_score DOUBLE,
      correlation_score DOUBLE,
      label ENUM('normal','problem') DEFAULT 'problem',
      alert_ts DATETIME DEFAULT CURRENT_TIMESTAMP,
      explain_json LONGTEXT,
      explain_shap_json LONGTEXT,
      raw_json LONGTEXT,
      normalized_json LONGTEXT,
      identifier_type VARCHAR(128),
      severity VARCHAR(16),
      PRIMARY KEY (id),
      INDEX idx_event_id (event_id),
      INDEX idx_entity_id (entity_id),
      INDEX idx_label_alerts (label)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    def _safe_alter(col_sql):
        try:
            cur.execute("ALTER TABLE events ADD COLUMN " + col_sql)
        except Exception:
            pass

    _safe_alter("correlation_score DOUBLE DEFAULT 0.0")
    _safe_alter("identifier_type VARCHAR(128)")
    _safe_alter("severity VARCHAR(16)")
    _safe_alter("source VARCHAR(128)")
    _safe_alter("entity_id VARCHAR(256)")

    cur.close()
    conn.close()
    log.info("ensure_db_schema done (DB=%s host=%s)", MYSQL_DB, MYSQL_HOST)


def insert_or_update_event(record: dict):
    """
    Insert or update into events table.
    Defensive: validate placeholder count to avoid the 'Not all parameters were used' error.
    """
    sql = """
    INSERT INTO events (
      id, event_id, source, entity_type, entity_id, event_type,
      raw_json, normalized_json, enriched_json, template_id,
      ti_score, detection_score, correlation_score,
      identifier_type, severity,
      label, detected, model_version, alert_ts
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    ON DUPLICATE KEY UPDATE
      raw_json=VALUES(raw_json),
      normalized_json=VALUES(normalized_json),
      enriched_json=VALUES(enriched_json),
      template_id=VALUES(template_id),
      ti_score=VALUES(ti_score),
      detection_score=VALUES(detection_score),
      correlation_score=VALUES(correlation_score),
      identifier_type=VALUES(identifier_type),
      severity=VALUES(severity),
      label=VALUES(label),
      detected=VALUES(detected),
      model_version=VALUES(model_version),
      alert_ts=VALUES(alert_ts),
      updated_ts = CURRENT_TIMESTAMP;
    """
    params = (
        record.get("id"),
        record.get("event_id"),
        record.get("source"),
        record.get("entity_type"),
        record.get("entity_id"),
        record.get("event_type"),
        json.dumps(record.get("raw") or {}),
        json.dumps(record.get("normalized") or {}),
        json.dumps(record.get("enriched") or {}),
        record.get("template_id"),
        record.get("ti_score"),
        record.get("detection_score"),
        record.get("correlation_score") if record.get("correlation_score") is not None else 0.0,
        record.get("identifier_type"),
        record.get("severity"),
        record.get("label", "normal"),
        bool(record.get("detected", False)),
        record.get("model_version"),
        record.get("alert_ts"),
    )

    placeholder_count = sql.count("%s")
    if placeholder_count != len(params):
        log.error("SQL placeholder count mismatch in insert_or_update_event: placeholders=%s params=%s", placeholder_count, len(params))
        log.error("SQL: %s", sql)
        log.error("PARAMS: %s", params)
        raise ValueError(f"SQL placeholders ({placeholder_count}) != params ({len(params)})")

    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
    except Exception:
        log.exception("insert_or_update_event failed executing SQL. params=%s", params)
        raise
    finally:
        try: cur.close()
        except Exception: pass
        try: conn.close()
        except Exception: pass


def insert_alert_from_rec(record: dict, explain: dict | None = None, explain_shap: dict | None = None):
    sql = """
    INSERT INTO alerts (
      event_id, entity_id, entity_type, event_type, source,
      detection_score, ti_score, correlation_score, label, alert_ts,
      explain_json, explain_shap_json, raw_json, normalized_json,
      identifier_type, severity
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """
    params = (
        record.get("event_id"),
        record.get("entity_id"),
        record.get("entity_type"),
        record.get("event_type"),
        record.get("source"),
        record.get("detection_score"),
        record.get("ti_score"),
        record.get("correlation_score"),
        record.get("label"),
        record.get("alert_ts"),
        json.dumps(explain or {}),
        json.dumps(explain_shap or {}),
        json.dumps(record.get("raw") or {}),
        json.dumps(record.get("normalized") or {}),
        record.get("identifier_type"),
        record.get("severity"),
    )

    placeholder_count = sql.count("%s")
    if placeholder_count != len(params):
        log.error("insert_alert_from_rec placeholder mismatch: %s vs %s", placeholder_count, len(params))
        log.error("SQL: %s", sql)
        log.error("PARAMS: %s", params)
        raise ValueError("SQL placeholders != params length")

    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
    except Exception:
        log.exception("insert_alert_from_rec failed. params=%s", params)
        raise
    finally:
        try: cur.close()
        except Exception: pass
        try: conn.close()
        except Exception: pass


def fetch_some_alerts(limit: int = 10):
    """Helper used for debugging: returns recent alerts rows (dictionary)."""
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id, event_id, entity_id, identifier_type, severity, detection_score, alert_ts FROM alerts ORDER BY alert_ts DESC LIMIT %s", (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

# services/consumer/mysql_db.py  (replace existing get_recent_counts)
from datetime import datetime, timedelta
from typing import Dict, Any

def get_recent_counts(window_minutes: int = 60) -> Dict[str, Any]:
    """
    Return metrics for system-health and be compatible with multiple callers.
    Returns keys:
      - alerts_total
      - alerts_by_severity (dict)
      - events_last_window
      - avg_detection_score_last_window
      - last_event_ts
      - window_minutes

    Also adds convenience aliases for UI:
      - events_last_hour
      - avg_detection_score_last_hour
    """
    try:
        conn = get_conn()
        cur = conn.cursor(dictionary=True)

        now = datetime.utcnow()
        since_dt = now - timedelta(minutes=window_minutes)
        since_str = since_dt.strftime("%Y-%m-%d %H:%M:%S")

        # last event ts
        last_ts_str = None
        try:
            cur.execute("SELECT MAX(COALESCE(alert_ts, updated_ts, ingest_ts)) AS last_ts FROM events")
            row = cur.fetchone()
            last_ts = row.get("last_ts") if row else None
            last_ts_str = last_ts.strftime("%Y-%m-%d %H:%M:%S") if last_ts else None
        except Exception:
            last_ts_str = None

        # events in window and avg detection score
        events_last_window = None
        avg_score = 0.0
        try:
            cur.execute(
                "SELECT COUNT(1) AS cnt, AVG(COALESCE(detection_score,0)) AS avg_score FROM events "
                "WHERE COALESCE(alert_ts, updated_ts, ingest_ts) >= %s",
                (since_str,),
            )
            r = cur.fetchone() or {}
            events_last_window = int(r.get("cnt") or 0)
            avg_score = float(r.get("avg_score") or 0.0)
        except Exception:
            events_last_window = None
            avg_score = 0.0

        # alerts total and by severity (prefer alerts table, fallback to events)
        alerts_total = None
        alerts_by_severity = {}
        try:
            cur.execute("SELECT COUNT(1) AS cnt FROM alerts")
            alerts_total = int(cur.fetchone().get("cnt") or 0)
            cur.execute("SELECT IFNULL(severity,'unknown') AS severity, COUNT(1) AS cnt FROM alerts GROUP BY severity")
            rows = cur.fetchall() or []
            alerts_by_severity = {r.get("severity") or "unknown": int(r.get("cnt") or 0) for r in rows}
        except Exception:
            try:
                cur.execute("SELECT COUNT(1) AS cnt FROM events WHERE label='problem'")
                alerts_total = int(cur.fetchone().get("cnt") or 0)
                cur.execute("SELECT IFNULL(severity,'unknown') AS severity, COUNT(1) AS cnt FROM events WHERE label='problem' GROUP BY severity")
                rows = cur.fetchall() or []
                alerts_by_severity = {r.get("severity") or "unknown": int(r.get("cnt") or 0) for r in rows}
            except Exception:
                alerts_total = None
                alerts_by_severity = {}

        cur.close()
        conn.close()

        # normalize and include UI-friendly aliases
        result = {
            "alerts_total": alerts_total,
            "alerts_by_severity": alerts_by_severity,
            "events_last_window": events_last_window,
            "avg_detection_score_last_window": round(avg_score, 6),
            "last_event_ts": last_ts_str,
            "window_minutes": window_minutes,
            # UI-friendly aliases (for compatibility)
            "events_last_hour": events_last_window,
            "avg_detection_score_last_hour": round(avg_score, 6),
        }
        return result

    except Exception as e:
        log.exception("get_recent_counts failed: %s", e)
        return {
            "alerts_total": None,
            "alerts_by_severity": {},
            "events_last_window": None,
            "avg_detection_score_last_window": 0.0,
            "last_event_ts": None,
            "window_minutes": window_minutes,
            "events_last_hour": None,
            "avg_detection_score_last_hour": 0.0,
            "error": str(e),
        }
