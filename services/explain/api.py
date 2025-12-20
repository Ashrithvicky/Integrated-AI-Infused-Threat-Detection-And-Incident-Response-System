# services/explain/api.py
# services/explain/api.py
import os, sys
# ensure project root is in path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from fastapi import FastAPI
from pydantic import BaseModel
from services.explain.shap_explainer import explain_tabular
from services.explain.seq_explain import token_importance
...



app = FastAPI()

class TabIn(BaseModel):
    features: dict

@app.post("/explain/tabular")
def explain_tab(tab: TabIn):
    return explain_tabular(tab.features)

class SeqIn(BaseModel):
    events: list

@app.post("/explain/sequence")
def explain_seq(s: SeqIn):
    return token_importance(s.events)

if __name__=="__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)
