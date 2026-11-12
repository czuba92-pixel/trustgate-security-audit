#!/usr/bin/env python3
"""NEXUS independent on-chain answer verifier for Telegraph H2 Evaluators.

Read-only Ethereum mainnet public RPC; no private keys, transfers, or Tradebot.
It reports VERIFIED only when >=2 independent providers agree at the exact
requested block height and block hash. Any missing fact fails closed.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal, InvalidOperation
from typing import Callable, Any

INTENT = "ONCHAIN_METRIC_VERIFY_GENERAL"
CHAIN_ID = "0x1"
ALLOWED_RPC = {
    "1rpc": "https://1rpc.io/eth",
    "flashbots": "https://rpc.flashbots.net",
    "drpc": "https://eth.drpc.org",
}
ADDRESS = re.compile(r"^0x[a-fA-F0-9]{40}$")
HASH = re.compile(r"^0x[a-fA-F0-9]{64}$")
HEX = re.compile(r"^0x[0-9a-fA-F]+$")
DEMO_ADDRESS = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
DEMO_BLOCK = 20_000_000

class VerificationError(Exception):
    """Public-data validation failed. Do not score as a success."""


def jsonrpc(url: str, method: str, params: list[Any]) -> Any:
    if url not in ALLOWED_RPC.values():
        raise VerificationError("RPC endpoint is not allowlisted")
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}, separators=(",", ":")).encode()
    req = urllib.request.Request(url, data=body, method="POST", headers={
        "Content-Type": "application/json", "Accept": "application/json",
        "User-Agent": "NEXUS-Telegraph-Evaluator/0.1",
    })
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            if response.status != 200:
                raise VerificationError(f"upstream HTTP {response.status}")
            payload = response.read(128_001)
            if len(payload) > 128_000:
                raise VerificationError("oversized JSON-RPC result")
            obj = json.loads(payload)
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise VerificationError(f"RPC transport/parse failure: {type(exc).__name__}") from exc
    if not isinstance(obj, dict) or obj.get("jsonrpc") != "2.0" or obj.get("id") != 1:
        raise VerificationError("invalid JSON-RPC envelope")
    if "error" in obj or "result" not in obj:
        raise VerificationError("RPC returned error or no result")
    return obj["result"]


def as_hex_int(raw: Any, *, name: str) -> int:
    if not isinstance(raw, str) or not HEX.fullmatch(raw):
        raise VerificationError(f"malformed {name}: expected 0x hexadecimal")
    value = int(raw, 16)
    if value < 0 or value > (1 << 256) - 1:
        raise VerificationError(f"invalid {name} range")
    return value


def verify_one_provider(name: str, address: str, block: int, metric: str = "balance",
                        transport: Callable[[str, str, list[Any]], Any] = jsonrpc) -> dict:
    if name not in ALLOWED_RPC:
        raise VerificationError("unknown provider")
    endpoint = ALLOWED_RPC[name]
    chain = transport(endpoint, "eth_chainId", [])
    if chain != CHAIN_ID:
        raise VerificationError(f"{name}: wrong blockchain chain ID")
    height = hex(block)
    header = transport(endpoint, "eth_getBlockByNumber", [height, False])
    if not isinstance(header, dict) or as_hex_int(header.get("number"), name="block number") != block:
        raise VerificationError(f"{name}: wrong block number")
    block_hash = header.get("hash")
    if not isinstance(block_hash, str) or not HASH.fullmatch(block_hash):
        raise VerificationError(f"{name}: block hash missing or malformed")
    result = {"provider": name, "endpoint": endpoint, "chain_id": CHAIN_ID,
              "block": block, "block_hash": block_hash.lower(),
              "address": address.lower()}
    if metric == "balance":
        wei = as_hex_int(transport(endpoint, "eth_getBalance", [address, height]), name="balance")
        result["balance_wei"] = str(wei)
    elif metric == "tx_count":
        nonce = as_hex_int(transport(endpoint, "eth_getTransactionCount", [address, height]), name="nonce")
        result["tx_count"] = nonce
    else:
        raise VerificationError("unsupported metric")
    return result


def verify(address: str, block: int, providers: tuple[str, ...] = ("1rpc", "flashbots"),
           metric: str = "balance",
           transport: Callable[[str, str, list[Any]], Any] = jsonrpc) -> dict:
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    evidence: dict = {"status": "UNVERIFIED", "intent_id": INTENT,
        "chain": "ethereum", "network": "mainnet", "address": address, "block": block,
        "metric": metric, "checked_at_utc": now, "providers_required": list(providers)}
    if not ADDRESS.fullmatch(address):
        return {**evidence, "error": "invalid Ethereum address"}
    if isinstance(block, bool) or not isinstance(block, int) or not 1 <= block <= 1_000_000_000:
        return {**evidence, "error": "block must be explicit positive integer"}
    if metric not in ("balance", "tx_count"):
        return {**evidence, "error": "unsupported metric"}
    if len(set(providers)) != len(providers) or len(providers) < 2 or any(p not in ALLOWED_RPC for p in providers):
        return {**evidence, "error": "at least two distinct allowlisted RPC providers required"}
    observations = []
    problems = []
    with ThreadPoolExecutor(max_workers=len(providers)) as pool:
        futures = {pool.submit(verify_one_provider, name, address, block, metric, transport): name for name in providers}
        for fut in as_completed(futures):
            try: observations.append(fut.result())
            except Exception as exc:
                problems.append({"provider": futures[fut], "type": type(exc).__name__, "error": str(exc)[:140]})
    observations.sort(key=lambda row: row["provider"])
    evidence["observations"] = observations
    if problems:
        evidence["errors"] = problems
        return evidence
    fields = ("chain_id", "address", "block", "block_hash", "balance_wei" if metric=="balance" else "tx_count")
    conflicts = [field for field in fields if len({row[field] for row in observations}) != 1]
    if conflicts:
        evidence["error"] = "independent RPC disagreement"
        evidence["conflicting_fields"] = conflicts
        return evidence
    evidence.update(status="VERIFIED", block_hash=observations[0]["block_hash"],
        evidence_source="two or more independent live public JSON-RPC reads at the exact pinned block")
    if metric == "balance":
        wei = int(observations[0]["balance_wei"])
        evidence.update(balance_wei=str(wei), balance_gwei_exact=format(Decimal(wei)/Decimal(10**9), "f"))
    else:
        evidence.update(tx_count=observations[0]["tx_count"])
    return evidence


def evaluate_claim(evidence: dict, *, claimed_balance_gwei: str | None = None,
                   claimed_tx_count: str | None = None) -> dict:
    if evidence.get("status") != "VERIFIED":
        return {"verdict": "ABSTAIN", "reason": "ground truth not independently confirmed"}
    if claimed_balance_gwei is None and claimed_tx_count is None:
        return {"verdict": "NO_CLAIM", "reason": "ground truth gathered, no candidate answer supplied"}
    if (claimed_balance_gwei is not None and "balance_gwei_exact" not in evidence) or (claimed_tx_count is not None and "tx_count" not in evidence):
        return {"verdict": "ABSTAIN", "reason": "candidate field not independently verified for this metric"}
    claims = {}
    try:
        if claimed_balance_gwei is not None:
            value = Decimal(claimed_balance_gwei)
            if not value.is_finite() or value < 0:
                raise ValueError("balance claim not finite nonnegative")
            claims["balance_gwei"] = value == Decimal(evidence["balance_gwei_exact"])
        if claimed_tx_count is not None:
            if not claimed_tx_count.isascii() or not claimed_tx_count.isdecimal():
                raise ValueError("transaction count must be unsigned integer")
            claims["tx_count"] = int(claimed_tx_count) == evidence["tx_count"]
    except (InvalidOperation, ValueError) as exc:
        return {"verdict": "INVALID_CLAIM", "error": str(exc)[:100]}
    return {"verdict": "MATCH" if all(claims.values()) else "MISMATCH", "field_matches": claims}


def main() -> int:
    p=argparse.ArgumentParser(description="NEXUS read-only Telegraph ONCHAIN_METRIC_VERIFY evaluator")
    p.add_argument("--address", default=DEMO_ADDRESS)
    p.add_argument("--block", type=int, default=DEMO_BLOCK)
    p.add_argument("--metric", choices=("balance","tx_count"), default="balance")
    p.add_argument("--providers", nargs="+", choices=tuple(ALLOWED_RPC), default=["1rpc", "flashbots"])
    p.add_argument("--claimed-balance-gwei")
    p.add_argument("--claimed-tx-count")
    p.add_argument("--output", help="Write public evidence JSON (no private keys)")
    args=p.parse_args()
    report=verify(args.address, args.block, tuple(args.providers),metric=args.metric)
    report["candidate_check"] = evaluate_claim(report,
        claimed_balance_gwei=args.claimed_balance_gwei, claimed_tx_count=args.claimed_tx_count)
    encoded=json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    print(encoded, end="")
    if args.output:
        with open(args.output, "w", encoding="utf8") as file: file.write(encoded)
    return 0 if report["status"] == "VERIFIED" else 2


if __name__ == "__main__":
    sys.exit(main())
