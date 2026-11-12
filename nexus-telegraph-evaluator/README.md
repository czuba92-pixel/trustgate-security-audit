# NEXUS On-chain Integrity Evaluator — Telegraph Season II

**Track:** Evaluators · **Intent:** `ONCHAIN_METRIC_VERIFY_GENERAL` · **Issue:** [Telegraph #87](https://github.com/telegraphprotocol/bounties/issues/87)

**Status verified on November 12, 2026:** Three independently corroborated Ethereum balance evaluation pairs were submitted through the official Sepolia evaluation-pool API using an EIP-191 message signature. The node returned **HTTP 200, signed=true, received=3, accepted=3, rejected=0**. The independent readback returned all three rows as **`admitted`** with **`attested`** provenance; **`eligible` is not yet confirmed** (requires subsequent pool freeze). The pool has 5 total contributors, 4 eligible contributors as of epoch 2076. The three case hashes are recorded in `evidence/pool_readback.json`.

**Public contributor address:** `0xC62cA7cC2d30b88F144E1adF20c9a363818B759f`. Only an off-chain EIP-191 signature was used. No deposits, gas, real trades, payments, or interaction with Tradebot/BRAIN production occurred. No private keys are included in this branch.

## What the project contributes

- `data/evaluation_pairs_v1.jsonl`: three original real-data test questions, grounded correct Gwei answers and deliberately incorrect alternatives. Dates and on-chain heights are explicit; all rows point to public Blockscout evidence.
- `evidence/evaluation_pairs_evidence.json`: real block numbers, chain addresses, exact wei values, verified six-decimal Gwei values and source URLs. The sampled values were cross-checked with Flashbots and Blockscout. Network acceptance is not the same as later use for ranking.
- `src/submit_evaluation.py`: one-shot example of exact-body SHA256 + EIP-191 signing, `/api/evalpool/submissions` POST, idempotency ledger, and public pool readback. **Do not run without configuring a separate, purpose-limited contributor key and producing your own data.** Never publish a private key.
- `src/build_dataset_batch.py`: research source for attempting to collect independent historical balance pairs using public RPCs and Blockscout, with fail-closed filtering. Older remote nodes can prune archival state and APIs can rate-limit; do not treat unverified candidates as facts.
- `src/comparator.c` and `build/nexus_comparator.wasm.base64`: separate deterministic WASM score comparator and reproducible compiled artifact, following [Telegraph comparator ABI](https://anjoman.ai/docs/scoring/build-a-scoring-module). These are **local research artifacts only**, not registered on-chain. They did not cause the three evaluation-pool admissions.

## Reproduce the public evidence

Run `python3 -m json.tool evidence/evaluation_pairs_evidence.json`; open each `source_url` (Blockscout's historical balance API), check that the first item at/before the pinned block has the stated wei value, divide by 1e9 for Gwei and round to six decimal places. Compare each answer in `data/evaluation_pairs_v1.jsonl` with the corroborated number. The wrong answer intentionally differs by 30% to make the error meaningful.

Official readback (no authentication):

`https://devnode.telegraphprotocol.com/api/evalpool/submissions/mine?submitter=0xC62cA7cC2d30b88F144E1adF20c9a363818B759f&intent_id=ONCHAIN_METRIC_VERIFY_GENERAL`

Pool status:

`https://devnode.telegraphprotocol.com/api/evalpool/status?intent_id=ONCHAIN_METRIC_VERIFY_GENERAL`

To rebuild the optional WASM comparator, install Clang with wasm32 support:

```bash
clang --target=wasm32-unknown-unknown -Oz -fno-builtin -nostdlib \
  -Wl,--no-entry -Wl,--export-memory -Wl,--export=imw_score_deterministic \
  -Wl,--export=imw_alloc -Wl,--export=imw_free -Wl,--strip-all \
  -Wl,--initial-memory=131072 -o nexus_comparator.wasm src/comparator.c
```

The WASM binary is also distributed as **base64 text** in `build/nexus_comparator.wasm.base64` for portability; decode it with `base64 -d`.

## Limits and integrity

This is an **experimental testnet contribution**. An `admitted` row is not `eligible`; eligibility, evaluator canonical registration, ranking impact and hackathon prize status require independent confirmations. Historical archive providers may return HTTP 429/410, pruned-state errors or timeout; failures must not be replaced with current balances. It works only with **Ethereum native ETH balance at explicit historical blocks**, not every EVM chain or `tx_count`. The comparator follows the network's existing reference rule; it is not a claim of a novel scoring algorithm.

The user's earlier Tradebot work informed the **methodology** (independent evidence, fail-closed claims, adversarial checks). Source files here are original independent work, not a change to Tradebot/BRAIN.

**Free GitHub Issue #87 is explicitly unfunded.** Cash prizes are competitive and separate, under [Season II rules](https://hackathon.telegraphprotocol.com/rules). No prize or eligibility is implied by this contribution.

Maintainer/participant: Tomasz Czuba · AI assistance: NEXUS / GPT-6.
