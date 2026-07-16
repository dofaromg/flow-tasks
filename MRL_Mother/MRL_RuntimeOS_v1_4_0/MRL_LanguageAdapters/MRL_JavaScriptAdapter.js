class MRLJavaScriptAdapter {
  constructor() { this.language = 'JavaScript'; }
  parse(source) {
    const functionRegex = /function\s+([A-Za-z_$][\w$]*)\s*\(([^)]*)\)|(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*\(([^)]*)\)\s*=>/g;
    const nodes = [];
    let match;
    while ((match = functionRegex.exec(source))) {
      nodes.push({ kind: 'function', name: match[1] || match[3], params: (match[2] || match[4] || '').split(',').map(s=>s.trim()).filter(Boolean) });
    }
    if (!nodes.length) nodes.push({ kind: 'statement', value: source.slice(0, 500) });
    return { language: this.language, nodes, tokens: source.split(/\s+/).filter(Boolean) };
  }
}
module.exports = { MRLJavaScriptAdapter };
