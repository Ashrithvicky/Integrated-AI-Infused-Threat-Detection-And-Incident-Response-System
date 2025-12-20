# contrastive_train.py - tiny contrastive encoder POC using two modalities (log/token & biometrics)
'''import torch, torch.nn as nn, random
from torch.utils.data import Dataset, DataLoader
class SimpleEnc(nn.Module):
    def __init__(self, in_dim, hid=64):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(in_dim,hid), nn.ReLU(), nn.Linear(hid,hid))
    def forward(self,x): return self.net(x)

class SimDataset(Dataset):
    def __init__(self, n=2000):
        self.data=[]
        for _ in range(n):
            a=torch.randn(16)  # modality A (logs)
            b=torch.randn(12)  # modality B (biometrics)
            self.data.append((a,b))
    def __len__(self): return len(self.data)
    def __getitem__(self, i): return self.data[i]

def info_nce(z1,z2, temp=0.5):
    z1 = nn.functional.normalize(z1,dim=1)
    z2 = nn.functional.normalize(z2,dim=1)
    logits = z1 @ z2.t() / temp
    labels = torch.arange(z1.size(0))
    return nn.CrossEntropyLoss()(logits, labels)

def train():
    ds=SimDataset()
    dl=DataLoader(ds,batch_size=64,shuffle=True)
    encA=SimpleEnc(16); encB=SimpleEnc(12)
    opt = torch.optim.Adam(list(encA.parameters())+list(encB.parameters()), lr=1e-3)
    for epoch in range(8):
        lsum=0.0
        for a,b in dl:
            za=encA(a); zb=encB(b)
            loss = info_nce(za,zb)
            opt.zero_grad(); loss.backward(); opt.step()
            lsum+=loss.item()
        print("Epoch",epoch,"loss",lsum/len(dl))
    torch.save({"A":encA.state_dict(),"B":encB.state_dict()},"models/fusion/contrastive.pth")
    print("saved fusion model")
if __name__=="__main__":
    train()
'''

# services/ml/fusion/contrastive_train.py
import os, torch, torch.nn as nn
from torch.utils.data import DataLoader, Dataset
import numpy as np

class SimpleEnc(nn.Module):
    def __init__(self, in_dim, hid=64):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(in_dim,hid), nn.ReLU(), nn.Linear(hid,hid))
    def forward(self,x): return self.net(x)

class SimDataset(Dataset):
    def __init__(self, n=2000):
        self.data=[]
        for _ in range(n):
            a = np.random.randn(16).astype(np.float32)  # logs
            b = np.random.randn(12).astype(np.float32)  # biometrics
            self.data.append((a,b))
    def __len__(self): return len(self.data)
    def __getitem__(self,i): return self.data[i]

def info_nce(z1,z2,temp=0.5):
    z1 = nn.functional.normalize(z1,dim=1)
    z2 = nn.functional.normalize(z2,dim=1)
    logits = z1 @ z2.t() / temp
    labels = torch.arange(z1.size(0), device=z1.device)
    return nn.CrossEntropyLoss()(logits, labels)

def train(save_path="services/ml/models/fusion/contrastive.pth"):
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    ds = SimDataset()
    dl = DataLoader(ds, batch_size=128, shuffle=True)
    encA = SimpleEnc(16); encB = SimpleEnc(12)
    opt = torch.optim.Adam(list(encA.parameters())+list(encB.parameters()), lr=1e-3)
    for epoch in range(6):
        tot=0.0
        for a,b in dl:
            a=torch.tensor(a); b=torch.tensor(b)
            za = encA(a); zb = encB(b)
            loss = info_nce(za,zb)
            opt.zero_grad(); loss.backward(); opt.step()
            tot += loss.item()
        print("Epoch",epoch,"loss",tot/len(dl))
    torch.save({"A":encA.state_dict(),"B":encB.state_dict()}, save_path)
    print("Saved fusion model to", save_path)

if __name__=="__main__":
    train()
