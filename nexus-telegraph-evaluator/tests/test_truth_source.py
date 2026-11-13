"""Fail-closed static and fixture checks; NOT a Telegraph-node acceptance test."""
from pathlib import Path
import hashlib
import importlib.util
import json
import re
import unittest
from urllib.parse import urlencode, urlparse, parse_qs
import yaml

BASE = Path(__file__).resolve().parents[1]
SOURCE = BASE / 'data' / 'truth_source_eth_balance_v1.yaml'
JSONL = BASE / 'data' / 'truth_source_eth_balance_v1.jsonl'
DATA = yaml.safe_load(SOURCE.read_text('utf-8'))


def build_url(address, block):
    """Mirror the documented declarative path/query mapping for offline tests."""
    if not re.fullmatch(r'0x[0-9a-fA-F]{40}', address):
        raise ValueError('invalid-address')
    if type(block) is not int or not 0 <= block <= 10**12:
        raise ValueError('invalid-block')
    route = DATA['endpoints'][0]
    path = route['external_path'].replace('{address}', address)
    return DATA['base_url'] + path + '?' + urlencode({'block_number': block})


def extract_gwei(body, pinned_block):
    """An offline defensive verifier for the external response contract.

    A node's mapping does not execute these checks automatically. These are
    independent checks of the witness used to validate this source.
    """
    if not isinstance(body, dict) or not isinstance(body.get('items'), list):
        raise ValueError('missing-items')
    if not body['items']:
        raise ValueError('no-historical-state')
    head = body['items'][0]
    if not isinstance(head.get('block_number'), int) or head['block_number'] > pinned_block:
        raise ValueError('future-state')
    value = head.get('value')
    if not isinstance(value, str) or not re.fullmatch(r'\d+', value):
        raise ValueError('unparseable-wei')
    from decimal import Decimal
    return Decimal(value) / Decimal(10**9)


class TruthSourceTests(unittest.TestCase):
    def test_miner_document(self):
        self.assertEqual(DATA['version'], '1')
        self.assertEqual(DATA['kind'], 'miner')
        self.assertEqual(DATA['protocol'], 'generic')
        self.assertEqual(DATA['auth']['type'], 'none')
        self.assertEqual(DATA['id'], 0)
        self.assertRegex(DATA['slug'], r'^[a-z0-9]+(-[a-z0-9]+)*$')

    def test_intent_exact(self):
        i='ONCHAIN_METRIC_VERIFY_GENERAL'
        e=DATA['endpoints'][0]
        self.assertEqual(e['intents'],[i])
        self.assertEqual(DATA['semantics']['supported_intents'],[i])
        self.assertEqual(DATA['intent_mapping'][i]['endpoint'],e['path'])

    def test_endpoint_public_keyless(self):
        p = urlparse(DATA['base_url'])
        self.assertEqual(p.scheme,'https')
        self.assertEqual(p.hostname,'eth.blockscout.com')
        self.assertEqual(DATA['auth'],{'type':'none'})
        self.assertEqual(len(DATA['endpoints']),1)

    def test_path_query_contract(self):
        e=DATA['endpoints'][0]
        self.assertEqual(e['method'],'GET')
        self.assertEqual(e['params']['path']['required'][0]['name'],'address')
        self.assertEqual(e['params']['query']['required'][0]['name'],'block_number')
        mapping=DATA['intent_mapping']['ONCHAIN_METRIC_VERIFY_GENERAL']
        self.assertEqual(mapping['input']['address']['from'],'address')
        self.assertEqual(mapping['input']['block_number']['from'],'block')
        hdr=e['params']['header']['required']
        self.assertEqual([h['name'] for h in hdr], ['X-NEXUS-Chain','X-NEXUS-Metric'])
        self.assertEqual([h['accepted_fields'][0]['value'] for h in hdr], ['ethereum','balance'])
        self.assertEqual(mapping['input']['X-NEXUS-Chain']['from'],'chain')
        self.assertEqual(mapping['input']['X-NEXUS-Metric']['from'],'metric')

    def test_output_mapping(self):
        m=DATA['intent_mapping']['ONCHAIN_METRIC_VERIFY_GENERAL']['output']['balance_gwei']
        self.assertEqual(m['path'],'items.0.value')
        self.assertEqual(m['unit'],'wei')

    def test_pinned_url_is_not_latest(self):
        a='0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045'
        u=build_url(a,20_000_000)
        self.assertEqual(parse_qs(urlparse(u).query)['block_number'],['20000000'])
        self.assertNotIn('latest',u)

    def test_reject_bad_address(self):
        for a in ['0x0', 'test', 'http://localhost', '0x'+'g'*40]:
            with self.assertRaises(ValueError): build_url(a,20_000_000)

    def test_reject_bad_block(self):
        a='0x'+'a'*40
        for b in ['latest',-1,1.5,True,None,10**20]:
            with self.assertRaises(ValueError): build_url(a,b)

    def test_external_historical_witness_one(self):
        fixture={'items':[{'block_number':19997048,'value':'495394228822711118729'}]}
        self.assertEqual(str(extract_gwei(fixture,20_000_000)),'495394228822.711118729')

    def test_external_historical_witness_two(self):
        fixture={'items':[{'block_number':19498309,'value':'955252261191686732332'}]}
        self.assertEqual(str(extract_gwei(fixture,19_500_000)),'955252261191.686732332')

    def test_fail_closed_on_unreliable_response(self):
        for j in [{}, {'items': []}, {'items':[{'block_number':20000001,'value':'15'}]},
                  {'items':[{'block_number':20000000,'value':'0x123'}]},
                  {'items':[{'block_number':20000000,'value':'NaN'}]}]:
            with self.assertRaises(ValueError):extract_gwei(j,20_000_000)

    def test_signed_upload_payload_shape(self):
        lines=JSONL.read_bytes().splitlines()
        self.assertEqual(len(lines),1)
        row=json.loads(lines[0])
        self.assertEqual(set(row),{'label_kind','source'})
        self.assertEqual(row['label_kind'],'truth_source')
        self.assertEqual(row['source'],SOURCE.read_text('utf-8'))
        self.assertNotIn('prompt',row)
        self.assertLess(len(lines[0]),32768)

    def test_no_key_material_or_runtime_refs(self):
        s=SOURCE.read_text('utf-8').lower()
        self.assertNotIn('private_key',s)
        self.assertNotIn('tradebot',s)
        self.assertNotIn('authorization:',s)


if __name__=='__main__': unittest.main()
