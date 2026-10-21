class MRLFPlusPlusAdapter {
  constructor() { this.language = 'MRL_FPlusPlus'; }

  parse(source) {
    const tokens = source.match(/particle|[A-Za-z_][A-Za-z0-9_]*|@[A-Za-z_][A-Za-z0-9_]*|"[^"]*"|\{|\}|:|\|>|⊕|⊗|>>=|\(|\)|,|\S/g) || [];
    const nodes = [];
    let i = 0;
    while (i < tokens.length) {
      if (tokens[i] === 'particle') {
        const name = tokens[i+1] || 'MRL_UnknownParticle';
        i += 2;
        const properties = {};
        if (tokens[i] === '{') {
          i++;
          while (i < tokens.length && tokens[i] !== '}') {
            let key = tokens[i];
            if (key && key.startsWith('@')) key = key.slice(1);
            if (tokens[i+1] === ':') {
              let value = tokens[i+2];
              if (value && value.startsWith('"') && value.endsWith('"')) value = value.slice(1,-1);
              properties[key] = value;
              i += 3;
            } else i++;
          }
          if (tokens[i] === '}') i++;
        }
        nodes.push({ kind: 'particle', name, properties });
      } else {
        nodes.push({ kind: 'operator_or_token', value: tokens[i] });
        i++;
      }
    }
    return { language: this.language, nodes, tokens };
  }
}
module.exports = { MRLFPlusPlusAdapter };
