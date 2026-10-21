const { MRL_hash } = require('./MRL_MetaIR');

class MRLParticleIREngine {
  constructor() { this.origin_signature = 'MrLiouWord'; }

  fromMetaIR(metaIR) {
    const particles = [];
    const astNodes = metaIR.syntax_tree?.nodes || [];
    for (const node of astNodes) particles.push(this.nodeToParticle(node, particles.length + 1, metaIR));
    const particleIR = {
      mrl_ir_type: 'MRL_ParticleIR',
      version: 'v1.2.0',
      origin_signature: this.origin_signature,
      source_hash: metaIR.mrl_hash,
      source_identity: metaIR.source_identity,
      particles,
      particle_atoms: particles.map(p => ({
        atom_id: p.id,
        atom_type: p.particle_type,
        simhash_seed: MRL_hash(p).slice(0,16),
        semantic: p.semantic
      })),
      created_at: new Date().toISOString()
    };
    particleIR.mrl_hash = MRL_hash(particleIR);
    return particleIR;
  }

  nodeToParticle(node, idx, metaIR) {
    const name = node.name || node.value || `MRL_Node_${idx}`;
    const typeMap = {
      particle: 'MRL_FluinParticle', function: 'MRL_FunctionParticle', method: 'MRL_FunctionParticle',
      class: 'MRL_TypeParticle', interface: 'MRL_TypeParticle', struct: 'MRL_TypeParticle',
      json_field: 'MRL_DataFieldParticle', yaml_field: 'MRL_DataFieldParticle', sql_statement: 'MRL_SQLParticle',
      heading: 'MRL_DocumentHeadingParticle', statement: 'MRL_StatementParticle', shell_command: 'MRL_CommandParticle',
      html_tag: 'MRL_UIParticle', css_rule: 'MRL_StyleParticle'
    };
    const properties = { ...node };
    const layer = node.properties?.layer || node.properties?.['@layer'] || this.inferLayer(node);
    return {
      id: `MRL_P_${String(idx).padStart(4,'0')}`,
      particle_type: typeMap[node.kind] || 'MRL_GenericParticle',
      layer,
      source_language: metaIR.source_identity?.language || 'unknown',
      properties,
      semantic: String(name).slice(0, 500),
      origin_signature: this.origin_signature,
      status: 'implemented_runtime_particle'
    };
  }

  inferLayer(node) {
    if (node.kind === 'particle') return 'L0_Particle';
    if (['function','class','interface','struct'].includes(node.kind)) return 'L2_CodeStructure';
    if (['json_field','yaml_field','sql_statement'].includes(node.kind)) return 'L3_DataStructure';
    if (['heading','statement'].includes(node.kind)) return 'L4_SemanticText';
    return 'L5_Runtime';
  }
}

module.exports = { MRLParticleIREngine };
