import yaml
import json
import os
from parse_namelist import summarize_atm_in

def load_matrix(path="run_matrix.json"):
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return json.load(f)
    

def add_entry(matrix, new_entry, interactive=True):
    for existing in matrix:
        if existing["run_name"] == new_entry["run_name"]:
            if existing["atm_in_sha256"] == new_entry["atm_in_sha256"]:
                print(f"✔ Run '{new_entry['run_name']}' already exists (identical atm_in). Skipping.")
                return matrix

            # Same name, different content
            print(f"⚠ Run name '{new_entry['run_name']}' already exists but atm_in differs.")
            print(f"  Existing snapshot: {existing['snapshot_date']}")
            print(f"  New snapshot:      {new_entry['snapshot_date']}")

            if interactive:
                resp = input("Add anyway as a new entry? [y/N]: ").strip().lower()
                if resp != "y":
                    print("⏭ Skipping.")
                    return matrix

    print(f" Adding new run: {new_entry['run_name']}")
    matrix.append(new_entry)
    return matrix


matrix = load_matrix("docs/run_matrix.json")

with open("config/runs.yml") as f:
    cfg = yaml.safe_load(f)

for run in cfg["runs"]:
    summary = summarize_atm_in(run["atm_in"])
    if summary is None:
        continue
    summary["run_name"] = run["name"]
    matrix = add_entry(matrix, summary)

print("Loaded config")
print("Config keys:", cfg.keys())
print("Runs in YAML:", len(cfg.get("runs", [])))

print("Runs in matrix before write:", len(matrix))

with open("docs/run_matrix.json", "w") as f:
    json.dump(matrix, f, indent=2)
