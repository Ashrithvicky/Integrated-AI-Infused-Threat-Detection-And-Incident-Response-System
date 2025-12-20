# services/ml/generate_synthetic.py
import pandas as pd, numpy as np, os
os.makedirs("data", exist_ok=True)
n = 2000
count_normal = np.random.poisson(3, n)
unique_normal = np.random.randint(1,4, n)
m = 50
count_anom = np.random.poisson(30, m)
unique_anom = np.random.randint(5,15, m)
dfn = pd.DataFrame({"count": count_normal, "unique_events": unique_normal, "label": 0})
dfa = pd.DataFrame({"count": count_anom, "unique_events": unique_anom, "label": 1})
df = pd.concat([dfn, dfa], ignore_index=True)
os.makedirs("models", exist_ok=True)
df.to_csv("data/session_features.csv", index=False)
print("Wrote data/session_features.csv")
