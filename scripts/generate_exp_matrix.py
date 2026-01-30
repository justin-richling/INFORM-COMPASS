import yaml
import json
import os
from parse_namelist import summarize_atm_in
from pathlib import Path

def load_matrix(path="run_matrix.json"):
    p = Path(path)
    if not p.exists() or p.stat().st_size == 0:
        with open(p, "w") as f:
            json.dump([], f)
        return []
    #if not os.path.exists(path):
    #    return []
    with open(p) as f:
        #print("AHHHH",f)
        return json.load(f)
    

def diff_runs(old, new):
    diffs = {}

    # Compare nudged_vars
    old_set = set(old.get("nudged_vars", []))
    new_set = set(new.get("nudged_vars", []))
    added = new_set - old_set
    removed = old_set - new_set
    if added or removed:
        diffs["nudged_vars"] = {"added": list(added), "removed": list(removed)}

    # Compare cosp_vars
    old_set = set(old.get("cosp_vars", []))
    new_set = set(new.get("cosp_vars", []))
    added = new_set - old_set
    removed = old_set - new_set
    if added or removed:
        diffs["cosp_vars"] = {"added": list(added), "removed": list(removed)}

    # Compare fincl keys
    old_keys = set(old.get("fincl", {}).keys())
    new_keys = set(new.get("fincl", {}).keys())
    added = new_keys - old_keys
    removed = old_keys - new_keys
    if added or removed:
        diffs["fincl_keys"] = {"added": list(added), "removed": list(removed)}

    # Optional: compare other_vars
    old_set = set(old.get("other_vars", []))
    new_set = set(new.get("other_vars", []))
    added = new_set - old_set
    removed = old_set - new_set
    if added or removed:
        diffs["other_vars"] = {"added": list(added), "removed": list(removed)}

    return diffs


def add_entry(matrix, new_entry, interactive=False):
    for existing in matrix:
        if existing["run_name"] == new_entry["run_name"]:
            if existing.get("atm_in_sha256") == new_entry.get("atm_in_sha256"):
                print(f"✔ Run '{new_entry['run_name']}' already exists (identical atm_in). Skipping.")
                return matrix, "duplicate"

            print(f"⚠ Same run_name but different atm_in")
            diffs = diff_runs(existing, new_entry)
            print("📝 Differences:", diffs)
            return matrix, "conflict"
    matrix.append(new_entry)
    print(f" Added new run: {new_entry['run_name']}")
    return matrix, "added"


matrix = load_matrix("docs/run_matrix.json")

with open("config/runs.yml") as f:
    cfg = yaml.safe_load(f)

for run in cfg["runs"]:
    summary = summarize_atm_in(run["atm_in"])
    if summary is None:
        continue
    summary["run_name"] = run["name"]

    status = "added"
    matrix, status = add_entry(matrix, summary, interactive=False)
    #if status in {"duplicate", "conflict"}:
    #    exit(1)  # fail workflow if desired

print("Loaded config")
print("Config keys:", cfg.keys())
print("Runs in YAML:", len(cfg.get("runs", [])))

print("Runs in matrix before write:", len(matrix))

with open("docs/run_matrix.json", "w") as f:
    json.dump(matrix, f, indent=2)
