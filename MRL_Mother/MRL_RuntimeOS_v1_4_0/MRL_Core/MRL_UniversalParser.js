const { MRLFPlusPlusAdapter } = require('../MRL_LanguageAdapters/MRL_FPlusPlusAdapter');
const { MRLJavaScriptAdapter } = require('../MRL_LanguageAdapters/MRL_JavaScriptAdapter');
const { MRLJSONAdapter } = require('../MRL_LanguageAdapters/MRL_JSONAdapter');
const { MRLMarkdownAdapter } = require('../MRL_LanguageAdapters/MRL_MarkdownAdapter');
const { MRLCppAdapter } = require('../MRL_LanguageAdapters/MRL_CppAdapter');
const { MRLPythonAdapter } = require('../MRL_LanguageAdapters/MRL_PythonAdapter');
const { MRLSQLAdapter } = require('../MRL_LanguageAdapters/MRL_SQLAdapter');
const { MRLYAMLAdapter } = require('../MRL_LanguageAdapters/MRL_YAMLAdapter');
const { MRLHTMLAdapter } = require('../MRL_LanguageAdapters/MRL_HTMLAdapter');
const { MRLCSSAdapter } = require('../MRL_LanguageAdapters/MRL_CSSAdapter');
const { MRLShellAdapter } = require('../MRL_LanguageAdapters/MRL_ShellAdapter');
const { MRLNaturalLanguageAdapter } = require('../MRL_LanguageAdapters/MRL_NaturalLanguageAdapter');
const { MRLMetaIRCompiler, MRL_hash } = require('./MRL_MetaIR');
const { MRLParticleIREngine } = require('./MRL_ParticleIR');

class MRLUniversalParserCore {
  constructor() {
    this.origin_signature = 'MrLiouWord';
    const fpp = new MRLFPlusPlusAdapter();
    this.adapters = {
      fpp, fltnz:fpp, flpkg:fpp,
      js:new MRLJavaScriptAdapter(), ts:new MRLJavaScriptAdapter(), jsx:new MRLJavaScriptAdapter(), tsx:new MRLJavaScriptAdapter(),
      json:new MRLJSONAdapter(), md:new MRLMarkdownAdapter(), markdown:new MRLMarkdownAdapter(),
      cpp:new MRLCppAdapter(), cc:new MRLCppAdapter(), hpp:new MRLCppAdapter(), h:new MRLCppAdapter(), cxx:new MRLCppAdapter(),
      py:new MRLPythonAdapter(), python:new MRLPythonAdapter(),
      sql:new MRLSQLAdapter(), yaml:new MRLYAMLAdapter(), yml:new MRLYAMLAdapter(),
      html:new MRLHTMLAdapter(), htm:new MRLHTMLAdapter(), css:new MRLCSSAdapter(), sh:new MRLShellAdapter(), bash:new MRLShellAdapter(), txt:new MRLNaturalLanguageAdapter(), nl:new MRLNaturalLanguageAdapter()
    };
    this.metaCompiler = new MRLMetaIRCompiler();
    this.particleEngine = new MRLParticleIREngine();
  }

  detectLanguage(source, filename = '') {
    const ext = filename.includes('.') ? filename.split('.').pop().toLowerCase() : '';
    if (ext && this.adapters[ext]) return ext;
    if (/^\s*particle\s+/m.test(source) || source.includes('⋄fx.')) return 'fpp';
    if (/^\s*[\[{]/.test(source)) return 'json';
    if (/^\s*#\s+/m.test(source)) return 'md';
    if (/<html|<div|<script|<!doctype/i.test(source)) return 'html';
    if (/^\s*(SELECT|CREATE|INSERT|UPDATE|DELETE)\b/i.test(source)) return 'sql';
    if (/^\s*def\s+|^\s*class\s+/m.test(source)) return 'py';
    if (/class\s+\w+|#include|std::/.test(source)) return 'cpp';
    if (/function\s+|const\s+|let\s+|=>/.test(source)) return 'js';
    return 'txt';
  }

  parseToAll(source, filename = 'MRL_Input.fpp') {
    if (typeof source !== 'string') source = JSON.stringify(source, null, 2);
    const lang = this.detectLanguage(source, filename);
    const adapter = this.adapters[lang] || this.adapters.txt;
    const ast = adapter.parse(source);
    const semanticIntent = this.extractIntent(ast, source);
    const sourceHash = MRL_hash({ source, filename });
    const metaIR = this.metaCompiler.compile({ filename, language: ast.language, detected: lang, source_hash: sourceHash }, ast, semanticIntent);
    const particleIR = this.particleEngine.fromMetaIR(metaIR);
    metaIR.particle_atoms = particleIR.particle_atoms;
    return { ast, metaIR, particleIR };
  }

  extractIntent(ast, source) {
    const lower = source.toLowerCase();
    const intents = [];
    const add = v => { if (!intents.includes(v)) intents.push(v); };
    if (/(execute|run|執行|啟動)/i.test(source)) add('MRL_INTENT_EXECUTE');
    if (/(verify|test|驗證|測試)/i.test(source)) add('MRL_INTENT_VERIFY');
    if (/(particle|⋄fx|粒子)/i.test(source)) add('MRL_INTENT_PARTICLE_RUNTIME');
    if (/(context|上下文|關聯)/i.test(source)) add('MRL_INTENT_CONTEXT');
    if (/(attention|注意力|權重)/i.test(source)) add('MRL_INTENT_ATTENTION');
    if (/(file|文件|檔案|整理|分類)/i.test(source)) add('MRL_INTENT_FILE_ORGANIZE');
    if (/(code|程式|function|class)/i.test(source)) add('MRL_INTENT_CODE_ANALYZE');
    if (!intents.length) add('MRL_INTENT_GENERAL_PARSE');
    return { intents, summary: intents.join(','), node_count: ast?.nodes?.length || 0, language: ast?.language };
  }
}
module.exports = { MRLUniversalParserCore };
