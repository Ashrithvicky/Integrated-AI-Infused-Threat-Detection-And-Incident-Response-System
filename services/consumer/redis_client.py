# services/consumer/redis_client.py
"""
Resilient Redis client helper.
Tries to connect to real redis.Redis. If connection fails, returns a light-weight
in-memory fallback implementing get/set with optional TTL (best-effort).
"""

import os, time, threading
from dotenv import load_dotenv
load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

class InMemoryRedis:
    def __init__(self):
        self._store = {}
        self._exp = {}
        self._lock = threading.Lock()
        # background cleanup thread
        t = threading.Thread(target=self._cleanup_loop, daemon=True)
        t.start()

    def _cleanup_loop(self):
        while True:
            now = time.time()
            with self._lock:
                to_del = [k for k, exp in self._exp.items() if exp is not None and exp <= now]
                for k in to_del:
                    self._store.pop(k, None)
                    self._exp.pop(k, None)
            time.sleep(1.0)

    def set(self, key, value, ex=None):
        with self._lock:
            self._store[key] = value
            self._exp[key] = time.time() + ex if ex is not None else None
        return True

    def get(self, key):
        with self._lock:
            exp = self._exp.get(key)
            if exp is not None and exp <= time.time():
                # expired
                self._store.pop(key, None)
                self._exp.pop(key, None)
                return None
            return self._store.get(key)

    def delete(self, key):
        with self._lock:
            self._store.pop(key, None)
            self._exp.pop(key, None)
        return True

    # convenience to mimic redis encoding
    def setex(self, key, time_seconds, value):
        return self.set(key, value, ex=time_seconds)

def get_redis_client(host: str = REDIS_HOST, port: int = REDIS_PORT):
    """
    Try to return a real redis.Redis client. If connection fails, return InMemoryRedis.
    """
    try:
        import redis
        client = redis.Redis(host=host, port=port, db=0, socket_connect_timeout=1)
        # quick health check
        client.ping()
        return client
    except Exception:
        # fallback
        print("[redis_client] Warning: Redis not reachable at {}:{} — using in-memory fallback".format(host, port))
        return InMemoryRedis()
class DummyRedis:
    def __init__(self): self.store = {}
    def get(self, k): return self.store.get(k)
    def set(self, k, v, ex=None): self.store[k] = v
    def setex(self, k, seconds, v): self.set(k, v, ex=seconds)
