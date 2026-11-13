#!/usr/bin/env python3
"""Strict, OFFLINE V3 candidate checks. This is not official node acceptance.

Run: python3 -m unittest discover -s tests -p 'test_truth_source_v3.py' -v
Requires PyYAML; never loads keys, signs, pays, or touches the eval pool.
"""
import ipaddress
import json
import re
import unittest
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlsplit, quote
import yaml

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "truth_source_eth_balance_v3.yaml"
ROW = ROOT / "data" / "truth_source_eth_balance_v3.jsonl"
INTENT = "ONCHAIN_METRIC_VERIFY_GENERAL"
SRC = yaml.safe_load(SOURCE.read_text(encoding="utf-8"))
ENTRY = SRC["endpoints"][0]
MAPPING = SRC["intent_mapping"][INTENT]


def actual_url(address, block, chain="ethereum", metric="balance"):
    if chain != "ethereum" or metric != "balance":
        raise ValueError("unsupported chain or metric")
    if not re.fullmatch(r"0x[0-9a-fA-F]{40}", address):
        raise ValueError("invalid EVM address")
    if type(block) is not int or not (0 <= block <= 10**12):
        raise ValueError("invalid historical block")
    return (SRC["base_url"] + ENTRY["external_path"].replace("{address}", address)
            + "?block_number=" + str(block))


def balance_gwei(witness, pinned_block):
    """Reference conversion with fail-closed checks; tests do not claim on-node checks."""
    if type(pinned_block) is not int or pinned_block < 0:
        raise ValueError("invalid block")
    if not isinstance(witness, dict) or not isinstance(witness.get("items"), list):
        raise ValueError("missing history")
    if not witness["items"]:
        raise ValueError("no reference")
    first = witness["items"][0]
    if (not isinstance(first, dict)
            or type(first.get("block_number")) is not int
            or first["block_number"] > pinned_block
            or first["block_number"] < 0):
        raise ValueError("state not pinned")
    value = first.get("value")
    if not isinstance(value, str) or re.fullmatch(r"\d{1,100}", value) is None:
        raise ValueError("value must be unsigned decimal wei")
    return Decimal(value) / Decimal("1000000000")


class TestTruthSourceV3(unittest.TestCase):
    def test_scalar_schema(self):
        self.assertEqual(SRC["version"], "1")
        self.assertEqual(SRC["kind"], "miner")
        self.assertEqual(SRC["id"], 0)
        self.assertEqual(SRC["protocol"], "generic")

    def test_slug_and_top_fields(self):
        self.assertRegex(SRC["slug"], r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
        allowed = {"version", "kind", "id", "slug", "protocol", "name", "description",
                   "base_url", "auth", "endpoints", "intent_mapping", "semantics"}
        self.assertEqual(set(SRC), allowed)

    def test_only_keyless_public_https(self):
        self.assertEqual(SRC["auth"], {"type": "none"})
        parsed = urlsplit(SRC["base_url"])
        self.assertEqual(parsed.scheme, "https")
        self.assertEqual(parsed.hostname, "eth.blockscout.com")
        self.assertIsNone(parsed.password)
        self.assertIsNone(parsed.username)

    def test_scope_one_endpoint_one_intent(self):
        self.assertEqual(len(SRC["endpoints"]), 1)
        self.assertEqual(ENTRY["intents"], [INTENT])
        self.assertEqual(SRC["semantics"], {"supported_intents": [INTENT]})

    def test_endpoint_schema(self):
        self.assertEqual(set(ENTRY), {"path", "external_path", "method", "description", "intents", "params"})
        self.assertEqual(ENTRY["method"], "GET")
        self.assertEqual(ENTRY["path"], MAPPING["endpoint"])
        self.assertTrue(ENTRY["external_path"].startswith("/"))

    def test_query_path_parameter_contract(self):
        self.assertEqual([v["name"] for v in ENTRY["params"]["path"]["required"]], ["address"])
        self.assertEqual([v["name"] for v in ENTRY["params"]["query"]["required"]], ["block_number"])
        self.assertEqual(MAPPING["input"]["address"], {"from": "address"})
        self.assertEqual(MAPPING["input"]["block_number"], {"from": "block"})

    def test_chain_metric_request_guards(self):
        h = ENTRY["params"]["header"]["required"]
        self.assertEqual([v["name"] for v in h], ["X-NEXUS-Chain", "X-NEXUS-Metric"])
        self.assertEqual([v["accepted_fields"][0]["value"] for v in h], ["ethereum", "balance"])
        self.assertEqual(MAPPING["input"]["X-NEXUS-Chain"], {"from": "chain"})
        self.assertEqual(MAPPING["input"]["X-NEXUS-Metric"], {"from": "metric"})

    def test_exact_output_conversion(self):
        self.assertEqual(MAPPING["output"], {"balance_gwei": {"path": "items.0.value", "unit": "wei"}})

    def test_valid_url(self):
        a = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
        u = actual_url(a, 20000000)
        self.assertEqual(u, SRC["base_url"] + "/api/v2/addresses/" + a
                         + "/coin-balance-history?block_number=20000000")

    def test_reject_mismatched_chains(self):
        a = "0x" + "a"*40
        for chain in ["polygon", "arbitrum", "", "Ethereum"]:
            with self.subTest(chain=chain), self.assertRaises(ValueError):
                actual_url(a, 20000000, chain=chain)

    def test_reject_wrong_metrics(self):
        a = "0x" + "a"*40
        for metric in ["tx_count", "nonce", "storage"]:
            with self.subTest(metric=metric), self.assertRaises(ValueError):
                actual_url(a, 20000000, metric=metric)

    def test_reject_malformed_address(self):
        for addr in ["0x123", "", "https://localhost", "0x" + "z"*40]:
            with self.subTest(address=addr), self.assertRaises(ValueError):
                actual_url(addr, 20000000)

    def test_reject_invalid_block(self):
        a = "0x" + "a"*40
        for block in ["latest", True, -1, 1.25, 10**13, None]:
            with self.subTest(block=block), self.assertRaises(ValueError):
                actual_url(a, block)

    def test_known_historical_wei_case_a(self):
        w = {"items": [{"block_number": 19997048, "value": "495394228822711118729"}]}
        self.assertEqual(balance_gwei(w, 20000000), Decimal("495394228822.711118729"))

    def test_known_historical_wei_case_b(self):
        w = {"items": [{"block_number": 19498309, "value": "955252261191686732332"}]}
        self.assertEqual(balance_gwei(w, 19500000), Decimal("955252261191.686732332"))

    def test_fail_closed_history_unavailable(self):
        for body in [{}, {"items": []}, {"items": None}, {"items": "bad"}]:
            with self.subTest(body=body), self.assertRaises(ValueError):
                balance_gwei(body, 20000000)

    def test_fail_closed_unpinned_history(self):
        for data in [{"block_number": 20000001, "value": "15"},
                     {"block_number": "20000000", "value": "15"},
                     {"block_number": -1, "value": "15"}]:
            with self.subTest(data=data), self.assertRaises(ValueError):
                balance_gwei({"items": [data]}, 20000000)

    def test_fail_closed_invalid_wei(self):
        for value in ["0x123", "NaN", "-1", "1.25", "", 2000]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                balance_gwei({"items":[{"block_number": 19000000, "value": value}]}, 20000000)

    def test_truth_source_jsonl_no_leak(self):
        line = ROW.read_bytes()
        self.assertEqual(line.count(b"\n"), 1)
        self.assertTrue(line.endswith(b"\n"))
        self.assertLess(len(line), 32*1024)
        payload = json.loads(line)
        self.assertEqual(set(payload), {"label_kind", "source"})
        self.assertEqual(payload["label_kind"], "truth_source")
        self.assertIsInstance(payload["source"], str)
        self.assertEqual(payload["source"], SOURCE.read_text(encoding="utf-8"))
        for disallowed in ["private_key", "signer", "tradebot", "api_key"]:
            self.assertNotIn(disallowed, SOURCE.read_text().lower())


if __name__ == "__main__":
    unittest.main()
