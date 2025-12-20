# services/explain/seq_explain.py
# Very light-weight: compute gradient-based token importance for transformer.
import torch
import os
from services.ml.sequence.train_transformer import TransformerEncoderModel, EV_TO_ID
MODEL_PATH = "services/ml/models/sequence/transformer_seq.pth"
model = TransformerEncoderModel(vocab_size=len(EV_TO_ID))
if torch.cuda.is_available():
    device = "cuda"
else:
    device = "cpu"
model.to(device)
if os.path.exists(MODEL_PATH):
    ckpt = torch.load(MODEL_PATH, map_location=device)
    model.load_state_dict(ckpt["model"])
model.eval()

def token_importance(events):
    # events: list of tokens
    ids = [EV_TO_ID.get(e,0) for e in events]
    x = torch.tensor([ids], dtype=torch.long, device=device).requires_grad_(True)
    out = model(x)
    out.backward()
    grads = x.grad if x.grad is not None else None
    # approximate importance by embedding gradient norm
    # This is simplified: better to compute gradient wrt input embeddings
    return {"importance": "gradient-based POC not fully implemented"}
    