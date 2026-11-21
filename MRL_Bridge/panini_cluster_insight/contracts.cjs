'use strict';
// origin_signature: MrLiouWord
const fs = require('node:fs');
const path = require('node:path');
const { tools, PREFIX } = require('./adapter.cjs');
const { names, schemas } = require('./engine.cjs');
const outputSchema = {
  type: 'object', additionalProperties: false,
  required: ['ok', 'canonical_name', 'schema_version', 'origin_signature', 'internal_id', 'stage', 'function', 'dataset_id', 'lineage', 'result', 'result_sha256', 'mutation'],
  properties: {
    ok: { const: true }, canonical_name: { const: 'Mrliou_MRL_ParticleDict_PaniniClusterInsight_v1.0.0' },
    schema_version: { const: 'panini_cluster_insight/v1.0.0' }, origin_signature: { const: 'MrLiouWord' },
    internal_id: { const: 'Mrliou.ParticleDict.PaniniClusterInsight.v1' }, stage: { const: 'S4.5' },
    function: { type: 'object', additionalProperties: false, required: ['id', 'name'], properties: {
      id: { enum: Object.keys(names) }, name: { enum: Object.values(names) },
    } },
    dataset_id: schemas.call.properties.dataset_id,
    lineage: { type: 'object', additionalProperties: false,
      required: ['canonical_source_sha256', 'snapshot_sha256', 'upstream', 'verification', 'input_sha256', 'implementation_version'],
      properties: {
        canonical_source_sha256: { type: 'string', pattern: '^[a-f0-9]{64}$' },
        snapshot_sha256: { type: 'string', pattern: '^[a-f0-9]{64}$' },
        upstream: schemas.snapshot.properties.sources,
        verification: { const: 'operator_registered_byte_pins_not_semantic_canonical_approval' },
        input_sha256: { type: 'string', pattern: '^[a-f0-9]{64}$' },
        implementation_version: { const: 'MRL.PaniniAdapter/v1.0.0' },
      },
    },
    result: { anyOf: [{ type: 'array', items: { type: 'object' } }, { type: 'object' }] },
    result_sha256: { type: 'string', pattern: '^[a-f0-9]{64}$' }, mutation: { const: false },
  },
};
function contracts() {
  const paths = {};
  for (const [id, name] of Object.entries(names)) paths[PREFIX + '/' + id] = { post: {
    operationId: name, summary: `MRL S4.5 ${id} read/compute`, 'x-openai-isConsequential': false,
    security: [{ MRLReadKey: [] }],
    requestBody: { required: true, content: { 'application/json': { schema: schemas.call } } },
    responses: { 200: { description: 'Deterministic result; byte-pinned provenance, no mother mutation.',
      content: { 'application/json': { schema: outputSchema } } },
      default: { description: '401/403 read permission; 409 pin or lineage mismatch; 413 body limit; 415 media type; 422 invalid input; 503 unregistered/unavailable dataset.' } },
  } };
  return {
    'chatgpt_tools.json': tools,
    'openapi.json': { openapi: '3.1.0', info: { title: 'MRL PaniniClusterInsight Bridge', version: '1.0.0' },
      servers: [{ url: 'https://bridge.mrliouword.com' }], paths,
      components: { securitySchemes: { MRLReadKey: { type: 'apiKey', in: 'header', name: 'x-api-key' } } } },
    'input.schema.json': schemas.snapshot, 'call.schema.json': schemas.call,
    'canonical.schema.json': schemas.canonical, 'catalogue.schema.json': schemas.registry,
    'output.schema.json': outputSchema,
  };
}
if (require.main === module) {
  for (const [filename, value] of Object.entries(contracts())) fs.writeFileSync(path.join(__dirname, filename), JSON.stringify(value, null, 2) + '\n');
}
module.exports = { contracts, outputSchema };
