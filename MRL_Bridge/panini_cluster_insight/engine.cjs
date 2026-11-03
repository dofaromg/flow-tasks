'use strict';
// MRL S4.5 computation organ; origin_signature: MrLiouWord
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const Ajv = require('ajv');
const schemas = require('./schema.cjs');
const ajv = new Ajv({ strict: true, allErrors: true });
const validators = Object.fromEntries(Object.entries(schemas).map(([k, s]) => [k, ajv.compile(s)]));
const hash = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
function canonical(value) {
  if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
  if (value && typeof value === 'object') return '{' + Object.keys(value).sort().map(k => JSON.stringify(k) + ':' + canonical(value[k])).join(',') + '}';
  return JSON.stringify(value);
}
class InsightError extends Error {
  constructor(code, status = 422) { super(code); this.code = code; this.status = status; }
}
function validate(kind, value) {
  if (!validators[kind](value)) throw new InsightError('INVALID_' + kind.toUpperCase());
  return value;
}
const sourcePath = path.join(__dirname, 'sources', 'Mrliou_MRL_ParticleDict_PaniniClusterInsight_v1.0.0.json');
const sourceBytes = fs.readFileSync(sourcePath);
if (hash(sourceBytes) !== '92dd5c24c1e7f9e85b097b4fb3e54b9205d275323208c732a68105277fd0659a') throw new InsightError('CANONICAL_SOURCE_HASH_MISMATCH');
function freeze(value) {
  if (value && typeof value === 'object') { Object.values(value).forEach(freeze); Object.freeze(value); }
  return value;
}
const definition = freeze(validate('canonical', JSON.parse(sourceBytes)));
const functions = definition.subsystem_module.functions;
if (new Set(functions.map(f => f.id)).size !== 6) throw new InsightError('DUPLICATE_FUNCTION');
const names = Object.fromEntries(functions.map(f => [f.id, f.name]));

function checkSnapshot(value) {
  validate('snapshot', value);
  const roots = new Set();
  const idLayers = new Map();
  for (const cluster of value.clusters) {
    // No Unicode folding or silent renaming of canonical roots or IDs.
    if (roots.has(cluster.root)) throw new InsightError('DUPLICATE_ROOT');
    roots.add(cluster.root);
    const ids = new Set();
    for (const particle of cluster.particles) {
      if (ids.has(particle.id)) throw new InsightError('DUPLICATE_PARTICLE');
      ids.add(particle.id);
      if (idLayers.has(particle.id) && idLayers.get(particle.id) !== particle.layer) throw new InsightError('PARTICLE_LAYER_CONFLICT');
      idLayers.set(particle.id, particle.layer);
    }
  }
  return value;
}
function ontology_aspect_detector(cluster) {
  const layers = [...new Set(cluster.particles.map(p => p.layer))].sort();
  const has = (...required) => required.every(l => layers.includes(l));
  const aspects = [];
  if (has('L0', 'LC', 'LF')) aspects.push('triple_aspect');
  if (has('L0', 'LN')) aspects.push('parse_runtime_mirror');
  if (has('LF', 'LN')) aspects.push('flow_bridge');
  if (has('L0', 'LC')) aspects.push('capability_grounding');
  if (layers.length === 1) aspects.push('isolated_emergence');
  if (!aspects.length) aspects.push('cross_layer_active');
  return { cluster: cluster.root, layers, aspects };
}
function ranked(rows, field) {
  rows.sort((a, b) => b[field] - a[field] || (a.cluster < b.cluster ? -1 : a.cluster > b.cluster ? 1 : 0));
  return rows.map((r, i) => ({ ...r, rank: rows.findIndex(v => v[field] === rows[i][field]) + 1 }));
}
function cluster_activity_ranker(clusters) {
  return ranked(clusters.map(c => ({ cluster: c.root, particle_count: c.particles.length,
    layer_span: new Set(c.particles.map(p => p.layer)).size,
    activity: c.particles.length * new Set(c.particles.map(p => p.layer)).size })), 'activity');
}
function fractal_self_similarity_scorer(clusters, ratio) {
  if (!(typeof ratio === 'number' && Number.isFinite(ratio) && ratio > 0 && ratio < 1)) {
    throw new InsightError('F3_RATIO_DEFINITION_REQUIRED');
  }
  return { cluster_count: clusters.length, particle_count: new Set(clusters.flatMap(c => c.particles.map(p => p.id))).size,
    membership_count: clusters.reduce((n, c) => n + c.particles.length, 0),
    avg_cluster_size_ratio: ratio, ratio_origin: 'explicit_caller_parameter_not_defined_by_canonical',
    D: Math.log(clusters.length) / Math.log(1 / ratio),
    formula: 'log(cluster_count) / log(1/avg_cluster_size_ratio)',
    interpretation: 'canonical_formula_metric_not_empirical_fractal_proof' };
}
function panini_ontology_profiler(clusters) {
  return clusters.map(c => {
    const key = c.root === 'kriyā' ? 'key_insight_1_kriyā_activity_depth' : c.root === 'smṛti' ? 'key_insight_2_smṛti_triple_aspect' : null;
    return { cluster: c.root, source_pointer: key ? '/' + key : null,
      evidence_status: key ? 'canonical_statement_not_independently_verified' : 'profile_not_present_in_source',
      profile: key ? definition[key] : null };
  });
}
function concept_intensity_map(clusters) {
  return ranked(cluster_activity_ranker(clusters).map(({ rank: _rank, ...row }) => {
    const triple = ontology_aspect_detector(clusters.find(c => c.root === row.cluster)).aspects.includes('triple_aspect');
    return { ...row, triple_aspect_bonus: triple ? 10 : 0, intensity: row.activity + (triple ? 10 : 0) };
  }), 'intensity');
}
function downstream_module_advisor(clusters) {
  const activity = cluster_activity_ranker(clusters);
  const triple = clusters.some(c => c.root === 'smṛti' && ontology_aspect_detector(c).aspects.includes('triple_aspect'));
  const active = activity.some(c => c.cluster === 'kriyā' && c.activity === activity[0].activity);
  const sizes = new Set(clusters.map(c => c.particles.length));
  const density = sizes.size > 1 && clusters.some(c => c.particles.length === 1);
  return definition.downstream_module_suggestions.suggested_subsystems
    .filter((_, i) => [active, triple, density][i])
    .map(s => ({ ...s, status: 'recommendation_only', creates_module: false }));
}
function compute(functionId, snapshot, ratio = null) {
  checkSnapshot(snapshot);
  const clusters = snapshot.clusters;
  switch (functionId) {
    case 'F1': return cluster_activity_ranker(clusters);
    case 'F2': return clusters.map(ontology_aspect_detector);
    case 'F3': return fractal_self_similarity_scorer(clusters, ratio);
    case 'F4': return panini_ontology_profiler(clusters);
    case 'F5': return concept_intensity_map(clusters);
    case 'F6': return downstream_module_advisor(clusters);
    default: throw new InsightError('UNKNOWN_FUNCTION', 404);
  }
}

// Operator-owned catalogue only. Remote callers never select paths or upload data.
// Pin exact bytes for S4, S3.5 and their normalized projection; no writes or execution.
class DatasetRegistry {
  constructor(catalogue = {}) { this.catalogue = validate('registry', catalogue); }
  readPin(pin) {
    let bytes;
    try {
      const fd = fs.openSync(pin.filepath, 'r');
      try {
        const st = fs.fstatSync(fd);
        if (!st.isFile() || st.size > 5 * 1024 * 1024) throw new InsightError('SOURCE_SIZE_OR_TYPE');
        const buffer = Buffer.alloc(5 * 1024 * 1024 + 1);
        let size = 0; let n;
        while (size < buffer.length && (n = fs.readSync(fd, buffer, size, buffer.length - size, null)) > 0) size += n;
        bytes = buffer.subarray(0, size);
      } finally { fs.closeSync(fd); }
    } catch (e) { if (e instanceof InsightError) throw e; throw new InsightError('SOURCE_UNAVAILABLE', 503); }
    if (bytes.length > 5 * 1024 * 1024 || hash(bytes) !== pin.sha256) throw new InsightError('SOURCE_HASH_MISMATCH', 409);
    return bytes;
  }
  load(id) {
    if (!Object.hasOwn(this.catalogue, id)) throw new InsightError('DATASET_NOT_REGISTERED', 503);
    const entry = this.catalogue[id];
    if (entry.snapshot.version !== 'MRL.PaniniClusterInput/v1.0.0') throw new InsightError('SNAPSHOT_VERSION_MISMATCH', 409);
    this.readPin(entry.S4);
    this.readPin(entry.S3_5);
    if (entry.S4.version !== 'v1.0.0') throw new InsightError('UPSTREAM_VERSION_MISMATCH', 409);
    let snapshot;
    try { snapshot = JSON.parse(this.readPin(entry.snapshot)); }
    catch (e) { if (e instanceof InsightError) throw e; throw new InsightError('SOURCE_JSON_INVALID'); }
    checkSnapshot(snapshot);
    for (const key of ['S4', 'S3_5']) {
      const { ref, version, sha256 } = entry[key];
      if (canonical(snapshot.sources[key]) !== canonical({ ref, version, sha256 })) throw new InsightError('UPSTREAM_LINEAGE_MISMATCH', 409);
    }
    return { snapshot, sha256: entry.snapshot.sha256 };
  }
  call(id, args) {
    validate('call', args);
    if (!Object.hasOwn(names, id)) throw new InsightError('UNKNOWN_FUNCTION', 404);
    const { snapshot, sha256 } = this.load(args.dataset_id);
    if (args.cluster_root !== null && !['F2', 'F4'].includes(id)) throw new InsightError('CLUSTER_SELECTOR_NOT_SUPPORTED');
    let result = compute(id, snapshot, args.avg_cluster_size_ratio);
    if (args.cluster_root !== null) {
      result = result.filter(row => row.cluster === args.cluster_root);
      if (!result.length) throw new InsightError('CLUSTER_NOT_FOUND', 404);
    }
    return { ok: true, canonical_name: definition.canonical_name, schema_version: definition.schema_version,
      origin_signature: 'MrLiouWord', internal_id: definition.subsystem_module.internal_id, stage: 'S4.5',
      function: { id, name: names[id] }, dataset_id: args.dataset_id,
      lineage: { canonical_source_sha256: hash(sourceBytes), snapshot_sha256: sha256,
        upstream: snapshot.sources, verification: 'operator_registered_byte_pins_not_semantic_canonical_approval',
        input_sha256: hash(canonical(args)), implementation_version: 'MRL.PaniniAdapter/v1.0.0' },
      result, result_sha256: hash(canonical(result)), mutation: false };
  }
}
module.exports = { DatasetRegistry, InsightError, compute, checkSnapshot, validate, names, schemas, definition,
  canonical, hash, sourceBytes, cluster_activity_ranker, ontology_aspect_detector,
  fractal_self_similarity_scorer, panini_ontology_profiler, concept_intensity_map, downstream_module_advisor };
