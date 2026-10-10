import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const DIST = process.argv[2];
const A = require(`${DIST}/attention.js`);
const worker = require(`${DIST}/index.js`).default;

let P=0,F=0; const c=(n,cond,d)=>{if(cond){P++;console.log('  ✅',n);}else{F++;console.log('  ❌',n,d??'');}};
const close=(a,b,e=1e-9)=>Math.abs(a-b)<e;

console.log('== pure math ==');
// cosine
c('cosine identical = 1', close(A.cosineSimilarity([1,2,3],[1,2,3]),1));
c('cosine orthogonal = 0', close(A.cosineSimilarity([1,0],[0,1]),0));
c('cosine opposite = -1', close(A.cosineSimilarity([1,0],[-1,0]),-1));
// softmax
const sm=A.softmax([1,1,1]); c('softmax uniform -> 1/3 each', sm.every(x=>close(x,1/3)));
c('softmax sums to 1', close(A.softmax([3,1,0.2]).reduce((a,b)=>a+b,0),1));
// attention: symmetric keys -> equal weights
let r=A.scaledDotProductAttention([1,0],[[1,0],[1,0]],[[10,0],[0,10]]);
c('symmetric keys -> weights 0.5/0.5', close(r.weights[0],0.5)&&close(r.weights[1],0.5));
c('attention weights sum to 1', close(r.weights.reduce((a,b)=>a+b,0),1));
c('symmetric output = mean of values', close(r.output[0],5)&&close(r.output[1],5));
// attention: query aligns with key0 -> weight0 largest
r=A.scaledDotProductAttention([10,0],[[10,0],[0,10],[0,-10]],[[1,0,0],[0,1,0],[0,0,1]]);
c('aligned key gets highest weight', r.weights[0]>r.weights[1] && r.weights[0]>r.weights[2], JSON.stringify(r.weights));
// topK
const ranked=A.topKSimilar([1,0,0],[{id:'a',vector:[1,0,0]},{id:'b',vector:[0,1,0]},{id:'c',vector:[0.9,0.1,0]}],2);
c('topK ranks exact match first', ranked[0].id==='a', JSON.stringify(ranked));
c('topK returns k=2', ranked.length===2);
// dim mismatch throws
let threw=false; try{A.dot([1,2],[1,2,3]);}catch(e){threw=e instanceof A.VectorError;} c('dim mismatch throws VectorError', threw);

console.log('== worker HTTP ==');
const req=(m,p,b)=>new Request('https://ve.mrliou'+p,{method:m,headers:{'content-type':'application/json'},body:b!==undefined?JSON.stringify(b):undefined});
// mock KV
const store=new Map(); const KV={async get(k){return store.has(k)?store.get(k):null;},async put(k,v){store.set(k,v);},async delete(k){store.delete(k);}};
const env={PARTICLE_AUTH_VAULT:KV};
let R=await worker.fetch(req('GET','/health'),env); let j=await R.json(); c('health 200 + kv_bound', R.status===200&&j.kv_bound===true, JSON.stringify(j));
R=await worker.fetch(req('POST','/v1/attention',{query:[1,0],keys:[[1,0],[1,0]],values:[[10,0],[0,10]]}),env); j=await R.json();
c('/v1/attention 200 + output', R.status===200&&close(j.output[0],5), JSON.stringify(j));
R=await worker.fetch(req('POST','/v1/attention',{query:[1,0],keys:'nope',values:[[1]]}),env); c('/v1/attention bad input 400', R.status===400);
R=await worker.fetch(req('POST','/v1/similarity',{query:[1,0,0],corpus:[{id:'x',vector:[1,0,0]},{id:'y',vector:[0,1,0]}],top_k:1}),env); j=await R.json();
c('/v1/similarity ranks match first', R.status===200&&j.results[0].id==='x', JSON.stringify(j));
// embed store roundtrip
R=await worker.fetch(req('POST','/v1/embed/upsert',{id:'v1',vector:[1,2,3]}),env); c('embed upsert 201', R.status===201);
await worker.fetch(req('POST','/v1/embed/upsert',{id:'v2',vector:[3,2,1]}),env);
R=await worker.fetch(req('POST','/v1/embed/search',{query:[1,2,3],ids:['v1','v2'],top_k:2}),env); j=await R.json();
c('embed search finds nearest (v1)', R.status===200&&j.results[0].id==='v1', JSON.stringify(j));
// unbound KV degradation
R=await worker.fetch(req('POST','/v1/embed/upsert',{vector:[1]}),{}); c('embed upsert kv_unbound 503', R.status===503);
R=await worker.fetch(req('GET','/nope'),env); c('unknown route 404', R.status===404);

console.log(`\n===== vector-attention-engine: ${P} passed, ${F} failed =====`);
process.exit(F?1:0);
