import yaml
import json
from parse_namelist import summarize_atm_in

with open("config/runs.yml") as f:
    cfg = yaml.safe_load(f)

matrix = []

for run in cfg["runs"]:
    summary = summarize_atm_in(run["atm_in"])
    summary["run_name"] = run["name"]
    matrix.append(summary)

print("Loaded config")
print("Config keys:", cfg.keys())
print("Runs in YAML:", len(cfg.get("runs", [])))

print("Runs in matrix before write:", len(matrix))

with open("docs/run_matrix.json", "w") as f:
    json.dump(matrix, f, indent=2)
