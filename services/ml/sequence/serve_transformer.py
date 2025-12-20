# services/ml/sequence/serve_transformer.py
import os, torch, uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
#from train_transformer import TransformerEncoderModel, EV_TO_ID
from .train_transformer import TransformerEncoderModel, EV_TO_ID


MODEL_PATH = os.getenv("SEQ_MODEL_PATH", "services/ml/models/sequence/transformer_seq.pth")
app = FastAPI()
model = TransformerEncoderModel(vocab_size=len(EV_TO_ID))
if os.path.exists(MODEL_PATH):
    ckpt = torch.load(MODEL_PATH, map_location="cpu")
    model.load_state_dict(ckpt["model"])
    print("Loaded sequence model")
model.eval()

class SeqIn(BaseModel):
    events: list  # list of string event names

@app.post("/sequence/score")
def score_sequence(inp: SeqIn):
    ids = [EV_TO_ID.get(e,0) for e in inp.events]
    import torch
    x = torch.tensor([ids], dtype=torch.long)
    with torch.no_grad():
        s = float(model(x).item())
    return {"score": s}
