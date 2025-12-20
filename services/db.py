# services/db.py
import os
import json
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "threatuser")
DB_PASS = os.getenv("DB_PASS", "threatpass")
DB_NAME = os.getenv("DB_NAME", "threatsys")

def get_conn():
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
    )

def get_alerts(limit: int = 200):
    conn = get_conn()
    cur = conn.cursor(dictionary=True)
    sql = """
    SELECT
      id,
      event_id,
      entity_id,
      entity_type,
      event_type,
      source,
      detection_score,
      ti_score,
      correlation_score,
      identifier_type,
      severity,
      label,
      alert_ts,
      explain,
      explain_shap,
      raw,
      normalized
    FROM events
    ORDER BY alert_ts DESC, updated_ts DESC
    LIMIT %s
    """
    cur.execute(sql, (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    # Convert JSON text columns to objects if needed
    for r in rows:
        for key in ("explain", "explain_shap", "raw", "normalized"):
            val = r.get(key)
            if isinstance(val, str):
                try:
                    r[key] = json.loads(val)
                except Exception:
                    pass
    return rows
