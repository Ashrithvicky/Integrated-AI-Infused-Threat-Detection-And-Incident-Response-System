# services/attack_simulator/attack_simulator.py


# services/attack_simulator/attack_simulator.py
import os, sys, time, random, json
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

try:
    from services.normalizer.normalizer import normalize
    from services.enrich.enrich import enrich_event
    from services.consumer.consumer import process_event
except Exception:
    from normalizer import normalize
    from enrich import enrich_event
    from consumer import process_event
...


ATTACKS = [
    {"name":"phishing_to_priv_esc", "chain":["PhishingClick","CredentialHarvest","ConsoleLogin","PrivilegeEscalation","DataExfil"]},
    {"name":"lateral_movement", "chain":["InitialAccess","LateralMovement","ProcessStart","RemoteExec","Exfiltration"]},
    {"name":"supply_chain", "chain":["ThirdPartyCompromise","SupplyChainPayload","Deploy","Persistence","Exfiltration"]}
]

def make_attack_event(step, victim):
    return {
        "event_id": f"atk-{int(time.time()*1000)}-{random.randint(1,9999)}",
        "timestamp": datetime.utcnow().isoformat()+"Z",
        "source":"attack_sim",
        "entity_type":"user",
        "entity_id":victim,
        "event_type":step,
        "raw":{"detail":f"Simulated attack step {step}"},
        "meta":{"simulated":True}
    }

def run_simulation(cadence=0.5, direct=True, attack_names=None):
    victims = ["alice@example.com","bob@example.com","devops@example.com"]
    while True:
        attack = random.choice(ATTACKS) if not attack_names else next((a for a in ATTACKS if a["name"] in attack_names), ATTACKS[0])
        victim = random.choice(victims)
        for step in attack["chain"]:
            ev = make_attack_event(step, victim)
            if direct:
                norm = normalize(ev); enrich_event(norm, publish_fn=None); process_event(norm)
            else:
                # TODO kafka: produce to raw-events
                print("KAFKA mode not implemented in this feeder in direct releases")
            print("[ATTACK_SIM] emitted", step, "->", victim)
            time.sleep(cadence)
        time.sleep(random.uniform(5,15))

if __name__ == "__main__":
    run_simulation()
