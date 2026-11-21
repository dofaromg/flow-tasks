#!/usr/bin/env node
'use strict';
// Requested-vs-delivered file evidence; origin_signature: MrLiouWord
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const root = path.resolve(__dirname, '../..');
const prefix = 'MRL_Bridge/panini_cluster_insight/';
const expected = [
  'CHANGELOG.md', 'MRL_Bridge/package.json', 'MRL_Bridge/package-lock.json', 'MRL_Bridge/server.js',
  '.github/workflows/MRL_Panini_Cluster_Insight.yml',
  'config/Mrliou_MRL_Sync_Delivery_v1.json', 'config/Mrliou_Structure_Authorization_Delivery_v1.json',
  ...['schema.cjs', 'engine.cjs', 'adapter.cjs', 'mcp_stdio.cjs', 'contracts.cjs', 'register_dataset.cjs', 'test.cjs', 'audit.cjs', 'README.md',
    'chatgpt_tools.json', 'openapi.json', 'input.schema.json', 'call.schema.json', 'canonical.schema.json', 'catalogue.schema.json', 'output.schema.json',
    'sources/Mrliou_MRL_ParticleDict_PaniniClusterInsight_v1.0.0.json'].map(p => prefix + p),
].sort();
function digest(bytes) { return crypto.createHash('sha256').update(bytes).digest('hex'); }
function evidence() {
  const missing = expected.filter(p => !fs.existsSync(path.join(root, p)));
  const files = expected.filter(p => !missing.includes(p)).map(p => {
    const bytes = fs.readFileSync(path.join(root, p));
    return { path: p, size: bytes.length, sha256: digest(bytes) };
  });
  const walk = dir => fs.readdirSync(dir, { withFileTypes: true }).flatMap(e => e.isDirectory() ? walk(path.join(dir, e.name)) : [path.relative(root, path.join(dir, e.name)).split(path.sep).join('/')]);
  const unexpected = walk(__dirname).filter(p => !expected.includes(p) && p !== prefix + 'DELIVERY_AUDIT.json').sort();
  return { origin_signature: 'MrLiouWord', base_commit: '36dc69d98ec3e28e5cca744e82013ed32b203b61',
    expected_file_list: expected, files, missing_files: missing, empty_files: files.filter(f => !f.size).map(f => f.path),
    unexpected_files: unexpected, file_coverage_percent: 100 * files.filter(f => f.size > 0).length / expected.length,
    hash_scope: 'exact_file_bytes', audit_report_self_hash: 'printed_by_verifier_outside_this_report',
    dependency_tree: { parent: 'MRL_Bridge/server.js', input: ['original S3.5 FxDualContextBridge', 'original S4 CrossLayerIDMap v1.0.0', 'operator-verified pinned projection'],
      chain: ['schema.cjs', 'engine.cjs', 'adapter.cjs', 'existing Bridge admission/audit', 'OpenAPI / function-dispatch / MCP stdio'],
      child: 'S5 ReversibilityBatchTest priority consumer (not implemented by this change)' },
    package_map: { deployment: 'existing MRL_Bridge checkout; no ZIP requested', source: prefix + 'sources/',
      tools: prefix + 'chatgpt_tools.json', actions: prefix + 'openapi.json', mcp: prefix + 'mcp_stdio.cjs',
      tests: prefix + 'test.cjs', ci: '.github/workflows/MRL_Panini_Cluster_Insight.yml' },
    open_gates: ['recover actual S3.5/S4 and parent/companion source definitions', 'verify normalization against mother originals and register byte pins',
      'deploy reviewed branch to existing mother Bridge with dedicated read credential', 'perform live F1-F6 and ChatGPT tool-host invocation'],
    overall_delivery: 'DELIVERY_FAIL_PENDING_LIVE_AND_UPSTREAM_GATES' };
}
if (require.main === module) {
  const file = path.join(__dirname, 'DELIVERY_AUDIT.json');
  const report = evidence();
  if (process.argv.includes('--check')) {
    const stored = JSON.parse(fs.readFileSync(file));
    if (JSON.stringify(stored) !== JSON.stringify(report) || report.missing_files.length || report.empty_files.length || report.unexpected_files.length) {
      process.stderr.write('MRL_FILE_AUDIT_FAIL\n'); process.exitCode = 1;
    } else process.stdout.write(JSON.stringify({ file_coverage_percent: report.file_coverage_percent, payload_files: report.files.length,
      audit_report_sha256: digest(fs.readFileSync(file)), overall_delivery: report.overall_delivery }) + '\n');
  } else fs.writeFileSync(file, JSON.stringify(report, null, 2) + '\n');
}
module.exports = { expected, evidence };
