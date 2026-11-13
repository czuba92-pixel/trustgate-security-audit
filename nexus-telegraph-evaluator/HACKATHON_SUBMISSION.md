# Telegraph Hackathon Season II — evaluator entry pack (DRAFT, not submitted)

**November 13 feasibility audit (read-only):** [cross-chain archival API evidence and no-go verdict](evidence/H2_API_GAP_20261113.md). None of the tested no-key providers met the full historical-input coverage and acceptance requirement. This is not proof of global impossibility, and no further upload was performed. Until official validator and usable source evidence exists, treat #87 as **blocked**, not delivered. The Issue's own bounty is explicitly **unfunded**.

## Critical correction — authoritative issue #87 changed 2026-11-13 14:12 UTC

**Do not claim this repository currently completes issue #87 or is a qualifying H2 Evaluators delivery.** The authoritative [current issue #87](https://github.com/telegraphprotocol/bounties/issues/87) now calls for keyless public-API `truth_source` evaluation material for the **deterministic** intent `ONCHAIN_METRIC_VERIFY_GENERAL`. It explicitly states **do not build a comparator/scoring module** for this intent. The earlier three `eligible` `preference_pair` rows remain real node receipts, but they **do not fulfill the currently required deliverable**; the legacy WASM comparator is unrelated to what #87 presently accepts. Another public claimant with 241 eligible preference-pair rows reached the same conclusion in [their updated progress comment](https://github.com/telegraphprotocol/bounties/issues/87#issuecomment-6855425266).

The v1 signed truth-source upload was **rejected** (`source_unparseable`). Neither v2 nor v3 has ever received an independent network-eligibility verdict. Local `19/19 PASS` checked only the assertions we wrote, **not** the official Telegraph miner YAML validator, end-to-end routing, or accurate scoring over the intent's entire input domain. The proposed Blockscout source supports only an Ethereum native-balance subset and its custom header assumptions are **not proven to enforce chain/metric restrictions in the network**. Thus v3 is a research artifact, not a production-ready fix.

The advertised public no-fee YAML validation APIs returned **HTML** (`integrate.telegraphprotocol.com/api/validate`) and **HTTP 405** (`anjoman.ai/dashboard/validate`) during this read-only audit; neither supplied a schema verdict. Do not send another signed row until an independently supported validator or official error details prove the fix and its actual input/output behavior.

**Administrative gates still open:** The issue has a public `/claim` comment from `czuba92-pixel` but no observed bot acceptance or `/submit` from this account; the GitHub connector's write to the organizer repo returned HTTP 403. The H2 final entry has not been confirmed and the organizer email has not received a reply as of the audit. No cash or prize has been awarded. **Reward for issue #87 itself: unfunded.**



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

## Latest official readback — November 13, 2026

The original contributor wallet `0xC62cA7cC2d30b88F144E1adF20c9a363818B759f` was checked again against the [live Sepolia evalpool readback](https://devnode.telegraphprotocol.com/api/evalpool/submissions/mine?submitter=0xC62cA7cC2d30b88F144E1adF20c9a363818B759f&intent_id=ONCHAIN_METRIC_VERIFY_GENERAL): exactly **three** previously submitted `preference_pair` rows still show `eligible` and `attested`, with hashes `77ced07c4fb25e2b24b6326abdd0a2e7df0e84ce0cdf1672d72d6173913a3503`, `00654a2c349d2ca512d02ef845de73bf932f2b7e9b77b4b7db8063ef1ac493f4`, and `3981307a553c9830ff6b8666ea9a0bee90e882e66d813f7e2438deefe3cecd5f`. These accepted rows are a different record kind from the **unaccepted** deterministic v1/v2/v3 truth-source work.

## Current validation work — November 13, 2026 (v3, NOT submitted)

The authoritative Anjoman documentation explicitly supports both YAML as a string and JSON-object `source` rows. Therefore changing v1 to a JSON object (v2) alone **cannot be treated as a validated fix** for `source_unparseable`.

A deliberately reduced v3 candidate is available in [YAML](data/truth_source_eth_balance_v3.yaml) and an unsigned [JSONL row](data/truth_source_eth_balance_v3.jsonl). It keeps only documented miner fields, preserves a pinned-block query, and restricts input to Ethereum-mainnet balance queries. A fresh **independent read-only test run** downloaded the three published GitHub files by SHA and ran `python3 -m unittest discover -s tests -p 'test_truth_source_v3.py' -v`: **19/19 PASS, 0 failures**, on November 13. Source SHA256: `a9d9621356fea979b70e3262ac1c0fbe822b9ed8de37c625a980d1c2570de5c9`; unsigned JSONL SHA256: `d35cb12bf3ea1d76727eb69989c1e175b9dc24f12b76f3c03626e1dfaf258bc5`. No signing key is committed.

**Critical limitation:** the v3 tests are local fixture/schema-contract checks, not a Telegraph-node schema acceptance; `truth_source` v3 is **not eligible**, and has **not been signed or uploaded**. API reliability, particularly Blockscout's historical response latency, must also be examined before claiming network usefulness. The previous v1 upload remains `rejected/source_unparseable`; do not confuse its HTTP-200 storage receipt with eligibility.

A support request was sent on November 13 to `info@telegraphprotocol.com` via the participant's authorized email, subject `H2 Evaluators #87 — truth_source source_unparseable and final submission link`, asking for detailed source validation and the final H2 submission route for an already registered participant. No reply or completion is claimed.

**No further authenticated write or pool retry** should occur without resolving the specific schema gate and reconciling wallet contributor attribution. No Tradebot/BRAIN modifications or blockchain transactions are part of this activity.

## Current technical verdict — November 13, 2026 (new evidence)

The official Sepolia evalpool API returned **HTTP 200 / signed=true / accepted=1** for the first `truth_source` upload, but its **independent readback rejected the stored row**: `status: rejected`, `reason_code: source_unparseable`. Receipt: [v1 readback](https://devnode.telegraphprotocol.com/api/evalpool/submissions/mine?submitter=0x43cF97c1Bc280f4fa9cE7Be08E50E7919Ccc05F5&intent_id=ONCHAIN_METRIC_VERIFY_GENERAL); row hash `c4dc036072b8027da2d90666bfe2607240b092a9811274a91e03c2458a81981c`. **The upload is not accepted evaluation material.** This test attempt used a separate, purpose-limited contributor address (`0x43cF97c1Bc280f4fa9cE7Be08E50E7919Ccc05F5`), **not** the original 3-row contributor address (`0xC62cA7cC2d30b88F144E1adF20c9a363818B759f`). Until linked or confirmed by organizers, do not treat the separate address as credited to the registered hackathon participant.

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
