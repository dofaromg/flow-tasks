class MRLYAMLAdapter {
  constructor() { this.language = 'YAML'; }
  parse(source) {
    const nodes = [];
    const lines = source.split(/\r?\n/);
    for (const [idx,line] of lines.entries()) {
      const m = line.match(/^\s*([A-Za-z_][\w.-]*)\s*:\s*(.*)$/);
      if (m) nodes.push({ kind:'yaml_field', name:m[1], value_type:m[2] ? 'scalar' : 'object', line:idx+1 });
    }
    if (!nodes.length) nodes.push({ kind:'statement', value:source.slice(0,1000) });
    return { language:this.language, nodes, tokens:lines.flatMap(l=>l.split(/\s+/)).filter(Boolean) };
  }
}
module.exports = { MRLYAMLAdapter };
