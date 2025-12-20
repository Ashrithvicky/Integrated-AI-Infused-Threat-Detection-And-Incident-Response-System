# services/model_server/serve.py
from fastapi import FastAPI
from pydantic import BaseModel
import joblib, os
import numpy as np
from dotenv import load_dotenv
load_dotenv()

MODEL_PATH = os.getenv("MODEL_PATH", "./services/ml/models/iforest_v1.pkl")
app = FastAPI()
clf = None
try:
    if os.path.exists(MODEL_PATH):
        clf = joblib.load(MODEL_PATH)
        print("Loaded model")
    else:
        print("Model not found at", MODEL_PATH)
except Exception as e:
    print("Model load error", e)

class SessionFeat(BaseModel):
    count: int
    unique_events: int

@app.post("/score")
def score(sf: SessionFeat):
    vec = np.array([[sf.count, sf.unique_events]])
    if clf is None:
        return {"score": 0.0, "message": "no model"}
    raw = clf.decision_function(vec)[0]
    score = float(-raw)
    return {"score": score}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
