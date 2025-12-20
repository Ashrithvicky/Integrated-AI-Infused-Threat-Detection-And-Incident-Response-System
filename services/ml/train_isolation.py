# services/ml/train_isolation.py
import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib, os
os.makedirs("models", exist_ok=True)
df = pd.read_csv("data/session_features.csv")
X = df[["count","unique_events"]]
clf = IsolationForest(n_estimators=200, contamination=0.02, random_state=42)
clf.fit(X)
joblib.dump(clf, "services/ml/models/iforest_v1.pkl")
print("Saved model to models/iforest_v1.pkl")
