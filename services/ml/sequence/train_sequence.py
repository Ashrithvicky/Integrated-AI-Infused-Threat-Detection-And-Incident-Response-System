# train_sequence.py -- small transformer encoder on synthetic event sequences
import os, random, json
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

# Simple synthetic dataset: sequences of event ids mapped to ints
EVENT_VOCAB = ["ConsoleLogin","S3GetObject","EC2StartInstances","IAMPolicyChange","AuthFailure","ProcessStart","MaliciousAction"]
EV_TO_ID = {e:i+1 for i,e in enumerate(EVENT_VOCAB)}  # 0 reserved for pad

class SeqDataset(Dataset):
    def __init__(self, n=2000, seq_len=20, anomaly_frac=0.05):
        self.data=[]
        for _ in range(n):
            seq = [random.choice(list(EV_TO_ID.values())) for _ in range(seq_len)]
            label = 0
            # inject anomaly occasionally
            if random.random() < anomaly_frac:
                seq[random.randrange(seq_len)] = EV_TO_ID["MaliciousAction"]
                label = 1
            self.data.append((torch.tensor(seq,dtype=torch.long), label))
    def __len__(self): return len(self.data)
    def __getitem__(self, i): return self.data[i]

class TransformerEncoderModel(nn.Module):
    def __init__(self, vocab_size, d_model=64, nhead=4, num_layers=2):
        super().__init__()
        self.embed = nn.Embedding(vocab_size+1, d_model, padding_idx=0)
        encoder_layer = nn.TransformerEncoderLayer(d_model=d_model, nhead=nhead)
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.pool = nn.AdaptiveAvgPool1d(1)
        self.fc = nn.Linear(d_model, 1)
    def forward(self, x):
        # x: B x L
        x = self.embed(x).permute(1,0,2)  # L x B x D
        z = self.encoder(x)  # L x B x D
        z = z.permute(1,2,0)  # B x D x L
        pooled = self.pool(z).squeeze(-1)  # B x D
        out = torch.sigmoid(self.fc(pooled)).squeeze(-1)
        return out

def train():
    ds = SeqDataset(n=2500, seq_len=30, anomaly_frac=0.06)
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
    os.makedirs("models/sequence", exist_ok=True)
    torch.save({"model":model.state_dict(),"vocab":EV_TO_ID}, "models/sequence/transformer_seq.pth")
    print("Saved sequence model")

if __name__ == "__main__":
    train()
