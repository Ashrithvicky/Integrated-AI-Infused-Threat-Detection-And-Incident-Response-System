# simulator.py - emits attack chains into ingest pipeline (in-process)
import time, random
from datetime import datetime
from uuid import uuid4

ATTACK_CHAINS = [
    ["PhishingClick","CredentialHarvest","ConsoleLogin","PrivilegeEscalation","DataExfil"],
    ["LateralMove","ProcessStart","AccessSensitive","Exfil"],
]

def make_attack_event(chain_step, victim="alice@example.com"):
    return {
        "event_id": str(uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "source": "attack-sim",
        "entity_type": "user",
        "entity_id": victim,
        "event_type": chain_step,
        "geo": {"ip": "45.55.66.77"},
        "raw": {"details": f"Simulated attack step {chain_step}"}
    }

def run_simulator(publish_fn, cadence=1.0):
    while True:
        chain = random.choice(ATTACK_CHAINS)
        victim = random.choice(["alice@example.com","bob@example.com"])
        for step in chain:
            ev = make_attack_event(step, victim=victim)
            publish_fn(ev)
            print("[ATTACK_SIM] emitted", step, "->", victim)
            time.sleep(cadence)
        time.sleep(10)

if __name__ == "__main__":
    # demo: write to stdout
    run_simulator(lambda e: print("emit", e["event_type"]), cadence=0.5)
