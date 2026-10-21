const http = require('http');
const fs = require('fs');
const path = require('path');
const { MRLUniversalParserCore } = require('../MRL_Core/MRL_UniversalParser');
const { MRLRuntimeGraphBuilder } = require('../MRL_Runtime/MRL_RuntimeGraph_Builder');
const { MRLContextGraphBuilder } = require('../MRL_Context/MRL_ContextGraph_Builder');
const { MRLAttentionKernelRouter } = require('../MRL_Runtime/MRL_AttentionKernel_Router');
const { MRLRuntimeExecutor } = require('../MRL_Runtime/MRL_RuntimeExecutor');
const { MRLRoundTripVerifier } = require('../MRL_Verification/MRL_RoundTrip_Verifier');
const { MRLModuleRegistry } = require('../MRL_Registry/MRL_Module_Registry');
const { MRL_hash } = require('../MRL_Core/MRL_MetaIR');
const { MRLLogger } = require('../MRL_Enterprise/MRL_Logger');
const { MRL_loadConfig, MRL_validateConfig } = require('../MRL_Enterprise/MRL_Config');
const { MRL_validateAuth } = require('../MRL_Security/MRL_AuthGate');
const { MRLJobQueue } = require('../MRL_Jobs/MRL_JobQueue');
const { MRLRuntimeNodeManager } = require('../MRL_RuntimeNode/MRL_RuntimeNode_Manager');
const { MRLRuntimeMeshController } = require('../MRL_RuntimeMesh/MRL_RuntimeMesh_Controller');
const { MRLUpstashBoxAdapter } = require('../MRL_Adapters/MRL_UpstashBox_Adapter');
const { MRLRuntimeOSAIModelGatewayService } = require('../MRL_Services/MRL_RuntimeOS_AIModelGateway_Service_v1');
const { MRLRuntimeOSSkillModuleService } = require('../MRL_Services/MRL_RuntimeOS_SkillModule_Service_v1');
const { MRLRuntimeOSArtifactTransferService } = require('../MRL_Services/MRL_RuntimeOS_ArtifactTransfer_Service_v1');

const ROOT = path.resolve(__dirname, '..');
const MRL_CFG = MRL_loadConfig(ROOT);
const MRL_CFG_CHECK = MRL_validateConfig(MRL_CFG);
if (!MRL_CFG_CHECK.ok) { console.error(JSON.stringify({error:'MRL_CONFIG_INVALID', errors:MRL_CFG_CHECK.errors}, null, 2)); if (require.main === module) process.exit(1); }
const logger = new MRLLogger(ROOT);
const parser = new MRLUniversalParserCore();
const graphBuilder = new MRLRuntimeGraphBuilder();
const contextBuilder = new MRLContextGraphBuilder();
const router = new MRLAttentionKernelRouter();
const executor = new MRLRuntimeExecutor(ROOT);
const verifier = new MRLRoundTripVerifier();
const registry = new MRLModuleRegistry(ROOT);
const nodeManager = new MRLRuntimeNodeManager(ROOT);
const upstashAdapter = new MRLUpstashBoxAdapter();
const metrics = { started_at:new Date().toISOString(), requests:0, errors:0, jobs_submitted:0 };

function readBody(req) { return new Promise((resolve,reject)=>{ let data=''; req.on('data',c=>{ data+=c; if(data.length>MRL_CFG.max_body_bytes) reject(new Error('MRL_BODY_TOO_LARGE')); }); req.on('end',()=>{ try{ resolve(data ? JSON.parse(data) : {}) } catch(e){ reject(e) }}); }); }
function send(res, code, obj, type='application/json') { res.writeHead(code, {'content-type': type, 'access-control-allow-origin':'*', 'access-control-allow-headers':'content-type,authorization,x-mrl-token', 'access-control-allow-methods':'GET,POST,OPTIONS'}); res.end(type==='application/json'?JSON.stringify(obj,null,2):obj); }
function writeJSON(dirRel, name, obj) { const dir = path.join(ROOT, dirRel); fs.mkdirSync(dir, { recursive:true }); fs.writeFileSync(path.join(dir,name), JSON.stringify(obj,null,2)); }
function listFiles(dirRel) { const dir=path.join(ROOT,dirRel); if(!fs.existsSync(dir)) return []; return fs.readdirSync(dir).filter(f=>!f.startsWith('.')).map(f=>({ name:f, size:fs.statSync(path.join(dir,f)).size })); }
function runPipeline(body) {
  const source = body.source || 'particle CTX { @layer: L2 @data: "hello" }';
  const filename = body.filename || 'MRL_Input.fpp';
  const command = body.command || source;
  const bundle = parser.parseToAll(source, filename);
  const contextGraph = contextBuilder.build(bundle.metaIR, bundle.particleIR);
  const runtimeGraph = graphBuilder.build(bundle.particleIR, bundle.metaIR);
  const attentionRoute = router.route(runtimeGraph, command);
  const verification = verifier.verify(source, bundle, runtimeGraph, contextGraph);
  const meshPlan = mesh.plan(bundle, contextGraph, command);
  const trace = body.execute === false ? null : executor.execute(runtimeGraph, attentionRoute, bundle, { source, data: body.data });
  const meshExecution = body.execute === false ? null : mesh.execute(meshPlan, runtimeGraph, attentionRoute, bundle, { source, data: body.data });
  const stamp = Date.now();
  writeJSON('MRL_Storage/MRL_MetaIR', `MRL_MetaIR_${stamp}.json`, bundle.metaIR);
  writeJSON('MRL_Storage/MRL_ParticleIR', `MRL_ParticleIR_${stamp}.json`, bundle.particleIR);
  writeJSON('MRL_Storage/MRL_ContextGraph', `MRL_ContextGraph_${stamp}.json`, contextGraph);
  writeJSON('MRL_Storage/MRL_RuntimeGraph', `MRL_RuntimeGraph_${stamp}.json`, runtimeGraph);
  writeJSON('MRL_Storage/MRL_Attention', `MRL_AttentionRoute_${stamp}.json`, attentionRoute);
  logger.log('MRL_PIPELINE_RUN',{filename, meta_hash:bundle.metaIR.meta_hash, particle_count:bundle.particleIR.particles.length, verification_pass:verification.pass});
  return { origin_signature:'MrLiouWord', product:'MRL_RuntimeOS_EnterpriseRuntimePlatform_CoreExecutable_v1_4_0', bundle, contextGraph, runtimeGraph, attentionRoute, meshPlan, meshExecution, verification, trace };
}
const mesh = new MRLRuntimeMeshController(ROOT, nodeManager, graphBuilder, router, executor, logger);
const aiGateway = new MRLRuntimeOSAIModelGatewayService(ROOT);
const skillService = new MRLRuntimeOSSkillModuleService(ROOT, aiGateway, logger);
const artifactTransfer = new MRLRuntimeOSArtifactTransferService(ROOT);
const jobs = new MRLJobQueue(ROOT, runPipeline, logger);
if (nodeManager.listNodes().length === 0) {
  nodeManager.createNode({ node_id:'MRL_LOCAL_NODE', runtime:'node', role:'MRL_Local_RuntimeNode', keep_alive:true, isolation:'local_process', capabilities:['parse','execute','verify','attention','context','runtimegraph'] });
}

const server = http.createServer(async (req,res)=>{
  metrics.requests++;
  if (req.method === 'OPTIONS') return send(res, 200, {});
  try {
    if (req.url === '/' || req.url === '/index.html') return send(res, 200, fs.readFileSync(path.join(ROOT,'MRL_WebConsole','index.html'),'utf8'), 'text/html; charset=utf-8');
    if (req.url === '/openapi.json') return send(res, 200, JSON.parse(fs.readFileSync(path.join(ROOT,'MRL_OpenAPI','MRL_openapi.json'),'utf8')));
    if (req.url === '/api/mrl/health') return send(res, 200, { status:'ok', product:'MRL_RuntimeOS_EnterpriseRuntimePlatform_CoreExecutable_v1_4_0', origin_signature:'MrLiouWord', auth_required:MRL_CFG.auth_required, capabilities:['parse','metair','particleir','contextgraph','runtimegraph','attention','execute','verify','file_ingest','module_registry','storage','job_queue','audit_ledger','openapi','dl580_deploy','runtime_node','runtime_mesh','external_box_adapter','ai_model_gateway','skill_modules','artifact_transfer','blender_3d_model_bridge'] });
    if (req.url === '/api/mrl/metrics') return send(res, 200, { origin_signature:'MrLiouWord', ...metrics });
    const auth = MRL_validateAuth(req); if (!auth.ok) return send(res, auth.code || 401, { error:auth.error });

    if (req.url === '/api/mrl/runtime/nodes') return send(res,200,{origin_signature:'MrLiouWord', nodes:nodeManager.listNodes()});
    if (req.url === '/api/mrl/runtime/nodes/create' && req.method === 'POST') { const body=await readBody(req); return send(res,200,nodeManager.createNode(body)); }
    if (req.url === '/api/mrl/runtime/nodes/heartbeat' && req.method === 'POST') { const body=await readBody(req); const rec=nodeManager.heartbeat(body.node_id, body.status || 'alive'); return rec?send(res,200,rec):send(res,404,{error:'MRL_RUNTIME_NODE_NOT_FOUND'}); }
    if (req.url === '/api/mrl/runtime/mesh/plan' && req.method === 'POST') { const body=await readBody(req); const parsed=parser.parseToAll(body.source||'', body.filename||'MRL_Input.fpp'); const contextGraph=contextBuilder.build(parsed.metaIR, parsed.particleIR); return send(res,200,mesh.plan(parsed, contextGraph, body.command||body.source||'')); }
    if (req.url === '/api/mrl/runtime/mesh/list') return send(res,200,{origin_signature:'MrLiouWord', mesh:mesh.listPlans()});
    if (req.url === '/api/mrl/adapters/upstash/describe') return send(res,200,upstashAdapter.describe());
    if (req.url === '/api/mrl/adapters/upstash/register-node' && req.method === 'POST') { const body=await readBody(req); return send(res,200,nodeManager.createNode(upstashAdapter.toRuntimeNode(body))); }

    if (req.url === '/api/mrl/runtimeos/ai/describe') return send(res,200,aiGateway.describe());
    if (req.url === '/api/mrl/runtimeos/ai/health') return send(res,200,await aiGateway.health());
    if (req.url.startsWith('/api/mrl/runtimeos/ai/models')) { const backend = new URL(req.url,'http://localhost').searchParams.get('backend') || 'ollama'; return send(res,200,await aiGateway.listModels(backend)); }
    if (req.url === '/api/mrl/runtimeos/ai/generate' && req.method === 'POST') { const body = await readBody(req); return send(res,200,await aiGateway.generate(body)); }
    if (req.url === '/api/mrl/runtimeos/skills/list') return send(res,200,{origin_signature:'MrLiouWord', product:'MRL_RuntimeOS_EnterpriseRuntimePlatform_CoreExecutable_v1_4_0', skills:skillService.list()});
    if (req.url === '/api/mrl/runtimeos/skills/execute' && req.method === 'POST') { const body = await readBody(req); return send(res,200,await skillService.execute(body.skill, body.payload || {})); }
    if (req.url === '/api/mrl/runtimeos/artifacts/begin' && req.method === 'POST') { const body=await readBody(req); return send(res,200,artifactTransfer.begin(body)); }
    if (req.url === '/api/mrl/runtimeos/artifacts/chunk' && req.method === 'POST') { const body=await readBody(req); return send(res,200,artifactTransfer.addChunk(body)); }
    if (req.url === '/api/mrl/runtimeos/artifacts/assemble' && req.method === 'POST') { const body=await readBody(req); return send(res,200,artifactTransfer.assemble(body)); }
    if (req.url === '/api/mrl/runtimeos/blender/bridge/manifest') return send(res,200,JSON.parse(fs.readFileSync(path.join(ROOT,'MRL_BlenderBridge','MRL_RuntimeOS_3DModelBridge_Service_v1','MRL_BlenderBridge_MANIFEST.json'),'utf8')));
    if (req.url === '/api/mrl/registry/modules') return send(res,200, registry.persist());
    if (req.url === '/api/mrl/storage/list') return send(res,200,{ origin_signature:'MrLiouWord', files:{ trace:listFiles('MRL_Storage/MRL_Trace'), metair:listFiles('MRL_Storage/MRL_MetaIR'), particleir:listFiles('MRL_Storage/MRL_ParticleIR'), reports:listFiles('MRL_Storage/MRL_Reports'), files:listFiles('MRL_Storage/MRL_Files'), jobs:listFiles('MRL_Storage/MRL_Jobs'), audit:listFiles('MRL_Storage/MRL_Audit') }});
    if (req.url === '/api/mrl/audit/ledger') { const f=path.join(ROOT,'MRL_Storage','MRL_Audit','MRL_Audit_Ledger.jsonl'); return send(res,200,{origin_signature:'MrLiouWord', ledger:fs.existsSync(f)?fs.readFileSync(f,'utf8').trim().split('\n').filter(Boolean).slice(-200).map(x=>JSON.parse(x)):[]}); }
    if (req.url === '/api/mrl/jobs/submit' && req.method === 'POST') { const body=await readBody(req); metrics.jobs_submitted++; return send(res,200,jobs.submit(body)); }
    if (req.url === '/api/mrl/jobs/list') return send(res,200,{origin_signature:'MrLiouWord', jobs:jobs.list()});
    if (req.url.startsWith('/api/mrl/jobs/get')) { const id = new URL(req.url,'http://localhost').searchParams.get('id'); const rec=jobs.get(id); return rec?send(res,200,rec):send(res,404,{error:'MRL_JOB_NOT_FOUND'}); }
    if (req.url === '/api/mrl/files/ingest' && req.method === 'POST') { const body=await readBody(req); const filename=body.filename || `MRL_File_${Date.now()}.txt`; const content=String(body.content || ''); const rec={mrl_type:'MRL_File_Ingest_Record', origin_signature:'MrLiouWord', filename, size:content.length, sha256:MRL_hash({content}), created_at:new Date().toISOString()}; const safe=filename.replace(/[^A-Za-z0-9_.-]/g,'_'); fs.mkdirSync(path.join(ROOT,'MRL_Storage','MRL_Files'),{recursive:true}); fs.writeFileSync(path.join(ROOT,'MRL_Storage','MRL_Files',safe), content); writeJSON('MRL_Storage/MRL_Reports', `MRL_File_Ingest_${Date.now()}.json`, rec); logger.log('MRL_FILE_INGEST', rec); return send(res,200,rec); }
    if (req.url === '/api/mrl/parser/parse' && req.method === 'POST') { const body=await readBody(req); return send(res, 200, parser.parseToAll(body.source || '', body.filename || 'MRL_Input.fpp')); }
    if (req.url === '/api/mrl/metair/compile' && req.method === 'POST') { const body=await readBody(req); return send(res, 200, parser.parseToAll(body.source || '', body.filename || 'MRL_Input.fpp').metaIR); }
    if (req.url === '/api/mrl/particleir/compile' && req.method === 'POST') { const body=await readBody(req); return send(res, 200, parser.parseToAll(body.source || '', body.filename || 'MRL_Input.fpp').particleIR); }
    if (req.url === '/api/mrl/context/graph' && req.method === 'POST') { const body = await readBody(req); const p = parser.parseToAll(body.source||'', body.filename||'MRL_Input.fpp'); return send(res,200,contextBuilder.build(p.metaIR, p.particleIR)); }
    if (req.url === '/api/mrl/runtime/graph' && req.method === 'POST') { const body = await readBody(req); const p = parser.parseToAll(body.source||'', body.filename||'MRL_Input.fpp'); return send(res,200,graphBuilder.build(p.particleIR, p.metaIR)); }
    if (req.url === '/api/mrl/attention/route' && req.method === 'POST') { const body = await readBody(req); const result = runPipeline({...body, execute:false}); return send(res,200,result.attentionRoute); }
    if (req.url === '/api/mrl/verify/roundtrip' && req.method === 'POST') { const body = await readBody(req); return send(res,200,runPipeline({...body, execute:false}).verification); }
    if (req.url === '/api/mrl/runtime/execute' && req.method === 'POST') { const body = await readBody(req); return send(res,200,runPipeline(body)); }
    return send(res,404,{error:'MRL_ROUTE_NOT_FOUND', url:req.url});
  } catch(e) { metrics.errors++; logger.log('MRL_SERVER_ERROR',{message:e.message}); return send(res,500,{error:'MRL_SERVER_ERROR', message:e.message, stack:e.stack}); }
});
if (require.main === module) { server.listen(MRL_CFG.port, MRL_CFG.host, ()=>logger.log('MRL_SERVER_STARTED',{url:`http://${MRL_CFG.host}:${MRL_CFG.port}`})); }
module.exports = { server, runPipeline, ROOT, MRL_CFG, jobs };
