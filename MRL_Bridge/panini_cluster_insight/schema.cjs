'use strict';
// origin_signature: MrLiouWord
const str = { type: 'string', minLength: 1, maxLength: 1024 };
const digest = { type: 'string', pattern: '^[a-f0-9]{64}$' };
const object = (properties, required = Object.keys(properties)) => ({
  type: 'object', properties, required, additionalProperties: false,
});
const source = object({ ref: str, version: str, sha256: digest });
const snapshot = object({
  schema_version: { const: 'MRL.PaniniClusterInput/v1.0.0' },
  origin_signature: { const: 'MrLiouWord' },
  sources: object({ S4: source, S3_5: source }),
  clusters: { type: 'array', minItems: 1, maxItems: 1024, items: object({
    root: str,
    particles: { type: 'array', minItems: 1, maxItems: 4096, items: object({
      id: str, layer: { enum: ['L0', 'LC', 'LF', 'LN'] },
    }) },
  }) },
});
const call = object({
  dataset_id: { type: 'string', pattern: '^[A-Za-z0-9_.-]{1,80}$' },
  expected_schema_version: { const: 'panini_cluster_insight/v1.0.0' },
  cluster_root: { anyOf: [str, { type: 'null' }] },
  avg_cluster_size_ratio: { anyOf: [{ type: 'number', exclusiveMinimum: 0, exclusiveMaximum: 1 }, { type: 'null' }] },
});
const canonical = {
  type: 'object', required: ['canonical_name', 'schema_version', 'origin_signature', 'stage', 'subsystem_module', 'lineage'],
  properties: {
    canonical_name: { const: 'Mrliou_MRL_ParticleDict_PaniniClusterInsight_v1.0.0' },
    schema_version: { const: 'panini_cluster_insight/v1.0.0' },
    origin_signature: { const: 'MrLiouWord' }, stage: { const: 'S4.5' },
    subsystem_module: { type: 'object', required: ['internal_id', 'functions'], properties: {
      internal_id: { const: 'Mrliou.ParticleDict.PaniniClusterInsight.v1' },
      functions: { type: 'array', minItems: 6, maxItems: 6, items: {
        type: 'object', required: ['id', 'name'], properties: { id: { enum: ['F1', 'F2', 'F3', 'F4', 'F5', 'F6'] }, name: str },
      } },
    } },
    lineage: { type: 'array', minItems: 1 },
  },
};
const pin = object({ filepath: str, sha256: digest, ref: str, version: str });
const registry = {
  type: 'object', maxProperties: 256, propertyNames: { pattern: '^[A-Za-z0-9_.-]{1,80}$' },
  additionalProperties: object({ snapshot: pin, S4: pin, S3_5: pin }),
};
module.exports = { snapshot, call, canonical, registry };
