import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("v", ROOT / "src/onchain_verifier.py")
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)

class TestVerifier(unittest.TestCase):
    address = v.DEMO_ADDRESS
    block = v.DEMO_BLOCK
    h = "0x" + "b" * 64
    def transport(self, url, method, params):
        assert url in v.ALLOWED_RPC.values()
        if method == "eth_chainId": return "0x1"
        if method == "eth_getBlockByNumber": return {"number": hex(self.block), "hash": self.h}
        if method == "eth_getBalance": return hex(123456789123456789)
        if method == "eth_getTransactionCount": return hex(46)
        raise ValueError(method)
    def test_complete_agreement(self):
        r = v.verify(self.address, self.block, transport=self.transport)
        self.assertEqual(r["status"], "VERIFIED")
        self.assertNotIn("tx_count",r)
        self.assertEqual(r["balance_gwei_exact"], "123456789.123456789")
        self.assertEqual(v.evaluate_claim(r, claimed_balance_gwei="123456789.123456789")["verdict"],"MATCH")
        self.assertEqual(v.evaluate_claim(r, claimed_balance_gwei="123456789.123456790")["verdict"],"MISMATCH")
    def test_conflicting_balance(self):
        def fake(url, method, params):
            result=self.transport(url, method, params)
            if method=="eth_getBalance" and url==v.ALLOWED_RPC["flashbots"]:return "0x0"
            return result
        r=v.verify(self.address,self.block,transport=fake)
        self.assertEqual(r["status"],"UNVERIFIED")
        self.assertIn("balance_wei",r["conflicting_fields"])
        self.assertEqual(v.evaluate_claim(r,claimed_balance_gwei="0")["verdict"],"ABSTAIN")
    def test_conflicting_block(self):
        def fake(url, method, params):
            result=self.transport(url, method, params)
            if method=="eth_getBlockByNumber" and url==v.ALLOWED_RPC["flashbots"]:
                return {"number":hex(self.block),"hash":"0x"+"a"*64}
            return result
        r=v.verify(self.address,self.block,transport=fake)
        self.assertIn("block_hash",r["conflicting_fields"])
    def test_wrong_chain(self):
        def fake(url, method, params):
            if url==v.ALLOWED_RPC["flashbots"] and method=="eth_chainId":return "0x89"
            return self.transport(url,method,params)
        self.assertEqual(v.verify(self.address,self.block,transport=fake)["status"],"UNVERIFIED")
    def test_bad_inputs(self):
        for addr,block in [("0x123",self.block),(self.address,-1),(self.address,"latest"),(self.address,True)]:
            self.assertEqual(v.verify(addr,block,transport=self.transport)["status"],"UNVERIFIED")
        self.assertEqual(v.verify(self.address,self.block,providers=("1rpc","1rpc"),transport=self.transport)["status"],"UNVERIFIED")
    def test_no_bogus_verified_without_sources(self):
        def fail(url,method,params):raise v.VerificationError("timeout")
        r=v.verify(self.address,self.block,transport=fail)
        self.assertEqual(len(r.get("errors",[])),2)
        self.assertEqual(v.evaluate_claim(r,claimed_balance_gwei="0")["verdict"],"ABSTAIN")
    def test_claim_format_and_units(self):
        e=v.verify(self.address,self.block,transport=self.transport)
        for bad in ["NaN","Infinity","-1","not a number"]:
            self.assertEqual(v.evaluate_claim(e,claimed_balance_gwei=bad)["verdict"],"INVALID_CLAIM")
        self.assertEqual(v.evaluate_claim(e,claimed_tx_count="46")["verdict"],"ABSTAIN")
        e2=v.verify(self.address,self.block,metric="tx_count",transport=self.transport)
        self.assertEqual(e2["tx_count"],46)
        self.assertEqual(v.evaluate_claim(e2,claimed_tx_count="46")["verdict"],"MATCH")
        self.assertEqual(v.evaluate_claim(e2,claimed_tx_count="47")["verdict"],"MISMATCH")
        self.assertEqual(v.evaluate_claim(e2,claimed_tx_count="46.0")["verdict"],"INVALID_CLAIM")
    def test_provider_cannot_supply_nonce_history(self):
        def fake(url,method,params):
            if method == "eth_getTransactionCount":raise v.VerificationError("history pruned")
            return self.transport(url,method,params)
        self.assertEqual(v.verify(self.address,self.block,metric="balance",transport=fake)["status"],"VERIFIED")
        self.assertEqual(v.verify(self.address,self.block,metric="tx_count",transport=fake)["status"],"UNVERIFIED")
    def test_hex_validation(self):
        with self.assertRaises(v.VerificationError):v.as_hex_int("123",name="balance")
        with self.assertRaises(v.VerificationError):v.as_hex_int(None,name="balance")

if __name__ == "__main__": unittest.main(verbosity=2)
