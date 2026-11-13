# Telegraph Hackathon Season II — evaluator entry pack (DRAFT, not submitted)

**Prepared:** 2026-11-13  
**Entry status:** Draft for final H2 website submission. No organizer acceptance or prize is implied.

## Project details (copy into official entry form)

- **Project:** NEXUS On-chain Integrity Evaluator
- **Track:** Evaluators
- **Intent:** `ONCHAIN_METRIC_VERIFY_GENERAL` (family: `ONCHAIN_METRIC_VERIFY`)
- **Contributor GitHub:** `czuba92-pixel`
- **Public contributor address:** `0xC62cA7cC2d30b88F144E1adF20c9a363818B759f`
- **Source and reviewer access:** https://github.com/czuba92-pixel/trustgate-security-audit/tree/nexus-telegraph-evaluator-20261112/nexus-telegraph-evaluator
- **Accessible technical demonstration:** [DEMO.md](DEMO.md)
- **Run/reproducibility instructions:** [README.md](README.md)
- **Associated public issue:** https://github.com/telegraphprotocol/bounties/issues/87

## Short public description

NEXUS On-chain Integrity Evaluator is a reproducible, evidence-first experiment for checking factual on-chain metrics. We independently corroborated three historical Ethereum native-balance cases using public sources, then uploaded three signed evaluation answer pairs to Telegraph's Sepolia evaluation pool. The official node accepted all three and a readback on 2026-11-12 at 23:56 UTC reported each row as `eligible` with attested provenance. The repository includes original source data, the signed-upload client, a read-only receipt, failure-handling tests, and an optional deterministic WASM comparator prototype. It does **not** claim a live registered scoring module, ranking improvement, mainnet activity, paying users, or a prize.

## Accessible demo equivalent (2–5 minute review)

1. Open [DEMO.md](DEMO.md) and review the pinned Ethereum address, block, and wei-to-Gwei computation.
2. Compare the correct answer to the intentionally altered answer in [evaluation_pairs_v1.jsonl](data/evaluation_pairs_v1.jsonl).
3. Review [official_eligible_receipt.json](evidence/official_eligible_receipt.json) and, if reachable, the [official readback API](https://devnode.telegraphprotocol.com/api/evalpool/submissions/mine?submitter=0xC62cA7cC2d30b88F144E1adF20c9a363818B759f&intent_id=ONCHAIN_METRIC_VERIFY_GENERAL).
4. Run the local verification and comparator tests per [DEMO.md](DEMO.md). Test that absent or inconsistent historical source data causes abstention rather than a fabricated answer.

The README and DEMO provide detailed prerequisites, expected outcomes, limitations, and public evidence. These tests were reported as passing during preparation; this entry pack does not assert a new test run.

## Current technical verdict — November 13, 2026 (new evidence)

The official Sepolia evalpool API returned **HTTP 200 / signed=true / accepted=1** for the first `truth_source` upload, but its **independent readback rejected the stored row**: `status: rejected`, `reason_code: source_unparseable`. Receipt: [v1 readback](https://devnode.telegraphprotocol.com/api/evalpool/submissions/mine?submitter=0x43cF97c1Bc280f4fa9cE7Be08E50E7919Ccc05F5&intent_id=ONCHAIN_METRIC_VERIFY_GENERAL); row hash `c4dc036072b8027da2d90666bfe2607240b092a9811274a91e03c2458a81981c`. **The upload is not accepted evaluation material.**

A [second candidate (v2)](data/truth_source_eth_balance_v2.jsonl) uses the separately documented JSON-object `source` representation instead of YAML as a JSON string. It is a **local/publicly published candidate only, not posted to the node**: the follow-up tool execution was blocked. Do not claim eligibility or retry blindly. Historical balance source checks succeeded at pinned Ethereum blocks 20,000,000 and 19,500,000. That tests the upstream data, not the Telegraph miner schema.

The authenticated final H2 project submission is also **not verified**; user confirmed account registration only. By public GitHub account data, the `czuba92-pixel` account has **already starred** the `telegraphprotocol/bounties` repository. GitHub connector could not post issue comments (HTTP 403). Existing `/claim` is visible, but an organizer/bot acceptance receipt for this claim is still not recorded.

**Current next actions:** independently validate a conforming truth-source schema without blindly posting further rows; obtain an eligible network receipt, post truthful `/submit` on issue #87 if permitted, and submit the separate H2 project in an authenticated session.

## Important compliance gap discovered on November 13

**Do not send this draft as a claim of completed issue #87 or qualifying H2 evaluator delivery without resolving this gap.** The current [issue #87](https://github.com/telegraphprotocol/bounties/issues/87) and [Anjoman contribution docs](https://anjoman.ai/docs/scoring/contribute-evaluation-data) describe `ONCHAIN_METRIC_VERIFY_GENERAL` as **deterministic**, requesting a working keyless public API **truth source**, uploaded as a row with `label_kind: truth_source` and a miner-style `source` YAML/JSON (or a comparator registered and passing the network checks). The three proven `eligible` records in this repository are **preference pairs**, not truth sources. Technical row eligibility by itself does not establish that the material meets the updated task or is used for ranking. Our WASM module is **not** registered. The advertised `5/5 eligible contributors` pertains to the readback at that epoch and does not replace the truth-source requirement.

Next technical step: build and independently validate a conforming public, no-key truth source that genuinely answers this Intent, upload with a fresh purpose-limited EIP-191 signature, verify the status of that **new** row, and only then describe it as the issue contribution in `/submit`.

## Competition submission gate

- [x] GitHub code, reproducible guide, accessible demo and archived testnet readback published.
- [x] Three historic `preference_pair` evaluation rows previously reported `eligible`.
- [ ] Conforming deterministic `truth_source` or registered, network-accepted comparator (not yet done).
- [x] GitHub **Star** on https://github.com/telegraphprotocol/bounties verified for `czuba92-pixel` (public starred-repositories API).
- [ ] Final project entry sent through https://hackathon.telegraphprotocol.com/ (requires signed-in contestant session).
- [ ] Official final-entry receipt retained.

**Deadline:** 2026-12-01 23:59 UTC. H2 prizes are competitive, not guaranteed; issue #87 itself is unfunded. Do not disclose keys, commit secrets, spend gas or imply Tradebot/BRAIN production involvement.
