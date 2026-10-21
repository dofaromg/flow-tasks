class MRLSQLAdapter {
  constructor() { this.language = 'SQL'; }
  parse(source) {
    const statements = source.split(';').map(s=>s.trim()).filter(Boolean);
    const nodes = statements.map((s, i) => {
      const table = (s.match(/(?:CREATE\s+TABLE|FROM|INTO|UPDATE)\s+([A-Za-z_][\w]*)/i)||[])[1] || `MRL_SQL_${i+1}`;
      return { kind:'sql_statement', name:table, operation:(s.match(/^\s*(\w+)/)||[])[1]?.toUpperCase() || 'SQL', value:s };
    });
    return { language:this.language, nodes, tokens:source.split(/\s+/).filter(Boolean) };
  }
}
module.exports = { MRLSQLAdapter };
