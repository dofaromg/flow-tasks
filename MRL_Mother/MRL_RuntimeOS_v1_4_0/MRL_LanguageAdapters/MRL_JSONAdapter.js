class MRLJSONAdapter {
  constructor() { this.language = 'JSON'; }
  parse(source) {
    let obj;
    try { obj = JSON.parse(source); } catch (e) { throw new Error(`MRL_JSON_PARSE_FAIL: ${e.message}`); }
    const nodes = [];
    const walk = (value, path='root') => {
      if (value && typeof value === 'object' && !Array.isArray(value)) {
        for (const k of Object.keys(value)) {
          const child = `${path}.${k}`;
          nodes.push({ kind:'json_field', name:child, value_type:Array.isArray(value[k]) ? 'array' : typeof value[k] });
          walk(value[k], child);
        }
      } else if (Array.isArray(value)) {
        nodes.push({ kind:'json_field', name:path, value_type:'array', length:value.length });
      }
    };
    walk(obj);
    if (!nodes.length) nodes.push({ kind:'json_field', name:'root', value_type:typeof obj });
    return { language:this.language, nodes, tokens:Object.keys(obj || {}) };
  }
}
module.exports = { MRLJSONAdapter };
