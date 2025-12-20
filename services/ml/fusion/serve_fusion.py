# services/ml/fusion/serve_fusion.py
import os, sys
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import torch
from fastapi import FastAPI
from pydantic import BaseModel

from services.ml.fusion.contrastive_train import SimpleEnc  # correct module path
MODEL_PATH = os.getenv("FUSION_MODEL_PATH", "services/ml/models/fusion/contrastive.pth")
app = FastAPI()
encA = SimpleEnc(16); encB = SimpleEnc(12)
if os.path.exists(MODEL_PATH):
    ckpt = torch.load(MODEL_PATH, map_location="cpu")
    encA.load_state_dict(ckpt["A"]); encB.load_state_dict(ckpt["B"])
    print("Loaded fusion model")
encA.eval(); encB.eval()

class FusionIn(BaseModel):
    modalityA: list
    modalityB: list

@app.post("/fusion/embed")
def embed(inp: FusionIn):
    a = torch.tensor([inp.modalityA], dtype=torch.float32)
    b = torch.tensor([inp.modalityB], dtype=torch.float32)
    with torch.no_grad():
        za = encA(a); zb = encB(b)
        z = (za + zb) / 2.0
        vec = z.squeeze(0).numpy().tolist()
    return {"embedding": vec}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8011)
