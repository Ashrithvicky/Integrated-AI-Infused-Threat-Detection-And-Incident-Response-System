# services/rl/rl_agent.py
import random, json, os
ACTIONS = ["notify","collect_forensics","isolate_host"]
Q = {a:0.0 for a in ACTIONS}
N = {a:1 for a in ACTIONS}
EPS = float(os.getenv("RL_EPS", "0.1"))

def select_action():
    if random.random() < EPS:
        return random.choice(ACTIONS)
    return max(Q.items(), key=lambda x:x[1])[0]

def update(action, reward):
    N[action] += 1
    Q[action] += (reward - Q[action]) / N[action]

if __name__=="__main__":
    for _ in range(50):
        a = select_action()
        r = random.choice([0,1])
        update(a,r)
    print("Q",Q)
