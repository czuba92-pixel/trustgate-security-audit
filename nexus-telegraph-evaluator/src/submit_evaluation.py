#!/usr/bin/env python3
"""Submit only fully independently verified no-cost eval data; one POST, honest ledger.
DO NOT import any Tradebot key, or send blockchain transactions.
"""
from pathlib import Path
import json,hashlib,os,secrets,urllib.request,urllib.parse,urllib.error,datetime,time
from decimal import Decimal
from eth_account import Account
from eth_account.messages import encode_defunct

ROOT=Path(__file__).resolve().parents[1]
ENDPOINT="https://devnode.telegraphprotocol.com"
INTENT="ONCHAIN_METRIC_VERIFY_GENERAL"
DATA=ROOT/"data/evaluation_pairs_v1.jsonl"
EVIDENCE=ROOT/"evidence/evaluation_pairs_evidence.json"
KEY=ROOT/".contributor_key.json"
LEDGER=ROOT/"submission_ledger.json"

def load():
 raw=DATA.read_bytes()
 evidence=json.loads(EVIDENCE.read_text())
 rows=[json.loads(line) for line in raw.splitlines()]
 assert 1<=len(rows)<=40  # pool requires 5 contributors, not 5 rows
 assert hashlib.sha256(raw).hexdigest()==evidence["body_sha256"]
 assert len(rows)==len(evidence["samples"])
 assert all(r["intent_id"]==INTENT and r["label_kind"]=="preference_pair" and 16<=len(r["prompt"])<=16000 for r in rows)
 for row, proof in zip(rows,evidence["samples"]):
  assert Decimal(row["chosen"].split(" Gwei")[0])==Decimal(proof["balance_gwei_six_decimals"])
  assert Decimal(row["rejected"].split(" Gwei")[0])==Decimal(proof["false_gwei"])
  assert row["provenance"]=={"source_kind":"api","source_url":proof["source_url"]}
  assert proof["providers"]==["flashbots","blockscout"]
  assert Decimal(proof["balance_wei"])/Decimal(10**9)>0
  assert row["chosen"] !=row["rejected"]
 return raw,rows

def get_mine(address):
 url=ENDPOINT+"/api/evalpool/submissions/mine?"+urllib.parse.urlencode({"submitter":address,"intent_id":INTENT,"limit":200})
 req=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"NEXUS-Telegraph-Eval/1.0"})
 with urllib.request.urlopen(req,timeout=15) as f:
  assert f.status==200
  return json.loads(f.read(256000))

def save(o):
 tmp=LEDGER.with_suffix(".tmp")
 fd=os.open(str(tmp),os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
 with os.fdopen(fd,"w") as f:
  json.dump(o,f,ensure_ascii=False,indent=2)
  f.flush();os.fsync(f.fileno())
 os.replace(tmp,LEDGER)
 os.chmod(LEDGER,0o600)

def main(mode):
 raw,rows=load()
 d=json.loads(KEY.read_text())
 assert KEY.stat().st_mode&0o077==0
 assert d["purpose"]=="telegraph-evalpool-only"
 acct=Account.from_key(d["private_key"])
 assert acct.address.lower()==d["address"].lower()
 bodyhash=hashlib.sha256(raw).hexdigest()
 mine=get_mine(acct.address)
 print("PREFLIGHT",json.dumps({"mode":mode,"address":acct.address,"rows":len(rows),"body_sha256":bodyhash,"prior_uploaded_rows":mine.get("count"),"status":"PASS"},ensure_ascii=False),flush=True)
 if mode=="check":return
 assert mode=="send"
 if LEDGER.exists():
  ledger=json.loads(LEDGER.read_text())
  raise SystemExit("REFUSAL: prior submission ledger exists with status "+str(ledger.get("status"))+"; no blind retry")
 if int(mine.get("count",0))>0:
  raise SystemExit("REFUSAL: this signer already has rows on node; manual reconciliation required")
 nonce=secrets.token_hex(16)
 msg="\n".join(["Telegraph eval-pool submission v1","intent_id: "+INTENT,"body_sha256: "+bodyhash,"nonce: "+nonce,"chain_id: 11155111"])
 signature=acct.sign_message(encode_defunct(text=msg)).signature.hex()
 if not signature.startswith("0x"):signature="0x"+signature
 addr=acct.address
 ledger={"status":"request_started_unknown","intent_id":INTENT,"body_sha256":bodyhash,"address":addr,"rows":len(rows),"nonce":nonce,"time_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"network":"Sepolia testnet signed EIP-191, offchain POST, zero gas"}
 save(ledger) # before external call: no retries after ambiguity
 url=ENDPOINT+"/api/evalpool/submissions?"+urllib.parse.urlencode({"intent_id":INTENT,"submitter":addr})
 req=urllib.request.Request(url,raw,headers={"Content-Type":"application/x-ndjson","Accept":"application/json","X-Evalpool-Signature":signature,"X-Evalpool-Nonce":nonce,"User-Agent":"NEXUS-Telegraph-Eval/1.0"},method="POST")
 try:
  with urllib.request.urlopen(req,timeout=35) as response:
   payload=response.read(100000)
   status=response.status
  obj=json.loads(payload)
  ledger.update(status="server_accepted_body" if status==200 else "unexpected_http",http_status=status,response=obj)
 except urllib.error.HTTPError as e:
  detail=e.read(4000).decode("utf8","replace")
  ledger.update(status="server_http_error",http_status=e.code,error=detail)
 except Exception as e:
  ledger.update(status="response_ambiguous",error=type(e).__name__+":"+str(e)[:160])
 save(ledger)
 print("POST_RESULT",json.dumps({k:v for k,v in ledger.items() if k not in ("nonce",)},ensure_ascii=False)[:4500],flush=True)
 try:
  confirmation=get_mine(addr)
  receipt={"queried_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"address":addr,"count":confirmation.get("count"),"rows":[{k:v for k,v in x.items() if k in ("intent_id","row_hash","case_id","status","reason_code","provenance_class")} for x in confirmation.get("rows",[])[:100]]}
  (ROOT/"pool_readback.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2))
  print("READBACK",json.dumps(receipt,ensure_ascii=False)[:7000],flush=True)
 except Exception as e:print("READBACK_ERROR",type(e).__name__,str(e)[:150],flush=True)

if __name__=="__main__":
 import sys
 if len(sys.argv)!=2 or sys.argv[1] not in ("check","send"):raise SystemExit("Usage: submit_evaluation.py check|send")
 main(sys.argv[1])
