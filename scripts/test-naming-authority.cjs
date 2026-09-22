// origin_signature: MrLiouWord
const test = require('node:test');
const assert = require('node:assert/strict');
const { toMRLNodeId } = require('./update-neural-map');
const { validateMRLNaming } = require('./generate-mermaid');
const names = [
  'Mrliou_MRL_sync_operations_20260907_v1',
  'Mrliou_MRL_OuterAutomation_ProtectedBridge_v1',
  'Mrliou_MRL_SourceToProduct_ParallelLink_v1',
];
const map = (id, source) => ({ neural_network: {
  nodes: [{ id, source_branch: source }], synapses: [],
} });
for (const name of names) {
  test(`preserves ${name} exactly and idempotently`, () => {
    assert.equal(toMRLNodeId(name), name);
    assert.equal(toMRLNodeId(toMRLNodeId(name)), name);
    assert.equal(validateMRLNaming(map(name, name)), true);
  });
  test(`rejects historical wrong-order projection of ${name}`, () => {
    assert.throws(() => validateMRLNaming(map(name.replace('Mrliou_MRL_', 'MRL_Mrliou_'), name)), /authority violation/);
  });
}
test('retains legacy namespace behavior without changing owned-name case', () => {
  assert.equal(toMRLNodeId('main'), 'MRL_main');
  assert.equal(toMRLNodeId('mrl_existing'), 'MRL_existing');
  assert.equal(toMRLNodeId('mrliou_mrl_Case'), 'mrliou_mrl_Case');
  assert.throws(() => toMRLNodeId('Mrliou_MRL_'));
  assert.throws(() => toMRLNodeId('MRL_'));
});
test('rejects dangling edges and duplicate identities', () => {
  const data = map(names[0], names[0]);
  data.neural_network.synapses.push({ from: names[0], to: 'missing' });
  assert.throws(() => validateMRLNaming(data), /chain violation/);
  data.neural_network.synapses = [];
  data.neural_network.nodes.push({ ...data.neural_network.nodes[0] });
  assert.throws(() => validateMRLNaming(data), /collision/);
});
