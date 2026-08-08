class MRLShellAdapter {
  constructor() { this.language = 'Shell'; }
  parse(source) {
    const nodes = source.split(/\r?\n/).map((line, idx)=>line.trim()).filter(Boolean).map((line, idx)=>({ kind:'shell_command', name:line.split(/\s+/)[0], value:line, line:idx+1 }));
    return { language:this.language, nodes, tokens:source.split(/\s+/).filter(Boolean) };
  }
}
module.exports = { MRLShellAdapter };
