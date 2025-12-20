# config_drift.py - compares two JSON snapshots and emits diffs
import json, os
from deepdiff import DeepDiff
def compare_snapshots(old_path, new_path):
    a=json.load(open(old_path)); b=json.load(open(new_path))
    diff = DeepDiff(a,b,ignore_order=True).to_dict()
    return diff

if __name__=="__main__":
    # demo
    open("snap1.json","w").write(json.dumps({"bucket":"public","rules":[1,2]},indent=2))
    open("snap2.json","w").write(json.dumps({"bucket":"public","rules":[1,3]},indent=2))
    print(compare_snapshots("snap1.json","snap2.json"))
