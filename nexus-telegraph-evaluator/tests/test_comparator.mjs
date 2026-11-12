import fs from 'node:fs';
import assert from 'node:assert/strict';
const b64=fs.readFileSync(new URL('../build/nexus_comparator.wasm.base64',import.meta.url),'utf8').trim();
const bytes=Buffer.from(b64,'base64');
const {instance, module}=await WebAssembly.instantiate(bytes,{});
assert.equal(WebAssembly.Module.imports(module).length,0,'WASM must have no imports');
const {memory, imw_alloc, imw_free, imw_score_deterministic:score}=instance.exports;
for (const s of ['memory','imw_alloc','imw_free','imw_score_deterministic']) assert.ok(instance.exports[s],`missing ${s}`);
const I64_MAX=(1n<<63n)-1n, I64_MIN=-(1n<<63n), N=(1n<<64n);
const wrap=v=>{v=(v%N+N)%N;return v>=1n<<63n?v-N:v};
const absWrap=v=>v<0n?wrap(-v):v;
const satMul=(a,b)=>{const p=a*b;return p>I64_MAX?I64_MAX:p<I64_MIN?I64_MIN:p};
const decay=(err,tol)=>{
 if(tol<=0n) return err===0n?10000n:0n;
 const window=satMul(tol,2n);
 if(err>=window)return 0n;
 return satMul(10000n,wrap(window-err))/window;
};
function reference(code,tol,truth,miner){
 const diff=absWrap(wrap(miner-truth));
 const kind=Number(BigInt.asIntN(32,code));
 if(kind===1) return decay(diff,tol);
 if(kind===2) {
  const denom=absWrap(truth)>0n?absWrap(truth):1n;
  const q=diff*10000n/denom;
  return decay(q>I64_MAX?I64_MAX:q<I64_MIN?I64_MIN:q,tol);
 }
 return truth===miner?10000n:0n;
}
function runTest(code,tol,truth,miner){
 const ptr=imw_alloc(16);assert.ok(ptr>0);const d=new DataView(memory.buffer);d.setBigInt64(ptr,code,true);d.setBigInt64(ptr+8,tol,true);
 const actual=score(truth,miner,ptr);imw_free(ptr,16);const expected=reference(code,tol,truth,miner);
 assert.equal(actual,expected);
 assert.equal(score(truth,miner,ptr),expected,'determinism');
 assert.ok(actual>=0n && actual<=10000n);
}
let cases=0;
const truths=[1n,7n,10000n,900000n,1000000000n,10n**18n,-7n,-10000n,-(10n**18n)];
const codes=[0n,1n,2n,3n,999n,4294967297n];
const tolerances=[-1n,0n,1n,10n,30n,100n,1000n,10000n,1000000n];
for(const truth of truths)for(const code of codes)for(const tol of tolerances){
 const variants=[truth,truth+1n,truth-1n,truth+10n,truth-10n,truth+100n,truth-100n,
  truth+((truth<0n?-truth:truth)/100n),truth-((truth<0n?-truth:truth)/100n),truth*2n];
 for(const miner of variants){if(miner>I64_MAX||miner<I64_MIN)continue;runTest(code,tol,truth,miner);cases++}
}
for(const [c,t,x,m] of [[1n,1n,1000n,1002n],[2n,100n,10n**18n,10n**18n+12345678900000000n],
 [2n,0n,1n,1n],[2n,1n,-1n,-2n],[1n,2n,20n,23n]]){runTest(c,t,x,m);cases++}
console.log(JSON.stringify({status:'PASS',cases,wasm_bytes:bytes.length,exports:Object.keys(instance.exports),imports:WebAssembly.Module.imports(module).length}));
