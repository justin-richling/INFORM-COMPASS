import re, os
from datetime import datetime
import hashlib
"""
def hash_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()
"""

def load_cam_doc(docsies):
    fincl_blocks = {}
    cosp_vars = {}
    nudged_vars = {}
    other_vars = {}
    empty_htapes = {}

    current_key = None
    current_type = None  # "fincl" or "nudge"
    try:
        with open(docsies, "r") as f:
            for raw_line in f:
                line = raw_line.rstrip()

                # End of namelist
                if line.strip() == "/":
                    current_key = None
                    current_type = None
                    continue

                # New variable assignment
                m = re.match(r"\s*([A-Za-z0-9_]+)\s*=", line)
                if m:
                    key = m.group(1)
                    key_lower = key.lower()

                    if key_lower.startswith("empty_htapes"):
                        current_key = key
                        current_type = "empty_htapes"
                        empty_htapes[current_key] = [line.strip()]
                        continue

                    # ---- fincl* blocks ----
                    if key_lower.startswith("cosp") or "cosp".lower() in key_lower:
                        current_key = key
                        current_type = "cosp"
                        cosp_vars[current_key] = [line.strip()]
                        continue

                    # ---- fincl* blocks ----
                    if key_lower.startswith("fincl"):
                        current_key = key
                        current_type = "fincl"
                        fincl_blocks[current_key] = [line.strip()]
                        continue

                    # ---- nudged variables ----
                    if key_lower.startswith("nudge_"):
                        current_key = key
                        current_type = "nudge"
                        nudged_vars[current_key] = [line.strip()]
                        continue

                    # ---- single-line vars ----
                    if key_lower in {"mfilt", "nhtfrq", "ncdata"}:
                        other_vars[key] = line.strip()
                        current_key = None
                        current_type = None
                        continue

                    # Anything else → reset
                    current_key = None
                    current_type = None
                    continue

                # ---- Continuation lines ----
                if current_key and line.startswith(" "):
                    if current_type == "fincl":
                        fincl_blocks[current_key].append(line.strip())
                    elif current_type == "nudge":
                        nudged_vars[current_key].append(line.strip())
                    elif current_type == "cosp":
                        cosp_vars[current_key].append(line.strip())
                    elif current_type == "empty_htapes":
                        empty_htapes[current_key].append(line.strip())
    except FileNotFoundError as e:
        print(e)
        return None, None, None, None, None


    fincl_dict = {}
    for key,val in fincl_blocks.items():
        sure_single = re.sub(r"\s+",
                                " ",
                                " ".join(val)
                            ).strip()
        fincl_vars = re.findall(r"'([^']+)'", sure_single)
        fincl_dict[key] = fincl_vars

    nudge_atm_in = []
    for key,val in nudged_vars.items():
        for v in val:
            nudge_atm_in.append(v.replace("\t\t"," "))

    other_vars_atm_in = []
    for key,val in other_vars.items():
        other_vars_atm_in.append(val.replace("\t\t"," "))

    cosp_vars_atm_in = []
    for key,val in cosp_vars.items():
        for v in val:
            cosp_vars_atm_in.append(v.replace("\t\t"," "))

    empty_htapes_atm_in = []
    for key,val in empty_htapes.items():
        for v in val:
            empty_htapes_atm_in.append(v.replace("\t\t"," "))

    return fincl_dict, cosp_vars_atm_in, nudge_atm_in, other_vars_atm_in, empty_htapes_atm_in



def summarize_atm_in(atm_in_path):
    fincl_dict, cosp_vars, nudge_vars, other_vars, empty_htapes = load_cam_doc(atm_in_path)
    # normalize all nudged vars to lowercase
    nudge_atm_in_normalized = []
    for v in nudge_vars:
        # split at the first '='
        if '=' in v:
            lhs, rhs = v.split('=', 1)
            lhs = lhs.strip().lower()        # lowercase only the variable name
            rhs = rhs.strip()                # keep the value exactly as-is
            nudge_atm_in_normalized.append(f"{lhs} = {rhs}")
        else:
            # if no '=', just lowercase the whole string (rare case)
            nudge_atm_in_normalized.append(v.lower())
        with open(atm_in_path, "rb") as f:
            data = f.read()
        sha256 = hashlib.sha256(data).hexdigest()

    if fincl_dict is None and cosp_vars is None and nudge_vars is None and other_vars is None and empty_htapes is None:
        return {
            "run_name": None,  # or however you define it
            "nudging": None,
            "nudged_vars": None,
            "cosp": None,
            "cosp_vars": None,
            "fincl": None,
            "empty_htapes": None,
            "other_vars": None,
            "source_atm_in": os.path.basename(atm_in_path),
            "atm_in_sha256": sha256,
            "snapshot_date": datetime.now(datetime.astimezone.utc).isoformat()
        }

    
    return {
        "run_name": atm_in_path.split("/")[-2],  # or however you define it
        "nudging": len(nudge_atm_in) > 0,
        "nudged_vars": nudge_atm_in,
        "cosp": len(cosp_vars) > 0,
        "cosp_vars": cosp_vars,
        "fincl": fincl_dict,
        "empty_htapes": empty_htapes,
        "other_vars": other_vars,
        "source_atm_in": os.path.basename(atm_in_path),
        "atm_in_sha256": sha256,
       # "snapshot_date": datetime.now(datetime.astimezone.utc).isoformat()
        "snapshot_date": datetime.utcnow().isoformat()
    }
