# services/consumer/api.py
'''import os
import traceback
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from fastapi.encoders import jsonable_encoder
# services/consumer/api.py (add or update)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(...)

# during development enable the frontend origin(s) you use
frontend_origins = [
    "http://localhost:5173",  # Vite / React dev server
    "http://localhost:3000",  # optional: other dev ports
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins,      # or ["*"] for quick debug (not for prod)
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


load_dotenv()

# import get_alerts from your db wrapper
from services.consumer.db import get_alerts


LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, LOG_LEVEL), format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("consumer.api")

app = FastAPI(title="ThreatSys API (consumer)", debug=(os.getenv("DEBUG", "0") == "1"))

# Allow local frontend; add other origins if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("CORS_ALLOW_ORIGIN", "http://localhost:5173")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

# small helper to return demo alerts if DB isn't available (set ENABLE_DEMO=1 to use)
def demo_alerts():
    return [
        {
            "id": "demo-1",
            "event_id": "demo-evt-1",
            "entity_id": "alice",
            "entity_type": "iam",
            "event_type": "ConsoleLogin",
            "source": "us-east-1",
            "detection_score": 0.9,
            "ti_score": 0.0,
            "correlation_score": 0.5,
            "identifier_type": "rule:iam_change",
            "severity": "high",
            "label": "problem",
            "alert_ts": "2025-12-10 00:00:00"
        }
    ]

@app.get("/alerts")
def alerts(limit: int = 200):
    """
    Return latest alerts. If DB unavailable and ENABLE_DEMO=1, returns demo data.
    Always returns JSON-serializable response (datetimes converted).
    """
    try:
        rows = get_alerts(limit)
        # jsonable_encoder converts datetimes, Decimal, set, etc -> JSON-safe primitives
        safe = jsonable_encoder(rows)
        return JSONResponse(content=safe)
    except Exception as exc:
        tb = traceback.format_exc()
        log.error("Error in /alerts: %s\n%s", exc, tb)

        if os.getenv("ENABLE_DEMO", "0") == "1":
            log.info("Returning demo alerts because ENABLE_DEMO=1")
            return JSONResponse(status_code=200, content=demo_alerts())

        return JSONResponse(
            status_code=500,
            content={"error": "internal_server_error", "detail": str(exc), "traceback": tb.splitlines()[-10:]},
        )
# helpful exception handler so unhandled exceptions are visible as JSON too
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    log.error("Unhandled exception: %s\n%s", exc, tb)
    return JSONResponse(
        status_code=500,
        content={"error": "unhandled_exception", "detail": str(exc), "traceback": tb.splitlines()[-10:]},
    )
print(">>> USING get_alerts FROM:", get_alerts.__module__)
# immediately after importing get_alerts in services/consumer/api.py
log.info("USING get_alerts FROM: %s", getattr(get_alerts, "__module__", str(get_alerts)))
log.info("DB config: MYSQL_HOST=%s MYSQL_USER=%s MYSQL_DB=%s MYSQL_PORT=%s", os.getenv("MYSQL_HOST"), 
         os.getenv("MYSQL_USER"), os.getenv('MYSQL_DB'), os.getenv('MYSQL_PORT'))


# services/consumer/api.py  -> add imports at top
import socket
from datetime import datetime

# and add endpoint function after /alerts handler:

def _check_redis():
    try:
        from services.consumer.mysql_db import r  # if your app exposes r, else attempt direct redis ping
        # if not available, attempt redis import
        try:
            r.ping()
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    except Exception:
        # best-effort: try redis client
        try:
            import redis
            client = redis.Redis(host=os.getenv("REDIS_HOST", "localhost"), port=6379, db=0)
            client.ping()
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}

def _check_kafka():
    try:
        from kafka import KafkaAdminClient
        kb = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
        try:
            admin = KafkaAdminClient(bootstrap_servers=kb, request_timeout_ms=2000)
            admin.close()
            return {"ok": True, "bootstrap": kb}
        except Exception as e:
            return {"ok": False, "bootstrap": kb, "error": str(e)}
    except Exception:
        return {"ok": False, "error": "kafka library not installed or unreachable", "bootstrap": os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")}

@app.get("/system-health")
def system_health():
    """
    Returns a JSON object describing system health: db, redis, kafka, model, recent event/alert counts.
    """
    from services.consumer.mysql_db import get_conn, get_recent_counts, MYSQL_HOST, MYSQL_PORT, MYSQL_DB, MYSQL_USER, MODEL_PATH

    tstamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    db_status = {"ok": False}
    db_counts = {}
    try:
        conn = get_conn()
        # simple ping: get version
        cur = conn.cursor()
        cur.execute("SELECT VERSION()")
        ver = cur.fetchone()[0] if cur else "unknown"
        cur.close()
        conn.close()
        db_status = {"ok": True, "host": f"{MYSQL_HOST}:{MYSQL_PORT}", "database": MYSQL_DB, "user": MYSQL_USER, "version": ver}
        db_counts = get_recent_counts(window_minutes=60)
    except Exception as e:
        db_status = {"ok": False, "host": f"{MYSQL_HOST}:{MYSQL_PORT}", "error": str(e)}

    # redis
    redis_status = _check_redis()

    # kafka
    kafka_status = _check_kafka()

    # model / file existence
    model_ok = os.path.exists(MODEL_PATH)
    model_info = {"ok": model_ok, "path": MODEL_PATH}
    # if you load model object somewhere you can include loaded flag and model name

    # Build summary
    summary = {
        "alerts_by_severity": db_counts.get("alerts_by_severity", {}),
        "events_ingested_last_hour": db_counts.get("events_last_window", 0),
        "avg_detection_score_last_hour": db_counts.get("avg_detection_score", 0.0),
    }

    overall_ok = db_status.get("ok", False) and redis_status.get("ok", False)

    payload = {
        "timestamp": tstamp,
        "ok": overall_ok,
        "components": {
            "mysql": dict(db_status, **{"counts": db_counts}),
            "redis": redis_status,
            "kafka": kafka_status,
            "model": model_info,
        },
        "summary": summary,
        "raw": {
            "sample_event": None
        }
    }
    return JSONResponse(content=payload)


import os
import time
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

# Try to import optional helpers, handle if not present
try:
    from services.consumer.mysql_db import get_conn, get_recent_counts, MYSQL_HOST, MYSQL_PORT, MYSQL_DB, MYSQL_USER, MODEL_PATH
except Exception as e:
    # If import fails, keep sensible defaults and record the import error
    get_conn = None
    get_recent_counts = None
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
    MYSQL_DB = os.getenv("MYSQL_DB", "threatsys")
    MYSQL_USER = os.getenv("MYSQL_USER", "threatuser")
    MODEL_PATH = os.getenv("MODEL_PATH", "./services/ml/models/iforest_v1.pkl")
    import_err_msg = str(e)
else:
    import_err_msg = None

@router.get("/system-health")
def system_health(minutes: int = 60):
    """Return simple health info for DB, model and optional services."""
    generated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    result = {
        "db": {"host": MYSQL_HOST, "port": MYSQL_PORT, "db": MYSQL_DB, "user": MYSQL_USER, "ok": False},
        "model": {"path": MODEL_PATH, "loaded": False},
        "recent": {"minutes": minutes, "recent_alerts": None, "recent_events": None, "alerts_by_severity": {}},
        "services": {"redis": False, "sequence_server": False, "federated_integrator": False},
        "generated_at": generated_at,
        "import_error": import_err_msg,
    }

    # 1) DB quick ping
    try:
        if get_conn is not None:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("SELECT 1")
            _ = cur.fetchone()
            cur.close()
            conn.close()
            result["db"]["ok"] = True
        else:
            # can't import get_conn - leave ok=false and note it
            result["db"]["ok"] = False
    except Exception as e:
        result["db"]["ok"] = False
        result["db"]["error"] = str(e)

    # 2) Model check (exists on disk)
    try:
        result["model"]["loaded"] = os.path.exists(MODEL_PATH)
    except Exception as e:
        result["model"]["loaded"] = False
        result["model"]["error"] = str(e)

    # 3) recent counts (optional)
    try:
        if get_recent_counts is not None:
            counts = get_recent_counts(minutes=minutes)  # expected to return dict
            # normalize expected structure
            result["recent"].update({
                "recent_alerts": counts.get("alerts", None),
                "recent_events": counts.get("events", None),
                "alerts_by_severity": counts.get("by_severity", {}),
            })
        else:
            result["recent"]["note"] = "get_recent_counts not available"
    except Exception as e:
        result["recent"]["error"] = str(e)

    # 4) probe optional services (non-fatal)
    # Redis: try connect if redis lib present and env configured (simple probe)
    try:
        import redis
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            r = redis.from_url(redis_url, socket_connect_timeout=1)
            pong = r.ping()
            result["services"]["redis"] = bool(pong)
        except Exception:
            result["services"]["redis"] = False
    except Exception:
        result["services"]["redis"] = False

    # Sequence server / federated integrator: simple socket check or HTTP GET could be added.
    # keep false by default.

    # 5) Done — return JSON. If DB was down and no import error, use 200; if import error present include 500 status so you notice
    status = 200
    if import_err_msg:
        # give visibility while dev is ongoing
        status = 500

    return JSONResponse(status_code=status, content=result)

# include router
app.include_router(router)



if __name__ == "__main__":
    # convenience dev runner (you can also run via uvicorn)
    import uvicorn
    uvicorn.run("services.consumer.api:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True, log_level="info")
    

'''

'''
# services/consumer/api.py
import os
import time
import traceback
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder

load_dotenv()

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, LOG_LEVEL), format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("consumer.api")

# Single FastAPI app (no duplicate instantiations)
app = FastAPI(title="ThreatSys Consumer API", version="0.1", debug=(os.getenv("DEBUG", "0") == "1"))

# CORS configuration (allow dev frontend by default)
_frontend_origins = os.getenv("CORS_ALLOW_ORIGINS")
if _frontend_origins:
    try:
        ORIGINS = [o.strip() for o in _frontend_origins.split(",") if o.strip()]
    except Exception:
        ORIGINS = ["http://localhost:5173"]
else:
    ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Try to import DB helpers. If they fail, keep safe fallbacks so this file doesn't require edits elsewhere.
_import_err: Optional[str] = None
get_conn = None
get_recent_counts = None
ensure_db_schema = None
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_DB = os.getenv("MYSQL_DB", "threatsys")
MYSQL_USER = os.getenv("MYSQL_USER", "threatuser")
MODEL_PATH = os.getenv("MODEL_PATH", "./services/ml/models/iforest_v1.pkl")

try:
    # prefer mysql_db if available
    from services.consumer import mysql_db as mysql_db_mod  # type: ignore
    # pull known names if present - else keep None and handle later
    get_conn = getattr(mysql_db_mod, "get_conn", None)
    get_recent_counts = getattr(mysql_db_mod, "get_recent_counts", None)
    ensure_db_schema = getattr(mysql_db_mod, "ensure_db_schema", None)
    MYSQL_HOST = getattr(mysql_db_mod, "MYSQL_HOST", MYSQL_HOST)
    MYSQL_PORT = int(getattr(mysql_db_mod, "MYSQL_PORT", MYSQL_PORT))
    MYSQL_DB = getattr(mysql_db_mod, "MYSQL_DB", MYSQL_DB)
    MYSQL_USER = getattr(mysql_db_mod, "MYSQL_USER", MYSQL_USER)
    MODEL_PATH = getattr(mysql_db_mod, "MODEL_PATH", MODEL_PATH)
except Exception as e:
    _import_err = f"mysql_db import failed: {e}"
    log.debug("mysql_db import failed in api.py: %s", traceback.format_exc())

# Try to import get_alerts from services.consumer.db (alerts endpoint)
get_alerts = None
try:
    from services.consumer.db import get_alerts  # type: ignore
except Exception as e:
    _import_err = (_import_err or "") + f"; get_alerts import failed: {e}"
    log.debug("services.consumer.db.get_alerts import failed: %s", traceback.format_exc())
    get_alerts = None

# Demo fallback alerts used if DB functions are unavailable or ENABLE_DEMO=1
def demo_alerts():
    return [
        {
            "id": "demo-1",
            "event_id": "demo-evt-1",
            "entity_id": "alice",
            "entity_type": "iam",
            "event_type": "ConsoleLogin",
            "source": "us-east-1",
            "detection_score": 0.9,
            "ti_score": 0.0,
            "correlation_score": 0.5,
            "identifier_type": "rule:iam_change",
            "severity": "high",
            "label": "problem",
            "alert_ts": "2025-12-10 00:00:00",
        }
    ]

# Startup: attempt to ensure DB schema if helper exists (non-fatal)
@app.on_event("startup")
def _startup():
    try:
        if ensure_db_schema:
            log.info("Calling ensure_db_schema() on startup")
            ensure_db_schema()
        else:
            log.debug("ensure_db_schema not available - skipping DB schema check at startup")
    except Exception as e:
        log.exception("ensure_db_schema failed: %s", e)


@app.get("/health")
def health():
    """Simple health check for the API itself."""
    return {"status": "ok", "time": datetime.utcnow().isoformat()}


@app.get("/alerts")
def alerts(limit: int = 200):
    """
    Return latest alerts from DB (get_alerts). Falls back to demo alerts if DB or helper is unavailable.
    """
    try:
        if get_alerts is None:
            raise RuntimeError("get_alerts not available")
        rows = get_alerts(limit)
        safe = jsonable_encoder(rows)
        return JSONResponse(status_code=200, content=safe)
    except Exception as exc:
        log.error("Error in /alerts: %s", exc)
        if os.getenv("ENABLE_DEMO", "0") == "1":
            log.info("Returning demo alerts because ENABLE_DEMO=1")
            return JSONResponse(status_code=200, content=demo_alerts())
        # else expose error
        return JSONResponse(status_code=500, content={"error": "failed_fetch_alerts", "detail": str(exc)})


def _probe_redis() -> Dict[str, Any]:
    """Best-effort redis probe; non-fatal."""
    try:
        import redis  # type: ignore
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        client = redis.from_url(redis_url, socket_connect_timeout=1)
        pong = client.ping()
        return {"ok": bool(pong), "url": redis_url}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _probe_kafka() -> Dict[str, Any]:
    """Best-effort kafka probe; non-fatal and optional (kafka lib may be missing)."""
    try:
        from kafka import KafkaAdminClient  # type: ignore
        kb = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
        try:
            admin = KafkaAdminClient(bootstrap_servers=kb, request_timeout_ms=2000)
            admin.close()
            return {"ok": True, "bootstrap": kb}
        except Exception as e:
            return {"ok": False, "bootstrap": kb, "error": str(e)}
    except Exception as e:
        return {"ok": False, "error": "kafka lib missing or unreachable", "detail": str(e)}


@app.get("/system-health")
def system_health(minutes: int = 60):
    """
    Robust system health endpoint.

    Returns checks for:
      - MySQL connectivity and recent counts (uses get_conn/get_recent_counts if available)
      - Redis (best-effort)
      - Kafka (best-effort)
      - Model file existence
      - Summary metrics aggregated

    This endpoint is tolerant of missing helpers and will include `import_error` when
    helper imports failed so you can debug without editing other files.
    """
    generated_at = datetime.utcnow().isoformat()
    result: Dict[str, Any] = {
        "generated_at": generated_at,
        "ok": False,
        "import_error": _import_err,
        "components": {
            "mysql": {"ok": False, "host": f"{MYSQL_HOST}:{MYSQL_PORT}", "db": MYSQL_DB, "user": MYSQL_USER},
            "redis": {"ok": False},
            "kafka": {"ok": False},
            "model": {"ok": False, "path": MODEL_PATH},
        },
        "recent": {"minutes": minutes, "alerts": None, "events": None, "alerts_by_severity": {}},
    }

    # MySQL quick ping + recent counts (if helpers available)
    try:
        if get_conn:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("SELECT VERSION()")
            ver = cur.fetchone()[0] if cur else "unknown"
            cur.close()
            try:
                conn.close()
            except Exception:
                pass
            result["components"]["mysql"].update({"ok": True, "version": ver})
        else:
            result["components"]["mysql"].update({"ok": False, "note": "get_conn helper not available"})
    except Exception as e:
        result["components"]["mysql"].update({"ok": False, "error": str(e)})

    # recent counts: tolerant to missing function names/arg shapes
    try:
        if get_recent_counts:
            # our helper might accept minutes or hours param; try common shapes
            try:
                counts = get_recent_counts(minutes)  # preferred signature
            except TypeError:
                try:
                    counts = get_recent_counts(hours=int(max(1, minutes / 60)))  # fallback
                except TypeError:
                    counts = get_recent_counts()  # last resort

            # normalize expected keys
            result["recent"]["alerts"] = counts.get("alerts") or counts.get("alerts_total") or counts.get("recent_alerts")
            result["recent"]["events"] = counts.get("events") or counts.get("events_last_hour") or counts.get("recent_events")
            result["recent"]["alerts_by_severity"] = counts.get("by_severity") or counts.get("alerts_by_severity") or {}
        else:
            result["recent"]["note"] = "get_recent_counts helper not available"
    except Exception as e:
        result["recent"]["error"] = str(e)

    # Redis probe
    try:
        redis_status = _probe_redis()
        result["components"]["redis"] = redis_status
    except Exception as e:
        result["components"]["redis"] = {"ok": False, "error": str(e)}

    # Kafka probe
    try:
        kafka_status = _probe_kafka()
        result["components"]["kafka"] = kafka_status
    except Exception as e:
        result["components"]["kafka"] = {"ok": False, "error": str(e)}

    # Model existence
    try:
        model_ok = os.path.exists(MODEL_PATH)
        result["components"]["model"].update({"ok": bool(model_ok)})
    except Exception as e:
        result["components"]["model"].update({"ok": False, "error": str(e)})

    # Build summary from available pieces
    try:
        alerts_total = None
        if isinstance(result["recent"].get("alerts"), int):
            alerts_total = result["recent"]["alerts"]
        elif isinstance(result["recent"].get("events"), int):
            alerts_total = result["recent"]["events"]

        result["summary"] = {
            "alerts_total": alerts_total,
            "alerts_by_severity": result["recent"].get("alerts_by_severity", {}),
            "events_window_minutes": minutes,
        }
    except Exception:
        result["summary"] = {}

    # overall ok heuristic: mysql ok AND model ok (redis/kafka optional for local dev)
    overall_ok = bool(result["components"]["mysql"].get("ok")) and bool(result["components"]["model"].get("ok"))
    result["ok"] = overall_ok

    status_code = 200 if overall_ok else 500 if _import_err else 200
    return JSONResponse(status_code=status_code, content=jsonable_encoder(result))


# Global exception handler (nice JSON trace)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    log.error("Unhandled exception: %s\n%s", exc, tb)
    payload = {"error": "unhandled_exception", "detail": str(exc), "traceback": tb.splitlines()[-10:]}
    return JSONResponse(status_code=500, content=payload)


if __name__ == "__main__":
    # convenience runner for dev (you can also use uvicorn externally)
    import uvicorn

    uvicorn.run(
        "services.consumer.api:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=(os.getenv("DEBUG", "0") == "1"),
        log_level=os.getenv("UVICORN_LOG_LEVEL", "info"),
    )
'''

# services/consumer/api.py
import os
import time
import traceback
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder

load_dotenv()

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, LOG_LEVEL), format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("consumer.api")

# Create FastAPI app once
app = FastAPI(title="ThreatSys Consumer API", version="0.1", debug=(os.getenv("DEBUG", "0") == "1"))

# CORS (allow dev frontend origins)
_frontend_env = os.getenv("CORS_ALLOW_ORIGINS")
if _frontend_env:
    try:
        ORIGINS = [o.strip() for o in _frontend_env.split(",") if o.strip()]
    except Exception:
        ORIGINS = ["http://localhost:5173"]
else:
    ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Try to import mysql_db helpers — keep fallbacks so no other files must change
_import_err: Optional[str] = None
get_conn = None
get_recent_counts = None
ensure_db_schema = None
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_DB = os.getenv("MYSQL_DB", "threatsys")
MYSQL_USER = os.getenv("MYSQL_USER", "threatuser")
MODEL_PATH = os.getenv("MODEL_PATH", "./services/ml/models/iforest_v1.pkl")

try:
    from services.consumer import mysql_db as mysql_db_mod  # type: ignore
    get_conn = getattr(mysql_db_mod, "get_conn", None)
    get_recent_counts = getattr(mysql_db_mod, "get_recent_counts", None)
    ensure_db_schema = getattr(mysql_db_mod, "ensure_db_schema", None)
    MYSQL_HOST = getattr(mysql_db_mod, "MYSQL_HOST", MYSQL_HOST)
    MYSQL_PORT = int(getattr(mysql_db_mod, "MYSQL_PORT", MYSQL_PORT))
    MYSQL_DB = getattr(mysql_db_mod, "MYSQL_DB", MYSQL_DB)
    MYSQL_USER = getattr(mysql_db_mod, "MYSQL_USER", MYSQL_USER)
    MODEL_PATH = getattr(mysql_db_mod, "MODEL_PATH", MODEL_PATH)
except Exception as e:
    _import_err = f"mysql_db import failed: {e}"
    log.debug("mysql_db import failed in api.py: %s", traceback.format_exc())

# Try to import get_alerts to power /alerts endpoint
get_alerts = None
try:
    from services.consumer.db import get_alerts  # type: ignore
except Exception:
    get_alerts = None
    log.debug("services.consumer.db.get_alerts not available; /alerts will fallback to demo")

def demo_alerts():
    return [
        {
            "id": "demo-1",
            "event_id": "demo-evt-1",
            "entity_id": "alice",
            "entity_type": "iam",
            "event_type": "ConsoleLogin",
            "source": "us-east-1",
            "detection_score": 0.9,
            "ti_score": 0.0,
            "correlation_score": 0.5,
            "identifier_type": "rule:iam_change",
            "severity": "high",
            "label": "problem",
            "alert_ts": "2025-12-10 00:00:00",
        }
    ]

@app.on_event("startup")
def _startup():
    try:
        if ensure_db_schema:
            log.info("Calling ensure_db_schema() on startup")
            ensure_db_schema()
        else:
            log.debug("ensure_db_schema not available")
    except Exception:
        log.exception("ensure_db_schema failed at startup")

@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}

@app.get("/alerts")
def alerts(limit: int = 200):
    try:
        if get_alerts is None:
            raise RuntimeError("get_alerts not available")
        rows = get_alerts(limit)
        safe = jsonable_encoder(rows)
        return JSONResponse(status_code=200, content=safe)
    except Exception as exc:
        log.error("Error in /alerts: %s", exc)
        if os.getenv("ENABLE_DEMO", "0") == "1":
            return JSONResponse(status_code=200, content=demo_alerts())
        return JSONResponse(status_code=500, content={"error": "failed_fetch_alerts", "detail": str(exc)})

def _probe_redis() -> Dict[str, Any]:
    try:
        import redis  # type: ignore
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        client = redis.from_url(redis_url, socket_connect_timeout=1)
        pong = client.ping()
        return {"ok": bool(pong), "url": redis_url}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def _probe_kafka() -> Dict[str, Any]:
    try:
        from kafka import KafkaAdminClient  # type: ignore
        kb = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
        try:
            admin = KafkaAdminClient(bootstrap_servers=kb, request_timeout_ms=2000)
            admin.close()
            return {"ok": True, "bootstrap": kb}
        except Exception as e:
            return {"ok": False, "bootstrap": kb, "error": str(e)}
    except Exception as e:
        return {"ok": False, "error": "kafka lib missing or unreachable", "detail": str(e)}

@app.get("/system-health")
def system_health(minutes: int = 60):
    generated_at = datetime.utcnow().isoformat()
    result: Dict[str, Any] = {
        "generated_at": generated_at,
        "ok": False,
        "import_error": _import_err,
        "components": {
            "mysql": {"ok": False, "host": f"{MYSQL_HOST}:{MYSQL_PORT}", "db": MYSQL_DB, "user": MYSQL_USER},
            "redis": {"ok": False},
            "kafka": {"ok": False},
            "model": {"ok": False, "path": MODEL_PATH},
        },
        "recent": {"minutes": minutes, "alerts": None, "events": None, "alerts_by_severity": {}},
        "summary": {"alerts_total": None, "alerts_by_severity": {}, "events_last_hour": None, "avg_detection_score_last_hour": 0.0},
    }

    # MySQL ping
    try:
        if get_conn:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("SELECT VERSION()")
            ver = cur.fetchone()[0] if cur else "unknown"
            try: cur.close()
            except: pass
            try: conn.close()
            except: pass
            result["components"]["mysql"].update({"ok": True, "version": ver})
        else:
            result["components"]["mysql"].update({"ok": False, "note": "get_conn helper not available"})
    except Exception as e:
        result["components"]["mysql"].update({"ok": False, "error": str(e)})

    # recent counts
    try:
        if get_recent_counts:
            # try common call shapes
            try:
                counts = get_recent_counts(window_minutes=minutes)
            except TypeError:
                try:
                    counts = get_recent_counts(minutes)
                except TypeError:
                    try:
                        counts = get_recent_counts()
                    except Exception as e:
                        raise
            # normalize keys
            result["recent"]["alerts"] = counts.get("alerts") or counts.get("alerts_total") or counts.get("recent_alerts")
            result["recent"]["events"] = counts.get("events") or counts.get("events_last_window") or counts.get("events_last_hour")
            result["recent"]["alerts_by_severity"] = counts.get("by_severity") or counts.get("alerts_by_severity") or {}
            # populate summary (UI-friendly)
            result["summary"]["alerts_total"] = result["recent"]["alerts"]
            result["summary"]["alerts_by_severity"] = result["recent"]["alerts_by_severity"]
            result["summary"]["events_last_hour"] = result["recent"]["events"]
            result["summary"]["avg_detection_score_last_hour"] = counts.get("avg_detection_score_last_window") or counts.get("avg_detection_score") or 0.0
            # attach raw counts to components.mysql for debugging
            result["components"]["mysql"]["counts"] = counts
        else:
            result["recent"]["note"] = "get_recent_counts helper not available"
    except Exception as e:
        result["recent"]["error"] = str(e)

    # Redis probe
    try:
        redis_status = _probe_redis()
        result["components"]["redis"] = redis_status
    except Exception as e:
        result["components"]["redis"] = {"ok": False, "error": str(e)}

    # Kafka probe
    try:
        kafka_status = _probe_kafka()
        result["components"]["kafka"] = kafka_status
    except Exception as e:
        result["components"]["kafka"] = {"ok": False, "error": str(e)}

    # Model existence
    try:
        model_ok = os.path.exists(MODEL_PATH)
        result["components"]["model"].update({"ok": bool(model_ok)})
    except Exception as e:
        result["components"]["model"].update({"ok": False, "error": str(e)})

    # overall OK heuristic
    overall_ok = bool(result["components"]["mysql"].get("ok")) and bool(result["components"]["model"].get("ok"))
    result["ok"] = overall_ok

    status_code = 200 if overall_ok else 500 if _import_err else 200
    return JSONResponse(status_code=status_code, content=jsonable_encoder(result))


# friendly JSON exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    log.error("Unhandled exception: %s\n%s", exc, tb)
    payload = {"error": "unhandled_exception", "detail": str(exc), "traceback": tb.splitlines()[-10:]}
    return JSONResponse(status_code=500, content=payload)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("services.consumer.api:app", host=os.getenv("HOST", "0.0.0.0"), port=int(os.getenv("PORT", 8000)), reload=(os.getenv("DEBUG", "0") == "1"), log_level=os.getenv("UVICORN_LOG_LEVEL", "info"))
