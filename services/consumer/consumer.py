"""
Final integrated consumer:

- Session update (Redis or in-memory)
- UEBA (IsolationForest)
- Online learner (River)
- Sequence model scoring (external seq server)
- Threat Intel score
- Simple rule engine (CloudTrail-aware)
- Graph ingestion
- Federated UEBA weights (if available)
- RL adaptive threshold (if available)
- Cross-domain correlation score
- Fusion layer (with optional weights)
- Explainability (SHAP best-effort)
- MySQL persistence (events + alerts)
"""

import os
import sys
import json
import logging
import uuid
from datetime import datetime

import numpy as np
import pandas as pd
import joblib
import redis

# Ensure repo root on path for relative imports
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("consumer")


def pick_identifier_and_severity(rule_score, ueba_score, seq_score, ti_score, corr_score, final_score):
    # Choose identifier_type by priority, return (identifier_type, severity)
    # priority: TI -> rule -> graph -> seq -> ueba -> fused
    identifier = "fused:combination"
    try:
        if ti_score and ti_score > 0.5:
            identifier = "ti:ip_reputation"
        elif rule_score and rule_score >= 0.8:
            identifier = "rule:iam_change"
        elif corr_score and corr_score >= 0.5:
            identifier = "graph:correlation"
        elif seq_score and seq_score >= 0.5:
            identifier = "seq:anomaly"
        elif ueba_score and ueba_score >= 0.5:
            identifier = "ueba:score"
    except Exception:
        identifier = "fused:combination"

    # severity mapping according to your requested thresholds
    # low: < 0.4, medium: 0.4..0.7, high: > 0.7
    if final_score > 0.7:
        severity = "high"
    elif final_score >= 0.4:   # covers 0.4 <= score <= 0.7
        severity = "medium"
    else:
        severity = "low"

    return identifier, severity

# ----------------- Imports with safe fallbacks -----------------

# feature builder & DB wrappers
try:
    from services.consumer.feature_builder import update_session, session_features
    from services.consumer.mysql_db import (
        insert_or_update_event,
        ensure_db_schema,
        insert_alert_from_rec,
    )
except Exception:
    # fallback local imports (repo root on sys.path above tries to help)
    try:
        from feature_builder import update_session, session_features
    except Exception:
        def update_session(r, ev):
            # minimal fallback: keep a tiny per-entity session
            k = (ev.get("entity_id") or (ev.get("userIdentity") or {}).get("userName") or "anon")
            sess = {"count": 1, "events": [ev.get("eventType") or ev.get("eventName")], "unique_events": 1}
            return sess

        def session_features(sess):
            return {"count": sess.get("count", 1), "unique_events": len(sess.get("events", []))}

    try:
        from mysql_db import insert_or_update_event, ensure_db_schema
    except Exception:
        def insert_or_update_event(rec):
            log.info("insert_or_update_event fallback (no-op) for id=%s", rec.get("id"))

        def ensure_db_schema():
            log.info("ensure_db_schema fallback (no-op)")

    # fallback for insert_alert_from_rec — try legacy add_alert if present
    try:
        from services.consumer.db import add_alert as legacy_add_alert
    except Exception:
        try:
            from db import add_alert as legacy_add_alert
        except Exception:
            legacy_add_alert = None

    def insert_alert_from_rec(rec, fusion_explain=None, explanation=None):
        if legacy_add_alert:
            try:
                # add_alert expects (id, entity_id, score, json_event)
                legacy_add_alert(rec.get("id"), rec.get("entity_id"), rec.get("detection_score"), json.dumps(rec.get("normalized") or {}))
            except Exception:
                log.exception("legacy_add_alert failed in fallback insert_alert_from_rec")
        else:
            # no-op fallback
            log.info("insert_alert_from_rec fallback (no-op) id=%s", rec.get("id"))


# sequence client
try:
    from services.consumer.seq_client import score_sequence
except Exception:
    def score_sequence(events):
        return 0.0


# online learner (river)
try:
    from services.online.online_learner import model as online_model
except Exception:
    online_model = None

# graph builder
try:
    from services.graph_service.graph_builder import add_event_to_graph
except Exception:
    def add_event_to_graph(ev):
        return

# fusion layer
try:
    from services.fusion.fusion import fuse as fusion_fuse
except Exception:
    def fusion_fuse(rule_score, ueba_score, seq_score, ti_score, weights=None):
        scores = [v for v in (rule_score, ueba_score, seq_score, ti_score) if v is not None]
        if not scores:
            return 0.0, {"components": {}}
        score = float(np.mean(scores))
        explain = {
            "components": {
                "rule": rule_score,
                "ueba": ueba_score,
                "seq": seq_score,
                "ti": ti_score,
            },
            "weights": weights,
        }
        return score, explain

# explainability
try:
    from services.explain.shap_explainer import explain_tabular
except Exception:
    def explain_tabular(features):
        return {"error": "shap not available"}

# cross-domain correlation
try:
    from services.correlation.correlator import correlate_entity
except Exception:
    def correlate_entity(entity_id):
        return {"entity": entity_id, "correlation_score": 0.0, "neighbors": [], "attribution": 0.0}

# federated UEBA integrator
try:
    from services.federated.integrator import get_fusion_weights
except Exception:
    def get_fusion_weights():
        return None

# RL adaptive threshold helper
try:
    from services.rl.adaptive_threshold import get_threshold as rl_get_threshold
except Exception:
    def rl_get_threshold():
        return None


# ----------------- ENV / globals -----------------

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
MODEL_PATH = os.getenv("MODEL_PATH", "./services/ml/models/iforest_v1.pkl")
DEFAULT_THRESHOLD = float(os.getenv("DETECTION_THRESHOLD", "0.7"))
MYSQL_ENABLED = os.getenv("MYSQL_ENABLED", "true").lower() in ("1", "true", "yes")

# ----------------- Redis / state backend -----------------

try:
    r = redis.Redis(host=REDIS_HOST, port=6379, db=0)
    r.ping()
except Exception:
    class DummyRedis:
        def __init__(self):
            self.store = {}

        # accept TTL argument for compatibility
        def set(self, k, v, ex=None):
            self.store[k] = v

        def get(self, k):
            return self.store.get(k)

        def delete(self, k):
            self.store.pop(k, None)

        def setex(self, k, seconds, v):
            self.set(k, v, ex=seconds)

    r = DummyRedis()
    print("[redis_client] Warning: Redis not reachable at localhost:6379 — using in-memory fallback")


# ----------------- DB init -----------------

if MYSQL_ENABLED:
    try:
        ensure_db_schema()
    except Exception as e:
        log.warning("MySQL ensure schema failed: %s", e)


# ----------------- UEBA model (IsolationForest) -----------------

clf = None
if os.path.exists(MODEL_PATH):
    try:
        clf = joblib.load(MODEL_PATH)
        log.info("Loaded model: %s", MODEL_PATH)
    except Exception as e:
        log.exception("Failed to load model: %s", e)
else:
    log.info("No model file at %s (UEBA will be skipped)", MODEL_PATH)


def compute_iforest_score(feats):
    """
    feats: dict with 'count' and 'unique_events'
    returns anomaly score in [0,1] (higher = more anomalous)
    """
    if clf is None:
        return 0.0
    try:
        df = pd.DataFrame(
            [
                {
                    "count": int(feats.get("count", 0)),
                    "unique_events": int(feats.get("unique_events", 0)),
                }
            ]
        )
        raw = clf.decision_function(df)[0]  # IsolationForest: higher = more normal
        score = float(-raw)  # invert: higher = more anomalous
        return max(0.0, min(1.0, score))
    except Exception as e:
        log.exception("UEBA scoring error: %s", e)
        return 0.0


# ----------------- Core event processing -----------------


def process_event(ev: dict):
    """
    Process a single normalized+enriched event dict.
    Returns a small result dict (used by tests / stdin mode).
    """
    try:
        event_id = ev.get("event_id") or str(uuid.uuid4())
        ev["event_id"] = event_id

        # Normalize some common fields (helpful if replaying raw CloudTrail items)
        # Keep raw original event under ev["_raw"] if needed
        # Accept both 'eventName' (CloudTrail) and 'event_type'
        if "eventName" in ev and "event_type" not in ev:
            ev["event_type"] = ev.get("eventName")
        # entity: userIdentity.userName -> entity_id
        if "userIdentity" in ev and isinstance(ev.get("userIdentity"), dict) and not ev.get("entity_id"):
            ev["entity_id"] = ev.get("userIdentity", {}).get("userName")

        # 1) Update session
        try:
            sess = update_session(r, ev)
        except Exception as e:
            log.exception("Session update failed: %s", e)
            sess = {
                "count": 1,
                "events": [ev.get("event_type") or ev.get("eventName")],
                "unique_events": 1,
            }
        feats = session_features(sess)  # e.g., {"count": N, "unique_events": M}

        # 2) UEBA score
        ueba_score = compute_iforest_score(feats)

        # 3) Online incremental score (River)
        online_score = 0.0
        if online_model is not None:
            try:
                x = {
                    "count": int(feats.get("count", 0)),
                    "unique_events": int(feats.get("unique_events", 0)),
                }
                online_score = float(online_model.score_one(x))
                online_model.learn_one(x)
            except Exception as e:
                log.exception("Online model error: %s", e)
                online_score = 0.0

        # 4) Sequence model score
        seq_score = 0.0
        try:
            events_seq = sess.get("events", [])[-40:]
            seq_score = float(score_sequence(events_seq) or 0.0)
        except Exception as e:
            log.debug("Sequence scoring not available: %s", e)
            seq_score = 0.0

        # 5) Threat intel score (if enrichment added 'ti')
        try:
            ti_score = float(ev.get("ti", {}).get("ip_reputation", 0.0) or 0.0)
        except Exception:
            ti_score = 0.0

        # 6) Simple rule engine (CloudTrail-aware)
        rule_score = 0.0
        et = (ev.get("event_type") or "").lower()
        user = (ev.get("userIdentity") or {}).get("userName") or ev.get("entity_id")
        ip = ev.get("sourceIPAddress") or ev.get("source_ip") or ev.get("sourceIpAddress") or ""

        # 6.1 Console Login (normal / suspicious)
        if "consolelogin" in et:
            # default: normal login → LOW
            rule_score = 0.1

            # impossible travel (very rough demo heuristic)
            last_region = sess.get("last_region")
            cur_region = ev.get("awsRegion") or ev.get("aws_region") or ev.get("region")
            if last_region is not None and cur_region is not None and cur_region != last_region:
                rule_score = max(rule_score, 0.7)

            # known bad IP range (demo)
            if str(ip).startswith("5.199"):
                rule_score = max(rule_score, 0.9)

            # store current region back into session (best-effort)
            sess["last_region"] = cur_region

        # 6.2 Listing buckets → LOW
        elif "listbuckets" in et:
            rule_score = 0.2

        # 6.3 Creating a user → MEDIUM risk
        elif "createuser" in et:
            rule_score = 0.6

        # 6.4 PutBucketPolicy → HIGH risk if public-read
        elif "putbucketpolicy" in et:
            params = ev.get("requestParameters", {}) or {}
            policy = params.get("policy", "") or ""
            if "public-read" in policy:
                rule_score = 0.9
            else:
                rule_score = 0.7

        # 6.5 GetObject → depends on bucket
        elif "getobject" in et:
            params = ev.get("requestParameters", {}) or {}
            bucket = params.get("bucketName", "") or params.get("bucket", "") or ""
            if bucket == "secure-logs":
                rule_score = 0.7  # medium-high: sensitive bucket
            else:
                rule_score = 0.3

        # 6.6 AssumeRole → HIGH risk for admin roles
        elif "assumerole" in et:
            params = ev.get("requestParameters", {}) or {}
            role = params.get("roleArn", "") or ""
            if "Admin" in role:
                rule_score = 1.0
            else:
                rule_score = 0.8

        # 7) Graph ingestion
        try:
            add_event_to_graph(ev)
        except Exception as e:
            log.debug("Graph ingestion failed: %s", e)

        # 8) Cross-domain correlation (graph-based)
        corr_info = {}
        try:
            entity_id = ev.get("entity_id") or user
            if entity_id:
                corr_info = correlate_entity(entity_id)
        except Exception as e:
            log.debug("Correlation failed: %s", e)
            corr_info = {
                "correlation_score": 0.0,
                "neighbors": [],
                "attribution": 0.0,
            }

        corr_score = float(corr_info.get("correlation_score", 0.0) or 0.0)

        # 9) Federated UEBA fusion weights (optional)
        weights = None
        try:
            weights = get_fusion_weights()
        except Exception as e:
            log.debug("Federated weights not available: %s", e)
            weights = None

        # 10) RL adaptive threshold (optional)
        threshold = DEFAULT_THRESHOLD
        try:
            t = rl_get_threshold()
            if t is not None:
                threshold = float(t)
        except Exception as e:
            log.debug("RL threshold not available: %s", e)

        # 11) Fusion (combine signals)
        try:
            try:
                # preferred: fusion supports weights
                final_score, fusion_explain = fusion_fuse(
                    rule_score=float(rule_score),
                    ueba_score=float(ueba_score),
                    seq_score=float(seq_score),
                    ti_score=float(ti_score),
                    weights=weights,
                )
            except TypeError:
                # fallback if fusion doesn't accept 'weights'
                final_score, fusion_explain = fusion_fuse(
                    rule_score=float(rule_score),
                    ueba_score=float(ueba_score),
                    seq_score=float(seq_score),
                    ti_score=float(ti_score),
                )
        except Exception as e:
            log.exception("Fusion error: %s", e)
            final_score = float(max(ueba_score, seq_score, online_score, ti_score, rule_score))
            fusion_explain = {"fallback": True}

        # 11.x) Demo safeguard: never ignore a strong component
        final_score = max(
            float(final_score),
            float(rule_score),
            float(ueba_score),
            float(seq_score),
            float(ti_score),
            float(online_score),
            float(corr_score),
        )
        final_score = max(0.0, min(1.0, final_score))

        is_problem = final_score > threshold
        label = "problem" if is_problem else "normal"

        # 12) Explainability (SHAP-style)
        try:
            feat_for_explain = {
                "count": feats.get("count", 0),
                "unique_events": feats.get("unique_events", 0),
                "ueba": ueba_score,
                "seq": seq_score,
                "ti": ti_score,
                "rule": rule_score,
                "corr": corr_score,
            }
            explanation = explain_tabular(feat_for_explain)
        except Exception as e:
            log.debug("Explainability not available: %s", e)
            explanation = {"note": "explainability failed or not configured"}

        # choose identifier and severity
        identifier_type, severity_label = pick_identifier_and_severity(
            rule_score=rule_score,
            ueba_score=ueba_score,
            seq_score=seq_score,
            ti_score=ti_score,
            corr_score=corr_score,
            final_score=final_score,
        )

        # 13) Persistence (MySQL + legacy SQLite alerts)
        rec = {
            "id": event_id,
            "event_id": ev.get("event_id"),
            "source": ev.get("source") or ev.get("awsRegion") or ev.get("aws_region") or ev.get("source"),
            "entity_type": ev.get("entity_type"),
            "entity_id": ev.get("entity_id") or user,
            "event_type": ev.get("event_type"),
            "raw": ev.get("raw") or ev,
            "normalized": ev,
            "enriched": ev.get("ti", {}),
            "template_id": ev.get("template_id"),
            "ti_score": ti_score,
            "detection_score": final_score,
            "correlation_score": corr_score,
            "identifier_type": identifier_type,
            "severity": severity_label,
            "label": label,
            "detected": is_problem,
            "model_version": clf.__class__.__name__ if clf else "none",
            "alert_ts": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S") if is_problem else None
        }


        if MYSQL_ENABLED:
            try:
                insert_or_update_event(rec)
            except Exception as e:
                log.exception("MySQL write failed: %s", e)

            if is_problem:
                try:
                    insert_alert_from_rec(rec, fusion_explain, explanation)
                    log.info(
                        "ALERT %s %s score=%.3f thresh=%.3f",
                        rec["id"],
                        rec["entity_id"],
                        final_score,
                        threshold,
                    )
                except Exception as e:
                    log.exception("MySQL alert insert failed: %s", e)

        return {
            "event_id": event_id,
            "final_score": final_score,
            "label": label,
            "threshold": threshold,
            "explain": fusion_explain,
            "explain_shap": explanation,
            "correlation": corr_info,
        }

    except Exception as e:
        log.exception("process_event top-level error: %s", e)
        return {"error": str(e)}


# ----------------- Consumer runner (Kafka or local) -----------------


def run_consumer(consume_fn=None):
    kafka_ok = False
    consumer = None
    try:
        from kafka import KafkaConsumer

        consumer = KafkaConsumer(
            "enriched-events",
            bootstrap_servers=KAFKA_BOOTSTRAP,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset="earliest",
            consumer_timeout_ms=1000,
        )
        kafka_ok = True
    except Exception as e:
        log.info("Kafka not available for consumer: %s", e)

    log.info("Consumer started. Kafka available: %s", kafka_ok)
    if consume_fn:
        for ev in consume_fn():
            try:
                process_event(ev)
            except Exception as e:
                log.exception("Error processing event from consume_fn: %s", e)
    elif kafka_ok and consumer is not None:
        for msg in consumer:
            try:
                process_event(msg.value)
            except Exception as e:
                log.exception("Error processing kafka message: %s", e)
    else:
        log.info("No consume function and Kafka not available. Exiting consumer run.")


if __name__ == "__main__":
    # dev mode: read JSON lines from stdin
    log.info("consumer main invoked - reading JSON lines from stdin")
    for line in sys.stdin:
        try:
            ev = json.loads(line.strip())
            out = process_event(ev)
            print(json.dumps(out))
        except Exception as e:
            log.exception("stdin processing error: %s", e)
