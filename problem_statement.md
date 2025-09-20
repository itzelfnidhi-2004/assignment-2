# 📌 Problem Statement: Collecting Protocol Contracts & Events

### 🎯 Goal

We want to build a dataset of **DeFi protocols → their smart contracts → and the events those contracts emit**.
This work is about **data collection and structuring**, not blockchain coding.

---

## 🚦 Phased Plan

### **Phase 1: Collect All Contract Addresses**

* For every **protocol + blockchain network** pair (from the CSV we already have):

  * Search for all **contract addresses** used by that protocol on that chain.
  * A protocol may have **multiple contracts per chain** (e.g., lending pools, token vaults). Collect them all.
* Most protocols list all their contract addresses in their docs, you can scrape this, or build agent to do this, or you can do it manually.
* Output should look like:

| protocol | network  | contract\_address |
| -------- | -------- | ----------------- |
| aave     | ethereum | 0x3dfd…abcd       |
| aave     | ethereum | 0x91c2…ef12       |
| sushi    | polygon  | 0x7ba9…f891       |

---

### **Phase 2: Fetch Contract ABIs**

* For each contract address you found:

  * Use the block explorer to check if the contract is **verified**.
  * If verified, download its **ABI** (Application Binary Interface).

    * The ABI is a JSON file describing the contract’s functions and events.
* Save each ABI alongside its contract address.

---

### **Phase 3: Extract Events from ABI**

* From each ABI, ignore everything except **events**.
* Events are like “log messages” a contract emits.
* Each event has:

  * **Name** (e.g., `Swap`)
  * **Arguments** (name + type, e.g., `token0 address, token1 address, amount uint256`)
* For each contract, build a list of its events in this format:

```
swap(token0 address, token1 address, amount uint256)
deposit(user address, amount uint256)
borrow(borrower address, amount uint256, rate uint256)
```

---

### ✅ Final Output

A structured dataset (JSON) with rows like:

| protocol | network  | contract\_address | verified | events                                                             |
| -------- | -------- | ----------------- | -------- | ------------------------------------------------------------------ |
| aave     | ethereum | 0x3dfd…abcd       | yes      | deposit(user address, amount uint256), borrow(borrower address, …) |
| uniswap  | arbitrum | 0x9c1a…ef12       | yes      | swap(token0 address, token1 address, amount uint256)               |
| sushi    | polygon  | 0x7ba9…f891       | no       | —                                                                  |

---

### 🧰 Tools You’ll Need

* **CSV from DeFiLlama** → starting point.
* **Block explorers** (Etherscan, BscScan, Arbiscan, etc.) for abis.
* **Explorer APIs** (to fetch ABIs programmatically if needed).

---

### 📌 Key Notes

* A single protocol may have **dozens of contracts per chain**. Collect them all.
* Only **verified contracts** have readable ABIs (and thus events).
* We only care about **events**, not contract functions.
* Output should stay consistent across all protocols.
