# fusion.py - merge scores and optionally provide SHAP for tabular model
import numpy as np, json, os
def fuse(rule_score, ueba_score, seq_score, ti_score, weights=None):
    if weights is None:
        weights = {"rule":0.4,"ueba":0.25,"seq":0.2,"ti":0.15}
    score = weights["rule"]*rule_score + weights["ueba"]*ueba_score + weights["seq"]*seq_score + weights["ti"]*ti_score
    # simple explain output
    explain = {"components": {"rule":rule_score,"ueba":ueba_score,"seq":seq_score,"ti":ti_score}, "weights":weights}
    return float(score), explain
