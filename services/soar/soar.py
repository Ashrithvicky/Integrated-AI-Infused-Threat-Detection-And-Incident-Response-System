# services/soar/soar.py
import os, time, requests
from dotenv import load_dotenv
load_dotenv()
ALERT_API = os.getenv("ALERT_API", "http://localhost:8000")

def run():
    print("SOAR stub started, polling", ALERT_API + "/alerts")
    while True:
        try:
            res = requests.get(ALERT_API + "/alerts", timeout=5)
            arr = res.json()
            for a in arr:
                print("SOAR: alert", a["id"], "entity", a["entity_id"], "score", a["score"])
            time.sleep(10)
        except Exception as e:
            print("SOAR poll error", e)
            time.sleep(5)

if __name__ == "__main__":
    run()
