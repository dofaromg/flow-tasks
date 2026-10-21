const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

function MRL_sha256(data) { return crypto.createHash('sha256').update(data).digest('hex'); }

class MRLRuntimeOSSkillModuleService {
  constructor(root, aiGateway = null, logger = null) {
    this.root = root;
    this.aiGateway = aiGateway;
    this.logger = logger;
    this.origin_signature = 'MrLiouWord';
    this.skills = new Map();
    this.registerBuiltins();
  }

  register(skill) {
    if (!skill || !skill.name || typeof skill.execute !== 'function') throw new Error('MRL_SKILL_INVALID');
    this.skills.set(skill.name, {
      origin_signature: this.origin_signature,
      product: 'MRL_RuntimeOS_EnterpriseRuntimePlatform_CoreExecutable_v1_4_0',
      ...skill
    });
  }

  registerBuiltins() {
    this.register({
      name: 'MRL_Skill_FileAnalyze_v1',
      category: 'file',
      description: 'Analyze text/file content length, lines, extension, hash and basic structure.',
      input_schema: { content: 'string', filename: 'string' },
      execute: async ({ content = '', filename = 'MRL_Input.txt' }) => {
        const ext = path.extname(filename).replace('.','').toLowerCase() || 'txt';
        const lines = String(content).split(/\r?\n/);
        return { filename, ext, bytes: Buffer.byteLength(String(content)), lines: lines.length, sha256: MRL_sha256(String(content)), preview: String(content).slice(0, 400) };
      }
    });
    this.register({
      name: 'MRL_Skill_CodeScaffold_v1',
      category: 'code',
      description: 'Generate product-named scaffold metadata and starter source for MRL modules.',
      input_schema: { module_name: 'string', language: 'string' },
      execute: async ({ module_name = 'MRL_RuntimeOS_Custom_Service_v1', language = 'javascript' }) => {
        const className = module_name.replace(/[^A-Za-z0-9]/g, '');
        const source = language.toLowerCase().includes('python')
          ? `class ${className}:\n    origin_signature = \"MrLiouWord\"\n    def execute(self, payload):\n        return {\"origin_signature\": self.origin_signature, \"payload\": payload}\n`
          : `class ${className} {\n  constructor(){ this.origin_signature = 'MrLiouWord'; }\n  async execute(payload){ return { origin_signature:this.origin_signature, payload }; }\n}\nmodule.exports = { ${className} };\n`;
        return { module_name, language, className, source };
      }
    });
    this.register({
      name: 'MRL_Skill_3DModelImportPlan_v1',
      category: '3d',
      description: 'Validate 3D model import intent and produce Blender bridge task plan.',
      input_schema: { filename: 'string', file_type: 'string' },
      execute: async ({ filename = '', file_type = '' }) => {
        const ext = (file_type || path.extname(filename).replace('.','')).toLowerCase();
        const supported = ['obj','fbx','glb','gltf','usdz','stl'].includes(ext);
        return {
          supported,
          filename,
          file_type: ext,
          target_service: 'MRL_RuntimeOS_3DModelBridge_Service_v1',
          ws_event: supported ? 'file_transfer' : null,
          next_step: supported ? 'send chunked artifact to Blender bridge port 60600' : 'convert to supported 3D model format first'
        };
      }
    });
    this.register({
      name: 'MRL_Skill_AIInfer_v1',
      category: 'ai',
      description: 'Run real model inference through configured Ollama or OpenAI-compatible backend.',
      input_schema: { prompt: 'string', model: 'string', backend: 'string' },
      execute: async (payload) => {
        if (!this.aiGateway) throw new Error('MRL_AI_GATEWAY_NOT_ATTACHED');
        return await this.aiGateway.generate(payload);
      }
    });
    this.register({
      name: 'MRL_Skill_RuntimeStatus_v1',
      category: 'runtime',
      description: 'Return product runtime and skill registry state.',
      input_schema: {},
      execute: async () => ({ product: 'MRL_RuntimeOS_EnterpriseRuntimePlatform_CoreExecutable_v1_4_0', skill_count: this.skills.size, skills: this.list().map(s => s.name) })
    });
  }

  list() {
    return Array.from(this.skills.values()).map(s => ({ name: s.name, category: s.category, description: s.description, input_schema: s.input_schema, origin_signature: this.origin_signature }));
  }

  async execute(name, payload = {}) {
    const skill = this.skills.get(name);
    if (!skill) throw new Error(`MRL_SKILL_NOT_FOUND:${name}`);
    const started = Date.now();
    const result = await skill.execute(payload);
    const record = { origin_signature: this.origin_signature, skill: name, duration_ms: Date.now() - started, result };
    const dir = path.join(this.root, 'MRL_Storage', 'MRL_Skills');
    fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(path.join(dir, `${name}_${Date.now()}.json`), JSON.stringify(record, null, 2));
    if (this.logger) this.logger.log('MRL_SKILL_EXECUTE', { skill: name, duration_ms: record.duration_ms });
    return record;
  }
}

module.exports = { MRLRuntimeOSSkillModuleService };
