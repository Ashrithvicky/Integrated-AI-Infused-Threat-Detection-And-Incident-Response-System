# services/explain/shap_explainer.py
import joblib, os, numpy as np
import shap
MODEL_PATH = os.getenv("EXPLAIN_MODEL_PATH","services/ml/models/iforest_v1.pkl")
MODEL = None
if os.path.exists(MODEL_PATH):
    MODEL = joblib.load(MODEL_PATH)

def explain_tabular(features: dict):
    """
    features: dict {feature_name: value}
    returns: dictionary of SHAP values per feature
    """
    if MODEL is None:
        return {"error":"no model"}
    # create background (small)
    background = np.array([[0,0]])
    explainer = shap.Explainer(MODEL, background)
    arr = np.array([list(features.values())])
    shap_values = explainer(arr)
    # map back
    return {"shap_values": dict(zip(features.keys(), shap_values.values[0].tolist()))}
