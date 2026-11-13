#!/usr/bin/env python3
"""Generate an offline, unsigned deterministic Telegraph truth_source row.

No network, signing key, or production service access. The resulting JSONL
requires an independent check and EIP-191 signature before any POST.
"""
from pathlib import Path
import json
ROOT = Path(__file__).resolve().parents[1]
source_file = ROOT / 'data' / 'truth_source_eth_balance_v1.yaml'
out_file = ROOT / 'data' / 'truth_source_eth_balance_v1.jsonl'


def build_row(yaml_bytes: bytes) -> bytes:
    source = yaml_bytes.decode('utf-8')
    # The docs accept YAML as a JSON string and disallow prompt/chosen/rejected.
    row = { 'label_kind': 'truth_source', 'source': source }
    return (json.dumps(row, ensure_ascii=False, separators=(',', ':')) + '\n').encode('utf-8')


if __name__ == '__main__':
    data = build_row(source_file.read_bytes())
    if len(data) > 32768:
        raise SystemExit('source size exceeds 32KiB')
    out_file.write_bytes(data)
    print(f'generated {out_file.name} ({len(data)} bytes) - UNSENT')
