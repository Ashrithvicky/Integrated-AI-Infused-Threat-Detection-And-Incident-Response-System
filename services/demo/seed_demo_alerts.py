# services/demo/seed_demo_alerts.py
import os
import json
import mysql.connector
from datetime import datetime, timedelta
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


def ensure_tables():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("USE {}".format(DB_NAME))

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
          id BIGINT AUTO_INCREMENT PRIMARY KEY,
          event_id VARCHAR(64) NOT NULL UNIQUE,
          entity_id VARCHAR(255),
          entity_type VARCHAR(64),
          event_type VARCHAR(128),
          source VARCHAR(64),
          ts DATETIME,
          raw LONGTEXT,
          normalized LONGTEXT,
          detection_score DOUBLE,
          ti_score DOUBLE,
          sequence_score DOUBLE,
          graph_score DOUBLE,
          fusion_score DOUBLE,
          label VARCHAR(32),
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS alerts (
          id BIGINT AUTO_INCREMENT PRIMARY KEY,
          event_id VARCHAR(64) NOT NULL,
          entity_id VARCHAR(255),
          entity_type VARCHAR(64),
          event_type VARCHAR(128),
          source VARCHAR(64),
          detection_score DOUBLE,
          ti_score DOUBLE,
          correlation_score DOUBLE,
          label VARCHAR(32),
          alert_ts DATETIME,
          `explain` LONGTEXT,
          `explain_shap` LONGTEXT,
          `raw` LONGTEXT,
          `normalized` LONGTEXT,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          KEY idx_event_id (event_id)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS feedback (
          id BIGINT AUTO_INCREMENT PRIMARY KEY,
          event_id VARCHAR(64) NOT NULL,
          analyst VARCHAR(128),
          label VARCHAR(32),
          comment TEXT,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          KEY idx_fb_event_id (event_id)
        )
        """
    )

    conn.commit()
    cur.close()
    conn.close()


def seed_demo():
    ensure_tables()
    conn = get_conn()
    cur = conn.cursor()

    # Check if we already have alerts
    cur.execute("SELECT COUNT(*) FROM alerts")
    (count,) = cur.fetchone()
    if count > 0:
        print(f"alerts table already has {count} rows, not seeding demo data.")
        cur.close()
        conn.close()
        return

    now = datetime.utcnow()

    # --- Demo event 1: IAM user login from unusual IP ---
    ev1_id = "demo-evt-alice-1"
    ev1_raw = {
        "eventVersion": "1.08",
        "eventTime": now.isoformat() + "Z",
        "eventSource": "signin.amazonaws.com",
        "eventName": "ConsoleLogin",
        "awsRegion": "us-east-1",
        "sourceIPAddress": "203.0.113.10",
        "userIdentity": {
            "type": "IAMUser",
            "userName": "alice",
            "arn": "arn:aws:iam::123456789012:user/alice",
        },
        "eventID": ev1_id,
    }
    ev1_norm = {
        "event_id": ev1_id,
        "entity_id": "alice",
        "entity_type": "user",
        "event_type": "ConsoleLogin",
        "source": "aws_cloudtrail",
    }

    # --- Demo event 2: Root login from suspicious IP ---
    ev2_id = "demo-evt-root-1"
    ev2_raw = {
        "eventVersion": "1.08",
        "eventTime": (now + timedelta(minutes=1)).isoformat() + "Z",
        "eventSource": "signin.amazonaws.com",
        "eventName": "ConsoleLogin",
        "awsRegion": "us-east-1",
        "sourceIPAddress": "198.51.100.250",
        "userIdentity": {
            "type": "Root",
            "arn": "arn:aws:iam::123456789012:root",
        },
        "eventID": ev2_id,
    }
    ev2_norm = {
        "event_id": ev2_id,
        "entity_id": "arn:aws:iam::123456789012:root",
        "entity_type": "root",
        "event_type": "ConsoleLogin",
        "source": "aws_cloudtrail",
    }

    # Insert into events table
    ev_sql = """
    INSERT INTO events
      (event_id, entity_id, entity_type, event_type, source, ts,
       raw, normalized, detection_score, ti_score, sequence_score, graph_score, fusion_score, label)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    cur.execute(
        ev_sql,
        (
            ev1_id,
            ev1_norm["entity_id"],
            ev1_norm["entity_type"],
            ev1_norm["event_type"],
            ev1_norm["source"],
            now,
            json.dumps(ev1_raw),
            json.dumps(ev1_norm),
            0.92,
            0.10,
            0.35,
            0.40,
            0.88,
            "problem",
        ),
    )

    cur.execute(
        ev_sql,
        (
            ev2_id,
            ev2_norm["entity_id"],
            ev2_norm["entity_type"],
            ev2_norm["event_type"],
            ev2_norm["source"],
            now + timedelta(minutes=1),
            json.dumps(ev2_raw),
            json.dumps(ev2_norm),
            0.97,
            0.70,
            0.50,
            0.60,
            0.95,
            "problem",
        ),
    )

    # Insert into alerts table (what frontend reads)
    alert_sql = """
    INSERT INTO alerts
      (`event_id`, `entity_id`, `entity_type`, `event_type`, `source`,
       `detection_score`, `ti_score`, `correlation_score`, `label`, `alert_ts`,
       `explain`, `explain_shap`, `raw`, `normalized`)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    explain1 = {
        "fusion": "Anomalous login pattern for user alice from rare IP.",
        "features": {"iforest": 0.92, "seq": 0.35, "ti": 0.10, "graph": 0.40},
    }
    explain2 = {
        "fusion": "Root ConsoleLogin from suspicious IP with high TI score.",
        "features": {"iforest": 0.97, "seq": 0.50, "ti": 0.70, "graph": 0.60},
    }

    shap1 = {"sourceIPAddress": 0.4, "user_type": 0.3}
    shap2 = {"sourceIPAddress": 0.6, "user_type": 0.5}

    cur.execute(
        alert_sql,
        (
            ev1_id,
            ev1_norm["entity_id"],
            ev1_norm["entity_type"],
            ev1_norm["event_type"],
            ev1_norm["source"],
            0.92,
            0.10,
            0.55,
            "problem",
            now,
            json.dumps(explain1),
            json.dumps(shap1),
            json.dumps(ev1_raw),
            json.dumps(ev1_norm),
        ),
    )

    cur.execute(
        alert_sql,
        (
            ev2_id,
            ev2_norm["entity_id"],
            ev2_norm["entity_type"],
            ev2_norm["event_type"],
            ev2_norm["source"],
            0.97,
            0.70,
            0.85,
            "problem",
            now + timedelta(minutes=1),
            json.dumps(explain2),
            json.dumps(shap2),
            json.dumps(ev2_raw),
            json.dumps(ev2_norm),
        ),
    )

    conn.commit()
    cur.close()
    conn.close()
    print("Seeded 2 demo alerts into MySQL.")
    

if __name__ == "__main__":
    seed_demo()
