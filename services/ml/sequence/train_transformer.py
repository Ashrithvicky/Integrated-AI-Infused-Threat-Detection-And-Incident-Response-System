# services/ml/sequence/train_transformer.py
import os, random, torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

EVENT_VOCAB = ["ConsoleLogin","S3GetObject","EC2StartInstances","IAMPolicyChange","AuthFailure","ProcessStart","MaliciousAction","RunInstances","CreateUser","AttachRolePolicy"]
EV_TO_ID = {e:i+1 for i,e in enumerate(EVENT_VOCAB)}  # pad 0

class SeqDataset(Dataset):
    def __init__(self, n=2000, seq_len=40, anomaly_frac=0.05):
        self.data=[]
        for _ in range(n):
            seq = [random.choice(list(EV_TO_ID.values())) for _ in range(seq_len)]
            label = 0
            if random.random() < anomaly_frac:
                seq[random.randrange(seq_len)] = EV_TO_ID["MaliciousAction"]
                label = 1
            self.data.append((torch.tensor(seq,dtype=torch.long), label))
    def __len__(self): return len(self.data)
    def __getitem__(self, i): return self.data[i]

class TransformerEncoderModel(nn.Module):
    def __init__(self, vocab_size, d_model=128, nhead=4, num_layers=2):
        super().__init__()
        self.embed = nn.Embedding(vocab_size+1, d_model, padding_idx=0)
        encoder_layer = nn.TransformerEncoderLayer(d_model=d_model, nhead=nhead, batch_first=True)
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.fc = nn.Sequential(nn.Linear(d_model,64), nn.ReLU(), nn.Linear(64,1))
    def forward(self, x):
        # x: B x L
        x = self.embed(x)  # B x L x D
        z = self.encoder(x)  # B x L x D
        pooled = z.mean(dim=1)  # average pool
        out = torch.sigmoid(self.fc(pooled)).squeeze(-1)
        return out

def train_and_save(out_path="services/ml/models/sequence/transformer_seq.pth"):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    ds = SeqDataset(n=3000, seq_len=40, anomaly_frac=0.05)
    dl = DataLoader(ds, batch_size=64, shuffle=True)
    model = TransformerEncoderModel(vocab_size=len(EV_TO_ID))
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = nn.BCELoss()
    model.train()
    for epoch in range(6):
        running=0.0
        for xb,yb in dl:
            pred = model(xb)
            loss = loss_fn(pred, yb.float())
            opt.zero_grad(); loss.backward(); opt.step()
            running += loss.item()
        print(f"Epoch {epoch} loss {running/len(dl):.4f}")
    torch.save({"model":model.state_dict(), "vocab":EV_TO_ID}, out_path)
    print("Saved transformer sequence model to", out_path)

if __name__ == "__main__":
    train_and_save()
