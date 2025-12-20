# biometrics_model.py - simple classifier (kNN) on timing vectors
import joblib, os
from sklearn.neighbors import KNeighborsClassifier
import numpy as np

MODEL_PATH = "./services/biometrics/models/biometrics_knn.pkl"
def train_demo():
    os.makedirs("./services/biometrics/models", exist_ok=True)
    # synthetic data: 3 users
    X=[]; y=[]
    users=["alice","bob","carol"]
    for uid,u in enumerate(users):
        for _ in range(150):
            base = np.random.normal(loc=100+uid*5, scale=15, size=40)
            X.append(base)
            y.append(u)
    clf = KNeighborsClassifier(n_neighbors=3)
    clf.fit(X,y)
    joblib.dump(clf, MODEL_PATH)
    print("saved biometrics model")
if __name__ == "__main__":
    train_demo()
