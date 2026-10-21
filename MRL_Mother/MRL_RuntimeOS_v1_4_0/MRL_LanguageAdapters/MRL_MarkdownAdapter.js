class MRLMarkdownAdapter {
  constructor() { this.language = 'Markdown'; }
  parse(source) {
    const lines = source.split(/\r?\n/);
    const nodes = lines.map((line, idx) => {
      const h = line.match(/^(#+)\s+(.*)/);
      if (h) return { kind: 'heading', level: h[1].length, value: h[2], line: idx + 1 };
      return { kind: 'statement', value: line, line: idx + 1 };
    }).filter(n => n.value && n.value.trim());
    return { language: this.language, nodes, tokens: lines.flatMap(l=>l.split(/\s+/)).filter(Boolean) };
  }
}
module.exports = { MRLMarkdownAdapter };
