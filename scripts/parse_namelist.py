import re

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
                        print("YEAH?")
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

    return {
        "run_name": atm_in_path.split("/")[-2],  # or however you define it
        "nudging": len(nudge_vars) > 0,
        "nudged_vars": nudge_vars,
        "cosp": len(cosp_vars) > 0,
        "cosp_vars": cosp_vars,
        "fincl": fincl_dict,
        "empty_htapes": empty_htapes,
        "other_vars": other_vars
    }
