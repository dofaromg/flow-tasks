class MRLNaturalLanguageAdapter {
  constructor() { this.language = 'NaturalLanguage'; }
  parse(source) {
    const sentences = source.split(/[。.!?？\n]+/).map(s=>s.trim()).filter(Boolean);
    const nodes = sentences.map((s, idx)=>({ kind:'statement', name:`MRL_Sentence_${idx+1}`, value:s, intent:this.inferIntent(s) }));
    return { language:this.language, nodes, tokens:source.split(/\s+|，|,|。/).filter(Boolean) };
  }
  inferIntent(s) {
    if (/整理|organize|分類/.test(s)) return 'MRL_INTENT_ORGANIZE';
    if (/分析|analyze|解析/.test(s)) return 'MRL_INTENT_ANALYZE';
    if (/寫|生成|create|build/.test(s)) return 'MRL_INTENT_CREATE';
    return 'MRL_INTENT_GENERAL';
  }
}
module.exports = { MRLNaturalLanguageAdapter };
