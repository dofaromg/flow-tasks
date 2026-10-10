#!/usr/bin/env node
import { createHash } from 'node:crypto';
import { lstatSync, readFileSync, readdirSync } from 'node:fs';
import { basename, resolve } from 'node:path';

const root = resolve(process.argv[2] || 'out');
const digest = (bytes) => createHash('sha256').update(bytes).digest('hex');
const expected = ['404.html','Expected_File_List.txt','MRL_PAGES_MANIFEST.json','SHA256SUMS.txt','_headers','_redirects','app.js','index.html','styles.css'].sort();
const declaredExpected = readFileSync(resolve(root, 'Expected_File_List.txt'), 'utf8').trim().split(/\r?\n/).filter(Boolean).sort();
const actual = readdirSync(root, {withFileTypes: true}).map((entry) => entry.name).sort();
const missing = expected.filter((name) => !actual.includes(name));
const extra = actual.filter((name) => !expected.includes(name));
const empty = actual.filter((name) => lstatSync(resolve(root, name)).isFile() && lstatSync(resolve(root, name)).size === 0);
const linked = actual.filter((name) => lstatSync(resolve(root, name)).isSymbolicLink());
const nonfiles = actual.filter((name) => !lstatSync(resolve(root, name)).isFile());
const checksumFailures = [];
if (JSON.stringify(declaredExpected) !== JSON.stringify(expected)) checksumFailures.push('Expected_File_List.txt does not match canonical output inventory');
const checksumLines = readFileSync(resolve(root, 'SHA256SUMS.txt'), 'utf8').trim().split(/\r?\n/).filter(Boolean);
const seen = new Set();
for (const line of checksumLines) {
  const match = line.match(/^([0-9a-f]{64})  ([^/\\]+)$/);
  if (!match || seen.has(match?.[2])) { checksumFailures.push(`invalid checksum line: ${line}`); continue; }
  const [, expectedHash, name] = match; seen.add(name);
  if (!expected.includes(name) || name === 'SHA256SUMS.txt') checksumFailures.push(`unexpected checksum member: ${name}`);
  else if (digest(readFileSync(resolve(root, name))) !== expectedHash) checksumFailures.push(`checksum mismatch: ${name}`);
}
const covered = expected.filter((name) => name !== 'SHA256SUMS.txt');
for (const name of covered) if (!seen.has(name)) checksumFailures.push(`checksum missing: ${name}`);

const manifestFailures = [];
let manifest = {};
try { manifest = JSON.parse(readFileSync(resolve(root, 'MRL_PAGES_MANIFEST.json'), 'utf8')); } catch (error) { manifestFailures.push(`manifest parse: ${error.message}`); }
if (manifest.schema !== 'Mrliou_MRL_APIWorks_Pages_Manifest_v1') manifestFailures.push('manifest schema mismatch');
if (manifest.canonical_id !== 'Mrliou_MRL_APIWorks_Pages_v1') manifestFailures.push('manifest canonical_id mismatch');
if (manifest.origin_signature !== 'MrLiouWord') manifestFailures.push('manifest origin mismatch');
if (!/^[0-9a-f]{40}$/.test(manifest.source_head || '')) manifestFailures.push('manifest source_head invalid');
if (manifest.output_directory !== basename(root)) manifestFailures.push('manifest output_directory mismatch');
const assetNames = ['404.html', '_headers', '_redirects', 'app.js', 'index.html', 'styles.css'];
if (JSON.stringify(Object.keys(manifest.assets || {}).sort()) !== JSON.stringify(assetNames)) manifestFailures.push('manifest asset coverage mismatch');
for (const name of assetNames) {
  const identity = manifest.assets?.[name];
  const bytes = readFileSync(resolve(root, name));
  if (!identity || identity.size_bytes !== bytes.length || identity.sha256 !== digest(bytes)) manifestFailures.push(`manifest identity mismatch: ${name}`);
}
const failures = [...missing, ...extra, ...empty, ...linked, ...nonfiles, ...checksumFailures, ...manifestFailures];
const result = {scope:'MRL_PAGES_OUTPUT_INTEGRITY',expected_count:expected.length,actual_count:actual.length,missing,extra,empty,linked,nonfiles,checksum_failures:checksumFailures,manifest_failures:manifestFailures,integrity_gate:failures.length?'FAIL':'PASS'};
console.log(JSON.stringify(result, null, 2));
process.exitCode = failures.length ? 1 : 0;
