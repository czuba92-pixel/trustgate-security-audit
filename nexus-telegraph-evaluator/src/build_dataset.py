#!/usr/bin/env python3
"""Generate original, independently verified Telegraph evaluation pairs.
No signing keys; no monetary transactions. Source data only from live public APIs.
"""
import json, os, time, datetime, hashlib, urllib.request, urllib.parse, urllib.error, re
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT=Path(__file__).resolve().parent
INTENT="ONCHAIN_METRIC_VERIFY_GENERAL"
ENDPOINTS={"1rpc":"https://1rpc.io/eth","flashbots":"https://rpc.flashbots.net"}
SAMPLES=[
("Vitalik public wallet", "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",20000000),
("Binance known hot wallet","0x28C6c06298d514Db089934071355E5743bf21d60",21000000),
("Coinbase known wallet","0x503828976D22510aad0201ac7ec88293211D23Da",20500000),
("Wrapped Ether token contract","0xC02aaa39b223FE8D0A0e5C4F27eAD9083C756Cc2",22000000),
("Ethereum proof-of-stake deposit contract","0x00000000219ab540356cBB839Cbe05303d7705Fa",23000000),
("Uniswap V2 Router","0x7a250d5630b4cf539739df2c5dacab00bF7579e8",21500000),
("Uniswap V3 SwapRouter","0xE592427A0AEce92De3Edee1F18E0157C05861564",22500000),
("USDT token contract","0xdAC17F958D2ee523a2206206994597C13D831ec7",23200000),
("USDC token contract","0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",20800000),
("Lido stETH token contract","0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84",22800000),
("Ethereum burn address","0x000000000000000000000000000000000000dEaD",22100000),
("Uniswap V3 Factory","0x1F98431c8aD98523631AE4a59f267346ea31F984",22300000),
]
def rpc(url,method,params):
 b=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
 req=urllib.request.Request(url,b,headers={"Content-Type":"application/json","User-Agent":"Mozilla/5.0","Accept":"application/json"})
 with urllib.request.urlopen(req,timeout=12) as f:
  d=json.loads(f.read(100_000))
 assert d.get("id")==1 and "result" in d and "error" not in d,(method,d)
 return d["result"]
def blockscout(addr,block):
 url="https://eth.blockscout.com/api/v2/addresses/"+addr+"/coin-balance-history?"+urllib.parse.urlencode({"block_number":block})
 req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0","Accept":"application/json"})
 with urllib.request.urlopen(req,timeout=12) as f:
  d=json.load(f)
 items=d.get("items") or []
 if not items:raise ValueError("Blockscout no historical items")
 point=items[0]
 assert int(point["block_number"])<=block
 return str(int(point["value"])),url,int(point["block_number"])
def main():
 rows=[];reports=[];fails=[]
 for i,(label,addr,block) in enumerate(SAMPLES):
  if not re.fullmatch(r"0x[0-9a-fA-F]{40}",addr):
   fails.append({"name":label,"reason":"INVALID_ADDRESS"});continue
  try:
   observations=[]
   for name,endpoint in ENDPOINTS.items():
    chain=rpc(endpoint,"eth_chainId",[])
    header=rpc(endpoint,"eth_getBlockByNumber",[hex(block),False])
    balance=rpc(endpoint,"eth_getBalance",[addr,hex(block)])
    assert chain=="0x1" and int(header["number"],16)==block
    observations.append({"provider":name,"block_hash":header["hash"],"balance_wei":str(int(balance,16))})
   assert len({z["block_hash"] for z in observations})==1 and len({z["balance_wei"] for z in observations})==1,"RPC disagreement"
   wei=int(observations[0]["balance_wei"])
   if wei<=0: raise ValueError("zero balance skipped: truth of zero is not scored")
   scout_wei,source_url,scout_updated=blockscout(addr,block)
   assert scout_wei==str(wei),"Blockscout disagrees with two RPCs"
   gwei=Decimal(wei)/Decimal(10**9)
   approx=gwei.quantize(Decimal("0.000001"),rounding=ROUND_HALF_UP)
   assert approx>0
   # Wrong answer is an intentionally wrong magnitude. Both answers have clear, explicitly-scored Gwei units.
   bogus=(approx*Decimal(10 if i%2==0 else 0.1)).quantize(Decimal("0.000001"))
   if bogus==approx:raise ValueError("negative answer not distinct")
   stems=[
     "State the native ETH balance of {addr} at Ethereum block {block}, in Gwei.",
     "On Ethereum mainnet, how many Gwei were held by address {addr} at block height {block}?",
     "For historical Ethereum block {block}, give the ETH wallet balance in Gwei for {addr}.",
     "Verify Ethereum native balance in Gwei for address {addr} at pinned height {block}.",
     "At block {block} on Ethereum, what is the native-account balance of {addr}, measured in Gwei?",
     "Report Gwei native funds for {addr} as of Ethereum block {block}.",
     "Find the on-chain ETH balance of {addr} at block {block}; use Gwei as units.",
     "Ethereum archive query: native balance of {addr} at height {block} (Gwei)?",
     "Return the exact six-decimal Gwei value for Ethereum address {addr} and block {block}.",
     "Read Ethereum address {addr} on block {block}: what's its ETH balance in Gwei?",
     "At Ethereum's historical block {block}, check Gwei at the public address {addr}.",
     "Compare on-chain balance on Ethereum block {block}: {addr}; what Gwei amount is there?",
   ]
   prompt=stems[i].format(addr=addr,block=block)
   assert len(prompt)>=16
   chosen=f"{approx:.6f} Gwei. Ethereum mainnet, pinned block {block}, address {addr}. Confirmed against two independent archive RPCs and Blockscout historical balance."
   rejected=f"{bogus:.6f} Gwei. Ethereum mainnet, pinned block {block}, address {addr}. This answer misstates the observed historical balance magnitude."
   assert chosen != rejected
   row={"prompt":prompt,"chosen":chosen,"rejected":rejected,"label_kind":"preference_pair","intent_id":INTENT,"provenance":{"source_kind":"api","source_url":source_url}}
   reports.append({"sample":label,"address":addr,"block":block,"wei":str(wei),"gwei_six_decimals":str(approx),"bogus_gwei":str(bogus),"blockscout_last_change_at":scout_updated,"block_hash":observations[0]["block_hash"],"providers":observations,"source_url":source_url})
   rows.append(row)
   print("PASS",i,label,block,str(approx),flush=True)
  except Exception as e:
   fails.append({"sample":label,"block":block,"error":type(e).__name__,"reason":str(e)[:180]})
   print("SKIP",i,label,type(e).__name__,str(e)[:110],flush=True)
  time.sleep(.2)
 if len(rows)<5:raise SystemExit("FAILED: fewer than 5 independently corroborated records")
 root=ROOT
 data=("".join(json.dumps(x,ensure_ascii=False,separators=(",",":"))+"\n" for x in rows)).encode("utf8")
 (root/"evaluation_pairs_v1.jsonl").write_bytes(data)
 evidence={"intent_id":INTENT,"generated_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"accepted_local_checks":len(rows),"failures":fails,"samples":reports,"body_sha256":hashlib.sha256(data).hexdigest(),"disclosure":"AI-assisted generation and fixed numeric perturbations; independent 1RPC+Flashbots+Blockscout checks; network acceptance NOT YET known"}
 (root/"evaluation_pairs_evidence.json").write_text(json.dumps(evidence,ensure_ascii=False,indent=2))
 print("RESULT",json.dumps({"rows":len(rows),"failures":len(fails),"sha256":evidence["body_sha256"],"bytes":len(data)},ensure_ascii=False),flush=True)
if __name__=="__main__":main()