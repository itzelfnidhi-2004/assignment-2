# fetch_addresses_v2.py
# Usage examples:
#   python fetch_addresses_v2.py            # default: process all
#   python fetch_addresses_v2.py --limit 10 # only first 10 protocols (good for testing)
#   python fetch_addresses_v2.py --start 20 --limit 10

import argparse, csv, json, os, re, requests, sys, time
from typing import Any

CSV_FILE = "protocols.csv"
OUT_FILE = "protocols_with_addresses.json"
LLAMA_PROTOCOL_URL = "https://api.llama.fi/protocol/{}"
LLAMA_ALL_CONTRACTS = "https://api.llama.fi/contracts"

ADDRESS_RE = re.compile(r"0x[a-fA-F0-9]{40}")

def is_address(s: str) -> bool:
    return bool(ADDRESS_RE.fullmatch(s))

def find_addresses_in_obj(obj: Any):
    """Recursively find any 0x... addresses inside obj (dict/list/str)."""
    found = set()
    if isinstance(obj, str):
        for m in ADDRESS_RE.findall(obj):
            found.add(m)
    elif isinstance(obj, dict):
        for v in obj.values():
            found |= find_addresses_in_obj(v)
    elif isinstance(obj, list):
        for item in obj:
            found |= find_addresses_in_obj(item)
    return found

def get_addresses_from_protocol_api(slug: str, chain: str):
    """Try the per-protocol llama endpoint and look for 'contracts' / 'addresses' fields."""
    url = LLAMA_PROTOCOL_URL.format(slug)
    try:
        r = requests.get(url, timeout=15)
        if r.status_code != 200:
            return set()
        data = r.json()
    except Exception as e:
        print("error", slug, chain, e)
        return set()

    results = set()
    # common place: "contracts": [ { "chain": "Ethereum", "address": "0x..." }, ... ]
    if isinstance(data, dict):
        if "contracts" in data:
            for c in data["contracts"] or []:
                addr = c.get("address") if isinstance(c, dict) else None
                if addr and is_address(addr):
                    if chain.lower() in ("abstract", "") or c.get("chain","").lower() == chain.lower():
                        results.add(addr)
        # sometimes "addresses" is a mapping
        if "addresses" in data and isinstance(data["addresses"], dict):
            for ch_name, addrs in data["addresses"].items():
                if chain.lower() == "abstract" or ch_name.lower() == chain.lower():
                    for a in addrs or []:
                        if isinstance(a, str) and is_address(a):
                            results.add(a)
        # as last resort, search entire object for addresses (will pick up TVL tokens — but these are addresses too)
        results |= find_addresses_in_obj(data)
    return results

_cached_llama_contracts = None
def get_addresses_from_llama_contracts(slug: str, chain: str):
    """Fallback: download the big /contracts list once and search entries heuristically."""
    global _cached_llama_contracts
    if _cached_llama_contracts is None:
        try:
            r = requests.get(LLAMA_ALL_CONTRACTS, timeout=30)
            _cached_llama_contracts = r.json()
        except Exception as e:
            print("error fetching llama contracts list:", e)
            _cached_llama_contracts = []

    results = set()
    for item in _cached_llama_contracts:
        # item is likely a dict; try common keys
        try:
            # fields that might identify the project: 'project', 'protocol', 'name', 'slug'
            project_names = []
            for k in ("project", "protocol", "name", "slug"):
                v = item.get(k) if isinstance(item, dict) else None
                if isinstance(v, str):
                    project_names.append(v.lower())

            matched = any(slug.lower() == pn or slug.lower() in pn for pn in project_names)
            if not matched:
                # sometimes there is a nested 'project' object or 'protocol' string; also check addresses fields generically
                # also try other fields for a crude match
                for v in item.values() if isinstance(item, dict) else []:
                    if isinstance(v, str) and slug.lower() in v.lower():
                        matched = True
                        break

            if not matched:
                continue

            # chain filtering: item.get("chain") or item.get("network")
            item_chain = (item.get("chain") or item.get("network") or "").lower() if isinstance(item, dict) else ""
            if chain.lower() != "abstract" and item_chain and chain.lower() != item_chain:
                continue

            # find any addresses inside the item
            results |= find_addresses_in_obj(item)
        except Exception:
            continue

    return results

def get_addresses(protocol: str, chain: str):
    # try slug directly
    addrs = set()
    addrs |= get_addresses_from_protocol_api(protocol, chain)
    if addrs:
        # filter out non checksummed lower-case addresses (leave as-is; can normalize later)
        return sorted(addrs)
    # fallback to master contracts list
    addrs |= get_addresses_from_llama_contracts(protocol, chain)
    return sorted(addrs)

def main(limit=None, start=0):
    if not os.path.exists(CSV_FILE):
        print("Missing", CSV_FILE)
        sys.exit(1)

    results = []
    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print("CSV headers:", reader.fieldnames, "| total rows:", len(rows))
    rows_to_process = rows[start: None if limit is None else start + limit]

    for idx, row in enumerate(rows_to_process, start=start):
        slug = (row.get("protocol") or "").strip()
        chain = (row.get("network") or "").strip()
        if not slug:
            continue
        print(f"[{idx+1}/{len(rows)}] {slug} on {chain} ...", end=" ")
        addrs = get_addresses(slug, chain)
        if not addrs:
            print(" No addresses found")
        else:
            print(f" Found {len(addrs)} addresses")
            for a in addrs:
                results.append({
                    "protocol": slug,
                    "network": chain,
                    "contract_address": a
                })
        # be kind to the API
        time.sleep(0.2)

    print("Writing", OUT_FILE, "...")
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print("Saved", OUT_FILE, "with", len(results), "entries")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="Process only first N rows (for testing)")
    ap.add_argument("--start", type=int, default=0, help="Start row index (0-based)")
    args = ap.parse_args()
    main(limit=args.limit, start=args.start)
