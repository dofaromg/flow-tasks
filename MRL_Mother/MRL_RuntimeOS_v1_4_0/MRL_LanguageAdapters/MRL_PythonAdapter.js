class MRLPythonAdapter {
  constructor() { this.language = 'Python'; }
  parse(source) {
    const nodes = [];
    const classRegex = /^\s*class\s+([A-Za-z_][\w]*)/gm;
    const funcRegex = /^\s*def\s+([A-Za-z_][\w]*)\s*\(([^)]*)\)/gm;
    let m;
    while ((m = classRegex.exec(source))) nodes.push({ kind:'class', name:m[1] });
    while ((m = funcRegex.exec(source))) nodes.push({ kind:'function', name:m[1], params:m[2].split(',').map(s=>s.trim()).filter(Boolean) });
    if (!nodes.length) nodes.push({ kind:'statement', value:source.slice(0,1000) });
    return { language:this.language, nodes, tokens:source.split(/\s+/).filter(Boolean) };
  }
}
module.exports = { MRLPythonAdapter };
