class MRLHTMLAdapter {
  constructor() { this.language = 'HTML'; }
  parse(source) {
    const nodes = [];
    const tagRegex = /<\s*([a-zA-Z][\w-]*)\b([^>]*)>/g;
    let m;
    while ((m = tagRegex.exec(source))) nodes.push({ kind:'html_tag', name:m[1].toLowerCase(), attrs:m[2].trim() });
    if (!nodes.length) nodes.push({ kind:'statement', value:source.slice(0,1000) });
    return { language:this.language, nodes, tokens:source.split(/\s+/).filter(Boolean) };
  }
}
module.exports = { MRLHTMLAdapter };
