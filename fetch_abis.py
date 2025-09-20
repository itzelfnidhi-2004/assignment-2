# fetch_abis.py
# Usage:
#   python fetch_abis.py
#   python fetch_abis.py --start 0 --limit 100

import argparse, json, os, time, requests
from dotenv import load_dotenv

load_dotenv()

IN_FILE = "protocols_with_addresses.json"
OUT_FILE = "protocols_with_abis.json"

# Map chain (your CSV) => (env key name, api base)
CHAIN_APIS = {
    "ethereum":   ("ETHERSCAN_API_KEY", "https://api.etherscan.io/api"),
    "polygon":    ("POLYGONSCAN_API_KEY", "https://api.polygonscan.com/api"),
    "bsc":        ("BSCSCAN_API_KEY", "https://api.bscscan.com/api"),
    "arbitrum":   ("ARBISCAN_API_KEY", "https://api.arbiscan.io/api"),
    "optimism":   ("OPTIMISMSCAN_API_KEY", "https://api-optimistic.etherscan.io/api"),
    "avalanche":  ("SNOWTRACE_API_KEY", "https://api.snowtrace.io/api"),
    "fantom":     ("FTMSCAN_API_KEY", "https://api.ftmscan.com/api")
    # add more as needed
}

def get_api_info(chain):
    info = CHAIN_APIS.get(chain.lower())
    if not info:
        return None, None
    keyname, base = info
    return os.getenv(keyname), base

def fetch_abi_and_name(address, chain):
    """Fetch ABI and contract name for a given address+chain"""
    api_key, base = get_api_info(chain)
    if not base:
        return None, None

    abi, name = None, None

    # 1) Fetch ABI
    abi_url = f"{base}?module=contract&action=getabi&address={address}&apikey={api_key or ''}"
    try:
        r = requests.get(abi_url, timeout=15).json()
        if isinstance(r, dict) and r.get("status") == "1":
            abi = json.loads(r["result"])
    except Exception:
        pass

    # 2) Fetch contract name
    name_url = f"{base}?module=contract&action=getsourcecode&address={address}&apikey={api_key or ''}"
    try:
        r = requests.get(name_url, timeout=15).json()
        if isinstance(r, dict) and r.get("status") == "1":
            results = r.get("result") or []
            if results and isinstance(results, list):
                name = results[0].get("ContractName") or None
    except Exception:
        pass

    return abi, name

def main(start=0, limit=None):
    if not os.path.exists(IN_FILE):
        print("Missing", IN_FILE)
        return

    with open(IN_FILE, encoding="utf-8") as f:
        items = json.load(f)

    total = len(items)
    end = None if limit is None else min(total, start + limit)
    slice_items = items[start:end]

    out = []
    for i, item in enumerate(slice_items, start=start):
        protocol = item.get("protocol")
        chain = item.get("network")
        addr = item.get("contract_address")
        print(f"[{i+1}/{total}]  {protocol} ({chain}) -> {addr}")

        abi, name = fetch_abi_and_name(addr, chain)
        if abi:
            print(f" ABI found | Contract: {name or 'Unknown'}")
        else:
            print(" No ABI (not verified or unsupported)")

        out.append({
            **item,
            "contract_name": name,
            "verified": bool(abi),
            "abi": abi
        })
        time.sleep(0.25)

    # merge with existing file if present
    existing = {}
    if os.path.exists(OUT_FILE):
        try:
            with open(OUT_FILE, encoding="utf-8") as f:
                for e in json.load(f):
                    existing[(e["protocol"], e["network"], e["contract_address"])] = e
        except Exception:
            existing = {}

    for rec in out:
        key = (rec["protocol"], rec["network"], rec["contract_address"])
        existing[key] = rec

    merged = list(existing.values())
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2)

    print(" Saved", OUT_FILE, "with", len(merged), "entries total")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    main(start=args.start, limit=args.limit)
