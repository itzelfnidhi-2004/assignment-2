# extract_events.py
# Usage:
#   python extract_events.py

import json, os

IN_FILE = "protocols_with_abis.json"
OUT_FILE = "protocols_with_events.json"

def format_event(entry):
    """entry is an ABI item of type 'event'"""
    name = entry.get("name", "")
    inputs = entry.get("inputs", []) or []
    parts = []
    for inp in inputs:
        in_name = inp.get("name", "")
        in_type = inp.get("type", "")
        if in_name:
            parts.append(f"{in_name} {in_type}")
        else:
            parts.append(in_type)
    return f"{name}({', '.join(parts)})"

def main():
    if not os.path.exists(IN_FILE):
        print("Missing", IN_FILE)
        return

    with open(IN_FILE, encoding="utf-8") as f:
        items = json.load(f)

    out = []
    for item in items:
        abi = item.get("abi")
        events = []
        if isinstance(abi, list):
            for entry in abi:
                if entry.get("type") == "event":
                    events.append(format_event(entry))
        out.append({
            "protocol": item.get("protocol"),
            "network": item.get("network"),
            "contract_address": item.get("contract_address"),
            "contract_name": item.get("contract_name"), 
            "verified": bool(item.get("verified")),
            "events": events
        })

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    print(" Saved", OUT_FILE, "with", len(out), "rows")

if __name__ == "__main__":
    main()
