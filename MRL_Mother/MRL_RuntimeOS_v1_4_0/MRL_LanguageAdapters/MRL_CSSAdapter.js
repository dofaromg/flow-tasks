class MRLCSSAdapter {
  constructor() { this.language = 'CSS'; }
  parse(source) {
    const nodes = [];
    const ruleRegex = /([^{}]+)\{([^{}]*)\}/g;
    let m;
    while ((m = ruleRegex.exec(source))) nodes.push({ kind:'css_rule', name:m[1].trim(), declarations:m[2].trim() });
    if (!nodes.length) nodes.push({ kind:'statement', value:source.slice(0,1000) });
    return { language:this.language, nodes, tokens:source.split(/\s+/).filter(Boolean) };
  }
}
module.exports = { MRLCSSAdapter };
