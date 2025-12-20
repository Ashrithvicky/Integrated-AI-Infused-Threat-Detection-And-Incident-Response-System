# keystroke_ingest.py - ingest keystroke timing vectors
import random, time, json
def gen_keystroke(user="alice@example.com"):
    # simple vector of inter-key delays (ms)
    vec = [random.uniform(50,200) for _ in range(40)]
    return {"event_id": str(time.time()), "timestamp": time.time(), "source":"keystroke", "entity_id":user, "event_type":"keystroke", "raw":{"vector":vec}}

if __name__ == "__main__":
    while True:
        e = gen_keystroke()
        print("keystroke event:", e["entity_id"], "len", len(e["raw"]["vector"]))
        time.sleep(0.7)
