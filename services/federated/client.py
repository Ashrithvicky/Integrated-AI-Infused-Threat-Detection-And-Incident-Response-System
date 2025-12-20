# services/federated/client.py
import time, random, requests, os, numpy as np
SERVER = os.getenv("FED_SERVER","http://localhost:9000")
CLIENT_ID = os.getenv("CLIENT_ID","client1")

def local_train_step():
    # toy "model" = vector of 10 floats learned from local data
    return list(np.random.randn(10).tolist())

def run():
    try:
        requests.post(SERVER+"/register", json={"client_id":CLIENT_ID}, timeout=5)
    except Exception as e:
        print("cannot register", e); return
    while True:
        w = local_train_step()
        try:
            requests.post(SERVER+"/submit_update", json={"client_id":CLIENT_ID,"weights":w}, timeout=5)
            resp = requests.get(SERVER+"/get_global", timeout=5).json()
            print("posted update; global len:", len(resp.get("global") or []))
        except Exception as e:
            print("error", e)
        time.sleep(10)

if __name__=="__main__":
    run()
