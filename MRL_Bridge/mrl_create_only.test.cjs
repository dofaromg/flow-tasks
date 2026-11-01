const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const crypto = require('node:crypto');
const { spawn } = require('node:child_process');
const { createWriter, validateName, status } = require('./mrl_create_only.cjs');
function fixture(t) { const root = fs.mkdtempSync(path.join(process.env.RUNNER_TEMP || os.tmpdir(), 'MRL-')); t.after(() => fs.rmSync(root, { recursive:true, force:true })); return root; }
test('binary SHA256 readback and existing file is preserved', t => {
 const root=fixture(t), write=createWriter(root), dest=path.join(root,'nested','x'), raw=Buffer.from([0,255,42]);
 const r=write(dest,raw); assert.equal(r.created_exclusively,true); assert.equal(r.sha256,crypto.createHash('sha256').update(fs.readFileSync(dest)).digest('hex'));
 assert.throws(()=>write(dest,Buffer.from('overwrite')), {code:'EEXIST'}); assert.deepEqual(fs.readFileSync(dest),raw);
});
test('independent processes race: exactly one winner', async t => {
 const root=fixture(t), dest=path.join(root,'race');
 const script=`const {createWriter}=require(${JSON.stringify(require.resolve('./mrl_create_only.cjs'))}); try {createWriter(process.argv[1])(process.argv[2],Buffer.from(process.argv[3]));process.exit(0)}catch(e){process.exit(e.code==='EEXIST'?9:10)}`;
 const codes=await Promise.all(Array.from({length:12},(_,i)=>new Promise(resolve=>{const p=spawn(process.execPath,['-e',script,root,dest,String(i)]);p.on('exit',resolve);}))); assert.equal(codes.filter(c=>c===0).length,1); assert.equal(codes.filter(c=>c===9).length,11);
});
test('traversal, sibling escape, symlink parent and destination refused', t=>{
 const root=fixture(t), other=fixture(t), write=createWriter(root);
 for(const p of [path.join(root,'..','escape'),root+'-sibling/x',root+'/../x']) assert.throws(()=>write(p,Buffer.from('x')));
 fs.symlinkSync(other,path.join(root,'link'),process.platform==='win32'?'junction':'dir'); assert.throws(()=>write(path.join(root,'link','x'),Buffer.from('x')));
 fs.symlinkSync(path.join(other,'target'),path.join(root,'leaf')); assert.throws(()=>write(path.join(root,'leaf'),Buffer.from('x'))); assert.equal(fs.existsSync(path.join(other,'target')),false);
});
test('Windows special paths rejected on every CI host',()=>{
 for(const p of ['D:relative','\\\\host\\share\\x','\\\\?\\D:\\x','D:\\MRL_Mother\\..\\x','D:\\MRL_Mother\\x:ads','D:\\MRL_Mother\\NUL.txt','D:\\MRL_Mother\\x.','D:\\MRL_Mother\\x ','D:\\MRL_Mother/x','D:\\MRL_Mother\\COM1','D:\\MRL_Mother\\CONIN$','D:\\MRL_Mother\\CONOUT$','D:\\MRL_Mother\\CON .txt','D:\\MRL_Mother\\FOO~1']) assert.throws(()=>validateName(p,true));
 validateName('D:\\MRL_Mother\\MRL_PR694_123\\回執.json',true);
});
test('permission failure is 403 and never creates target',t=>{
 const root=fixture(t), io=Object.create(fs); io.openSync=()=>{throw Object.assign(new Error('denied'),{code:'EACCES'})};
 assert.throws(()=>createWriter(root,io)(path.join(root,'x'),Buffer.from('x')),e=>status(e)===403); assert.equal(fs.existsSync(path.join(root,'x')),false);
});
test('write/fsync failure rolls back only newly created file',t=>{
 const root=fixture(t);
 for(const method of ['writeFileSync','fsyncSync']) {const io=Object.create(fs);io[method]=()=>{throw Object.assign(new Error('disk failure'),{code:'EIO'})};const dest=path.join(root,method);assert.throws(()=>createWriter(root,io)(dest,Buffer.from('x')));assert.equal(fs.existsSync(dest),false);}
});
test('disabled unless explicit existing root configured',()=>{assert.equal(createWriter(),null);assert.throws(()=>createWriter(path.join(os.tmpdir(),'MRL-does-not-exist-root')));});
test('actual server route contract: capabilities, status, legacy denial and base64',t=>{
 const vm=require('node:vm'); const root=fixture(t), routes={};
 const app={use(){},disable(){},get(p,...h){routes['GET '+p]=h.at(-1)},post(p,...h){routes['POST '+p]=h.at(-1)}};
 class Pool {on(){}}; class Redis {on(){}}
 const source=fs.readFileSync(path.join(__dirname,'server.js'),'utf8').replace(/boot\(\);\s*$/,'');
 const localRequire=name=>({express:Object.assign(()=>app,{json:()=>()=>{},text:()=>()=>{}}),pg:{Pool},ioredis:Redis,'./mrl_bridge_translation_center.cjs':{TranslationCenter:class{middleware(){} admission(){}}},'./mrl_create_only.cjs':require('./mrl_create_only.cjs')}[name]||require(name));
 vm.runInNewContext(source,{require:localRequire,process:{env:{MRL_BRIDGE_API_KEY:'test-only',MRL_BRIDGE_WRITE_ROOT:root,MRL_BRIDGE_LOG_DIR:root},on(){},version:process.version,platform:process.platform,arch:process.arch,pid:process.pid},console,Buffer,setInterval(){},setTimeout(){}});
 function call(route,body={}) {let code=200, data;const res={status(c){code=c;return this},json(d){data=d}};routes[route]({body,query:{},connection:{}},res);return {code,data};}
 assert.equal(call('GET /version').data.capabilities.file_write_create_only,true);
 const dest=path.join(root,'http.bin'),raw=Buffer.from([0,255,13]);
 assert.equal(call('POST /MRL_file/write',{filepath:dest,b64:raw.toString('base64')}).code,400);
 const body={filepath:dest,b64:raw.toString('base64'),create_only:true};assert.equal(call('POST /MRL_file/write',body).data.created_exclusively,true);
 assert.equal(call('POST /MRL_file/write',body).code,409);
 const read=call('POST /MRL_file/read',{filepath:dest,encoding:'base64'});assert.equal(read.data.content,raw.toString('base64'));assert.equal(read.data.size,raw.length);
 assert.equal(call('GET /MRL_write').code,405);
});
