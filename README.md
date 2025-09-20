Ethereum Protocols Demo - Assignment 2

Assignment Roadmap:

Phase 1 – Fetch addresses
Input: protocols.csv
Script: fetch_addresses_v2.py
Output: protocols_with_addresses.json

Phase 2 – Fetch ABIs + contract names
Input: protocols_with_addresses.json
Script: fetch_abis.py
Output: protocols_with_abis.json

Phase 3 – Extract events
Input: protocols_with_abis.json
Script: extract_events.py
Output: protocols_with_events.json


How to run:
1. Make sure Python is installed.
2. Place protocols.csv in the same folder as the scripts.
3. Run the scripts in order:
   python fetch_addresses_v2.py
   python fetch_abis.py
   python extract_events.py

Files included:
- protocols.csv
- fetch_addresses_v2.py
- fetch_abis.py
- extract_events.py
- protocols_with_addresses.json
- protocols_with_abis.json
- protocols_with_events.json
