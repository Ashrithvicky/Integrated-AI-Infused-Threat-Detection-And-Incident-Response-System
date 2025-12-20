import joblib
import numpy as np
from biometrics.keystroke_ingest import load_keystrokes

MODEL_PATH = "biometrics/models/biometrics_knn.pkl"

def main():
    print("\n[Biometrics Evaluation]\n")

    model = joblib.load(MODEL_PATH)
    samples = load_keystrokes()

    distances = []

    for s in samples:
        dist, _ = model.kneighbors([s])
        distances.append(dist[0][0])

    print("Samples evaluated:", len(distances))
    print("Avg keystroke distance:", np.mean(distances))
    print("Max deviation:", max(distances))

if __name__ == "__main__":
    main()
