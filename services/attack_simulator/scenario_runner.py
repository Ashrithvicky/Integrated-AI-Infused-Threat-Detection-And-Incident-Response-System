# services/attack_simulator/scenario_runner.py
import os, sys, time, random
import yaml
from datetime import datetime

# Ensure repo root on path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from services.normalizer.normalizer import normalize
from services.enrich.enrich import enrich_event
from services.consumer.consumer import process_event

SCENARIO_DIR = os.getenv("SCENARIO_DIR", os.path.join("services", "attack_simulator", "scenarios"))

def load_scenario(name: str):
    path = os.path.join(SCENARIO_DIR, name + ".yaml")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Scenario file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def run_scenario(name: str, cadence: float = 0.7):
    scen = load_scenario(name)
    victims = scen.get("victims", ["alice@example.com"])
    victim = random.choice(victims)
    chain = scen.get("chain", [])

    print(f"[SCENARIO] Running scenario '{name}' for victim {victim}")
    for step in chain:
        action = step.get("action", "UnknownAction")
        ev = {
            "event_id": f"sim-{int(time.time()*1000)}-{random.randint(1,9999)}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "source": "digital_twin",
            "entity_type": "user",
            "entity_id": victim,
            "event_type": action,
            "raw": step,
        }
        norm = normalize(ev)
        enrich_event(norm, publish_fn=None)
        process_event(norm)
        print(f"[SCENARIO] emitted {action} -> {victim}")
        time.sleep(cadence)

if __name__ == "__main__":
    # default run
    scenario_name = os.getenv("SCENARIO_NAME", "basic_phish")
    run_scenario(scenario_name, cadence=0.7)
