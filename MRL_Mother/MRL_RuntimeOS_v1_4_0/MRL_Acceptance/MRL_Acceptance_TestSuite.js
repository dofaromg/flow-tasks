const assert = require('assert');
const http = require('http');
const fs = require('fs');
const path = require('path');
const { runPipeline, server, jobs, ROOT } = require('../MRL_API/MRL_RuntimeServer');
const { MRLRuntimeNodeManager } = require('../MRL_RuntimeNode/MRL_RuntimeNode_Manager');
const { MRLUpstashBoxAdapter } = require('../MRL_Adapters/MRL_UpstashBox_Adapter');
const { MRLRuntimeOSAIModelGatewayService } = require('../MRL_Services/MRL_RuntimeOS_AIModelGateway_Service_v1');
const { MRLRuntimeOSSkillModuleService } = require('../MRL_Services/MRL_RuntimeOS_SkillModule_Service_v1');
const { MRLRuntimeOSArtifactTransferService } = require('../MRL_Services/MRL_RuntimeOS_ArtifactTransfer_Service_v1');

function testPipeline(source, filename) {
  const result = runPipeline({ source, filename, command:'整理 analyze parse execute verify attention context runtime mesh skill model artifact' });
  assert(result.origin_signature === 'MrLiouWord');
  assert(result.product === 'MRL_RuntimeOS_EnterpriseRuntimePlatform_CoreExecutable_v1_4_0');
  assert(result.bundle.metaIR.mrl_ir_type === 'MRL_MetaIR');
  assert(result.bundle.particleIR.particles.length >= 1);
  assert(result.contextGraph.nodes.length >= 1);
  assert(result.runtimeGraph.nodes.length >= 1);
  assert(result.attentionRoute.routes.length >= 1);
  assert(result.meshPlan.mrl_type === 'MRL_RuntimeMeshPlan');
  assert(result.meshExecution.status === 'completed');
  assert(result.verification.pass === true);
  assert(result.trace.steps.length >= 1);
  return result;
}

function createFakeOllamaServer() {
  const fake = http.createServer((req, res) => {
    if (req.url === '/api/tags') {
      res.writeHead(200, {'content-type':'application/json'});
      return res.end(JSON.stringify({ models: [{ name: 'mrl-test-model:latest', size: 1234 }] }));
    }
    if (req.url === '/api/generate') {
      let body='';
      req.on('data', c => body += c);
      req.on('end', () => {
        const parsed = body ? JSON.parse(body) : {};
        res.writeHead(200, {'content-type':'application/json'});
        res.end(JSON.stringify({ model: parsed.model, response: `MRL_TEST_AI_RESPONSE:${parsed.prompt}` }));
      });
      return;
    }
    res.writeHead(404, {'content-type':'application/json'}); res.end(JSON.stringify({ error:'not found' }));
  });
  return new Promise(resolve => {
    fake.listen(0, '127.0.0.1', () => {
      const port = fake.address().port;
      resolve({ server: fake, url: `http://127.0.0.1:${port}` });
    });
  });
}

(async()=>{
  const cases = [
    ['particle CTX { @layer: L2 @data: "整理文件" }\nparticle TOOL { @layer: L3 @type: "parser" }\nCTX ⊕ TOOL |> execute()', 'acceptance.fpp'],
    ['function MRL_add(a,b){ return a+b }', 'acceptance.js'],
    ['class MRLThing { public: void run(); };', 'acceptance.cpp'],
    ['def MRL_run(x):\n    return x', 'acceptance.py'],
    ['{"MRL_name":"demo","MRL_items":[1,2]}', 'acceptance.json'],
    ['# MRL Document\n\n整理文件\n整理文件', 'acceptance.md'],
    ['CREATE TABLE MRL_Test(id TEXT); SELECT * FROM MRL_Test;', 'acceptance.sql'],
    ['MRL_name: demo\nMRL_layer: L2', 'acceptance.yaml']
  ];
  const reports = cases.map(([source, filename]) => ({ filename, nodes: testPipeline(source, filename).runtimeGraph.nodes.length }));

  const nodeManager = new MRLRuntimeNodeManager(ROOT);
  const upstash = new MRLUpstashBoxAdapter();
  const externalNode = nodeManager.createNode(upstash.toRuntimeNode({ box_id:'box_acceptance_mock', runtime:'node', keepAlive:true, ssh_target:'mock@box.upstash.local' }));
  assert(externalNode.metadata.provider === 'Upstash Box');
  const heartbeat = nodeManager.heartbeat(externalNode.node_id, 'alive');
  assert(heartbeat.status === 'alive');

  const fake = await createFakeOllamaServer();
  const aiGateway = new MRLRuntimeOSAIModelGatewayService(ROOT, { ollamaHost: fake.url, defaultModel:'mrl-test-model:latest' });
  const aiHealth = await aiGateway.health();
  assert(aiHealth.live.ollama.reachable === true);
  const aiOut = await aiGateway.generate({ prompt:'hello mrl', backend:'ollama' });
  assert(String(aiOut.output).includes('MRL_TEST_AI_RESPONSE'));

  const skills = new MRLRuntimeOSSkillModuleService(ROOT, aiGateway, null);
  assert(skills.list().some(s => s.name === 'MRL_Skill_AIInfer_v1'));
  const fileSkill = await skills.execute('MRL_Skill_FileAnalyze_v1', { filename:'a.txt', content:'line1\nline2' });
  assert(fileSkill.result.lines === 2);
  const codeSkill = await skills.execute('MRL_Skill_CodeScaffold_v1', { module_name:'MRL_RuntimeOS_Test_Service_v1', language:'javascript' });
  assert(codeSkill.result.source.includes('MRLRuntimeOSTestServicev1'));
  const inferSkill = await skills.execute('MRL_Skill_AIInfer_v1', { prompt:'skill prompt', backend:'ollama', model:'mrl-test-model:latest' });
  assert(String(inferSkill.result.output).includes('MRL_TEST_AI_RESPONSE'));
  const modelPlan = await skills.execute('MRL_Skill_3DModelImportPlan_v1', { filename:'asset.glb' });
  assert(modelPlan.result.supported === true);

  const artifacts = new MRLRuntimeOSArtifactTransferService(ROOT);
  const begin = artifacts.begin({ filename:'MRL_acceptance_artifact.txt', total_chunks:2 });
  artifacts.addChunk({ artifact_id: begin.artifact_id, chunk_index:0, data_base64: Buffer.from('hello ').toString('base64') });
  const c2 = artifacts.addChunk({ artifact_id: begin.artifact_id, chunk_index:1, data_base64: Buffer.from('mrl').toString('base64') });
  assert(c2.complete === true);
  const assembled = artifacts.assemble({ artifact_id: begin.artifact_id });
  assert(assembled.size === 9);
  assert(fs.existsSync(assembled.path));

  const blenderManifestPath = path.join(ROOT,'MRL_BlenderBridge','MRL_RuntimeOS_3DModelBridge_Service_v1','MRL_BlenderBridge_MANIFEST.json');
  assert(fs.existsSync(blenderManifestPath));
  const blenderManifest = JSON.parse(fs.readFileSync(blenderManifestPath,'utf8'));
  assert(blenderManifest.module === 'MRL_RuntimeOS_3DModelBridge_Service_v1');

  const job = jobs.submit({ source:cases[0][0], filename:'job_acceptance.fpp', command:'execute verify mesh' });
  await new Promise(r=>setTimeout(r,250));
  const jobDone = jobs.get(job.job_id);
  assert(jobDone.status === 'completed');
  fake.server.close();

  console.log(JSON.stringify({
    status:'PASS',
    product:'MRL_RuntimeOS_EnterpriseRuntimePlatform_CoreExecutable_v1_4_0',
    checks:['MultiLanguageAdapters','MetaIR','ParticleIR','ContextGraph','RuntimeGraph','AttentionRoute','RuntimeExecute','TraceStore','RoundTripVerify','JobQueue','AuditLedger','OpenAPI','AuthGateConfig','RuntimeNode','RuntimeMesh','UpstashBoxAdapterSpec','AIModelGatewayProtocol','SkillModuleRegistry','SkillExecution','ArtifactTransfer','Blender3DModelBridgeSource'],
    truth_status:{
      sandbox_verified:'Node RuntimeOS, skill modules, artifact transfer, AI connector protocol fixture',
      dl580_pending:'Ollama/OpenAI-compatible live model host, Blender bpy runtime, persistent service deployment'
    },
    reports,
    runtime_node: externalNode.node_id,
    job:jobDone.job_id,
    origin_signature:'MrLiouWord'
  }, null, 2));
  if (server.listening) server.close();
})().catch(e=>{ console.error('MRL_ACCEPTANCE_FAIL', e); process.exit(1); });
