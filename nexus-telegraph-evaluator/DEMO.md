# NEXUS Telegraph Evaluator — accessible technical demo (Season II)

**Submitted by:** Tomasz Czuba, with AI assistance from NEXUS/GPT-6  
**Track:** Evaluators  
**Intent:** `ONCHAIN_METRIC_VERIFY_GENERAL`  
**Network:** Telegraph/Anjoman Sepolia evaluation pool; queried source data is Ethereum **mainnet** history  
**Status:** Three contributed rows were `admitted` and later confirmed `eligible` at epoch 2077, and public readback proves this. No hackathon prize, registration confirmation or final-entry receipt is claimed.

This is a reproducible **accessible alternative to a 2–5 minute demonstration**: it shows an input, verified result, the exact Telegraph integration receipt, and a failure case. No personal keys, logins or capital required.

## 1. The factual on-chain input

- **Intent:** `ONCHAIN_METRIC_VERIFY_GENERAL`
- **Ethereum address:** `0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045`
- **Historical block:** `20000000`
- **Metric:** native `balance`, returned as Gwei.
- **Ground truth:** `495394228822711118729` wei = `495394228822.711118729` Gwei; the six-decimal test answer is `495394228822.711119` Gwei.
- **Sources:** read-only Flashbots JSON-RPC `eth_getBalance` at hexadecimal block `0x1312d00`, and Blockscout's historic balance endpoint with decimal `block_number=20000000` (the most recent balance event at or before that height).

[Open the public Blockscout evidence](https://eth.blockscout.com/api/v2/addresses/0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045/coin-balance-history?block_number=20000000).

## 2. The adversarial comparison

See `data/evaluation_pairs_v1.jsonl` for the exact submitted JSONL (SHA-256 `b33c15048a692b3096b435fc9a199e1d64ec62fa860da16bc49e1cc109a47c46`).

The **correct** answer states `495394228822.711119 Gwei`. The intentionally **wrong** answer states a balance 30% smaller. Both answers explicitly name the address, block and units; this tests whether a model verifies on-chain evidence instead of choosing a plausible-looking figure.

The second example uses another Ethereum address at block `20500000`; the third uses the same first address at a different block `19500000`. All three passed independent readback before submission. Data values must **never** be replaced by current balances.

## 3. Telegraph integration — actual network receipt

The contributor signed the SHA-256 of the 3-row JSONL body using **EIP-191** (off-chain message). A single `POST /api/evalpool/submissions` to the Telegraph development network returned:

```json
{
  "intent_id": "ONCHAIN_METRIC_VERIFY_GENERAL",
  "signed": true,
  "received": 3,
  "accepted": 3,
  "duplicate": 0,
  "rejected": 0,
  "curated": 3
}
```

The independent GET readback reports **three `admitted` rows with `attested` provenance**. Their hashes and timestamps are in `evidence/pool_readback.json`.

[Verify the result directly on Telegraph](https://devnode.telegraphprotocol.com/api/evalpool/submissions/mine?submitter=0xC62cA7cC2d30b88F144E1adF20c9a363818B759f&intent_id=ONCHAIN_METRIC_VERIFY_GENERAL). This is public, read-only; no account is necessary.

[Check pool status](https://devnode.telegraphprotocol.com/api/evalpool/status?intent_id=ONCHAIN_METRIC_VERIFY_GENERAL). At initial submission: **5 total contributors, 4 `eligible`**. The subsequent node readback at epoch **2077** shows **5 total contributors, all 5 `eligible`**, meeting the minimum, and all three of our rows `eligible`. The JSON receipt is in `evidence/official_eligible_receipt.json`.

## 4. Reproduce fail-closed code tests

Run from this project's root directory (inside the `nexus-telegraph-evaluator` folder), using Python 3.12+ and Node.js:

```bash
python3 -m unittest discover -s tests -p 'test_verifier.py' -v
node tests/test_comparator.mjs
```

Expected: **9 Python tests PASS** and **4865 WASM test cases PASS**. These exact commands have been run against the **public GitHub branch** and passed.

A case is `UNVERIFIED` when one of the independent providers returns a different block hash, a different balance or an error. `evaluate_claim` then returns `ABSTAIN`, not an invented score. An invalid numeric claim also fails.

## 5. Honest limitations

- `admitted` is not the same as `eligible`, but the official node has since independently confirmed `eligible` for all three rows; that does not establish ranking impact or a competition win.
- Public archival Ethereum RPCs prune state or rate-limit queries, so not all old blocks can be independently checked at any moment.
- The confirmed dataset is **3 small cases**, not a representative benchmark proving overall model quality or economic impact.
- This package does not claim live ranking improvement, paid demand, external adoption, a mainnet deployment, contest acceptance or income.
- The optional `comparator.c` reproduces the network's existing deterministic reference rule; not a unique novel scoring algorithm.
- This dataset does **not** expose secret evaluation material or pretend to have independent customers.

**No gas, crypto trading, deposit, paid API or modification of the author's production Tradebot/BRAIN was involved.**
