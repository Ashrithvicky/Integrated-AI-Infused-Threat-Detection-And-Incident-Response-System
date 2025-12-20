# services/rl/adaptive_threshold.py
"""
Adaptive detection threshold helper.

Stores current threshold and adjusts it based on analyst feedback.
"""

import os
import json

STATE_FILE = os.getenv("RL_THRESH_STATE", "services/rl/threshold_state.json")
DEFAULT_THRESH = float(os.getenv("DETECTION_THRESHOLD", "0.7"))


def _load_state():
    if not os.path.exists(STATE_FILE):
        return {"threshold": DEFAULT_THRESH, "history": []}
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_state(s):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(s, f, indent=2)


def get_threshold():
    return _load_state().get("threshold", DEFAULT_THRESH)


def update_with_feedback(event_id: str, feedback_label: str):
    """
    feedback_label: "problem" or "normal" (from analyst)
    If analyst marks event as "problem", we lower threshold slightly
    to be more sensitive. If "normal", we raise threshold slightly.
    """
    s = _load_state()
    t = s.get("threshold", DEFAULT_THRESH)

    if feedback_label == "problem":
        t = max(0.1, t - 0.01)
    else:
        t = min(0.99, t + 0.01)

    s["threshold"] = t
    s["history"].append({
        "event": event_id,
        "label": feedback_label,
        "new_threshold": t
    })
    _save_state(s)
    return t


if __name__ == "__main__":
    print("Current threshold:", get_threshold())
    print("After marking event1 as problem:", update_with_feedback("event1","problem"))
    print("After marking event2 as normal:", update_with_feedback("event2","normal"))
