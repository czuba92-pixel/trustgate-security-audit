#!/usr/bin/env python3
"""Batch-based fixed-block ETH balance oracle comparisons for test cases.
Refuses all uncorroborated, zero, rounded-ambiguous, or unverifiable records.
"""
from pathlib import Path
import json,urllib.request,urllib.parse,urllib.error,hashlib,datetime,time,difflib,re
from decimal import Decimal,ROUND_HALF_UP
from build_dataset import SAMPLES,blockscout
ROOT=Path(__file__).resolve().parents[1]
RPCS={"flashbots":"https://rpc.flashbots.net"}
SAMPLES = SAMPLES + [
 ("Vitalik block 19.5m",SAMPLES[0][1],19500000),
 ("Binance historical block 22m",SAMPLES[1][1],22000000),
 ("Coinbase historical block 23m",SAMPLES[2][1],23000000),
 ("WETH escrow historical",SAMPLES[3][1],23500000),
 ("Deposit contract historical",SAMPLES[4][1],23550000),
 ("Burn account historical",SAMPLES[10][1],23050000),
]
stems=[
"Check the ETH native-coin balance in Gwei for {label} ({addr}) at Ethereum mainnet block {block}.",
"At historical Ethereum height {block}, report the account's Gwei balance: {addr} ({label}).",
"For the Ethereum ledger at block {block}, what Gwei value is held natively by {addr}, described as {label}?",
"Evaluate this pinned chain state: address {addr}; block {block}; return its native ETH balance in Gwei.",
"From Ethereum's block {block}, derive the native Gwei balance of {label} address {addr}.",
"What is the historical account balance in Gwei of Ethereum address {addr} at height {block}?",
"Provide Gwei, not wei or ETH, for address {addr} on Ethereum mainnet block {block} ({label}).",
"Evidence request: at block {block}, how much ETH-native Gwei does {addr} ({label}) own?",
"Ethereum archive test: output the Gwei balance of address {addr} at block number {block}.",
"At Ethereum block height {block}, how many Gwei are attributed to the wallet {addr} ({label})?",
"Check a historical Ethereum snapshot: give Gwei for account {addr}, block {block}.",
"Determine native ETH balance in Gwei at mainnet height {block} for {addr}, tagged {label}.",
"Reconcile ETH account {addr}: identify the balance in Gwei at Ethereum block {block} ({label}).",
"At Ethereum snapshot {block}, assess on-chain Gwei held by {label} address {addr}.",
"Return Gwei for this specific account and chain height: {addr} / Ethereum {block}.",
"Check address {addr} from Ethereum block {block}, reporting Gwei rather than wei.",
"Compute balance Gwei of the Ethereum account {addr} for block {block}, tagged {label}.",
"What was the natively held Gwei at Ethereum block {block} for {addr} ({label})?",
]
def batch(url):
 queries=[{"jsonrpc":"2.0","id":900,"method":"eth_chainId","params":[]}]
 for i,(_,a,b) in enumerate(SAMPLES):
  queries.append({"jsonrpc":"2.0","id":i*2+1,"method":"eth_getBalance","params":[a,hex(b)]})
  # Each request is explicit about the block. Independent RPC agreement + Blockscout pin the record.
 ans={}
 for off in range(0,len(queries),5):
  chunk=queries[off:off+5]
  req=urllib.request.Request(url,data=json.dumps(chunk).encode(),headers={"Content-Type":"application/json","Accept":"application/json","User-Agent":"Mozilla/5.0"})
  try:
   with urllib.request.urlopen(req,timeout=18) as resp:
    d=json.load(resp)
   if isinstance(d,list):
    ans.update({x.get("id"):x for x in d})
   else:
    for q in chunk:ans[q["id"]]={"error":{"message":"provider refused batch"}}
  except Exception as e:
   for q in chunk:ans[q["id"]]={"error":{"message":type(e).__name__+" "+str(e)[:90]}}
  time.sleep(.5)
 assert ans[900].get("result")=="0x1",ans.get(900)
 return ans
def main():
 sources={}
 for name,url in RPCS.items():
  try:
   sources[name]=batch(url)
   print("RPC_BATCH_PASS",name,"items",len(sources[name]),flush=True)
  except Exception as e:
   print("RPC_BATCH_FAIL",name,type(e).__name__,str(e)[:190],flush=True)
 if len(sources)!=1:raise SystemExit("STOP: Flashbots RPC batch unavailable (second independent source is Blockscout)")
 rows=[]; evidence=[]; skipped=[]
 for i,(label,addr,block) in enumerate(SAMPLES):
  try:
   vals=[]
   for name,d in sources.items():
    response=d.get(i*2+1,{})
    if response.get("error"):raise ValueError(name+" provider error: "+str(response.get("error"))[:140])
    result=response.get("result")
    assert isinstance(result,str) and result.startswith("0x")
    vals.append((name,int(result,16)))
   assert len(vals)==1,"RPC result unavailable"
   wei=vals[0][1]
   if wei<=0:raise ValueError("zero wei not scoreable under Telegraph comparator")
   scout,url,last_updated=blockscout(addr,block)
   assert int(scout)==wei,"Blockscout and the two RPCs disagree"
   value=(Decimal(wei)/Decimal(10**9)).quantize(Decimal("0.000001"),rounding=ROUND_HALF_UP)
   # Deliberately wrong answer, at least 10% away from true Gwei.
   wrong=(value*(Decimal("1.30") if i%2 else Decimal("0.70"))).quantize(Decimal("0.000001"),rounding=ROUND_HALF_UP)
   assert abs(wrong-value)>.000001
   prompt=stems[i].format(label=label,addr=addr,block=block)
   chosen=f"{value:.6f} Gwei. Correct pinned Ethereum block {block}, account {addr}; validated with independently operated Flashbots RPC and Blockscout API."
   rejected=f"{wrong:.6f} Gwei. Incorrect native ETH balance claimed for Ethereum block {block}, account {addr}."
   if any(difflib.SequenceMatcher(None,prompt,r["prompt"]).ratio()>=0.84 for r in rows):
    raise ValueError("near-duplicate prompt")
   row={"prompt":prompt,"chosen":chosen,"rejected":rejected,"label_kind":"preference_pair","intent_id":"ONCHAIN_METRIC_VERIFY_GENERAL","provenance":{"source_kind":"api","source_url":url}}
   rows.append(row)
   evidence.append({"sample":label,"address":addr,"block":block,"balance_wei":str(wei),"balance_gwei_six_decimals":str(value),"false_gwei":str(wrong),"block_hash":"NOT_CHECKED_IN_THIS_BATCH","providers":["flashbots","blockscout"],"blockscout_last_change":last_updated,"source_url":url})
   print("VERIFIED",i,label,str(value),flush=True)
  except Exception as e:
   skipped.append({"sample":label,"error":type(e).__name__,"details":str(e)[:140]})
   print("SKIPPED",i,label,type(e).__name__,str(e)[:110],flush=True)
  time.sleep(.70)
 if len(rows)<5:
  (ROOT/"dataset_rejections.json").write_text(json.dumps(skipped,indent=2))
  raise SystemExit("STOP: only "+str(len(rows))+" quality-assured rows (need >=5)")
 raw=("".join(json.dumps(r,ensure_ascii=False,separators=(",",":"))+"\n" for r in rows)).encode()
 (ROOT/"data/evaluation_pairs_v1.jsonl").write_bytes(raw)
 evidence_report={"intent":"ONCHAIN_METRIC_VERIFY_GENERAL","generated_at_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"samples":evidence,"rejected_candidates":skipped,"body_sha256":hashlib.sha256(raw).hexdigest(),"disclosure":"AI-assisted cases, independently verified real on-chain values; errors deliberately injected for rejected examples. No submission claimed yet."}
 (ROOT/"evidence/evaluation_pairs_evidence.json").write_text(json.dumps(evidence_report,indent=2))
 print("DATASET_READY",json.dumps({"rows":len(rows),"skipped":len(skipped),"body_sha256":evidence_report["body_sha256"],"bytes":len(raw)},ensure_ascii=False),flush=True)
if __name__=="__main__":main()
