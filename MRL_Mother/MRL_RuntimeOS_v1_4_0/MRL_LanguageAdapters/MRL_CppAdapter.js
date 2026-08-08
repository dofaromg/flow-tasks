class MRLCppAdapter {
  constructor() { this.language = 'C++'; }
  parse(source) {
    const nodes = [];
    const classRegex = /class\s+([A-Za-z_][\w]*)/g;
    const funcRegex = /([A-Za-z_][\w:<>&*\s]+)\s+([A-Za-z_][\w]*)\s*\(([^)]*)\)\s*[{;]/g;
    let m;
    while ((m = classRegex.exec(source))) nodes.push({ kind: 'class', name: m[1] });
    while ((m = funcRegex.exec(source))) nodes.push({ kind: 'function', name: m[2], return_type: m[1].trim(), params: m[3] });
    if (!nodes.length) nodes.push({ kind: 'statement', value: source.slice(0,500) });
    return { language: this.language, nodes, tokens: source.split(/\s+/).filter(Boolean) };
  }
}
module.exports = { MRLCppAdapter };
