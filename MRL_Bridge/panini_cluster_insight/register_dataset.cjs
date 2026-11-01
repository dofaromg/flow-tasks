#!/usr/bin/env node
'use strict';
// Operator-side byte-pin registration. Never changes mother source documents.
// origin_signature: MrLiouWord
const fs = require('node:fs');
const path = require('node:path');
const { DatasetRegistry, checkSnapshot, hash } = require('./engine.cjs');
function register({ id, snapshotPath, s4Path, s35Path, output }) {
  const snapshotBytes = fs.readFileSync(snapshotPath);
  const snapshot = checkSnapshot(JSON.parse(snapshotBytes));
  const pin = (filepath, metadata) => ({ filepath: path.resolve(filepath), ...metadata, sha256: hash(fs.readFileSync(filepath)) });
  const catalogue = { [id]: {
    snapshot: pin(snapshotPath, { ref: 'MRL.PaniniClusterInput:' + id, version: 'MRL.PaniniClusterInput/v1.0.0' }),
    S4: pin(s4Path, snapshot.sources.S4), S3_5: pin(s35Path, snapshot.sources.S3_5),
  } };
  // Validate supplied hashes/refs against real upstream bytes before any write.
  new DatasetRegistry(catalogue).load(id);
  fs.writeFileSync(output, JSON.stringify(catalogue, null, 2) + '\n', { flag: 'wx', mode: 0o600 });
  return { dataset_id: id, snapshot_sha256: hash(snapshotBytes), source_mutations: 0 };
}
if (require.main === module) {
  const [id, snapshotPath, s4Path, s35Path, output, ...extra] = process.argv.slice(2);
  try {
    if (!output || extra.length) throw new Error('USAGE: node register_dataset.cjs ID NORMALIZED_JSON S4_ORIGINAL S3_5_ORIGINAL NEW_CATALOGUE_JSON');
    process.stdout.write(JSON.stringify(register({ id, snapshotPath, s4Path, s35Path, output })) + '\n');
  } catch (_) { process.stderr.write('MRL_DATASET_REGISTRATION_FAILED: verify paths, source pins, schema and exclusive output\n'); process.exitCode = 1; }
}
module.exports = { register };
