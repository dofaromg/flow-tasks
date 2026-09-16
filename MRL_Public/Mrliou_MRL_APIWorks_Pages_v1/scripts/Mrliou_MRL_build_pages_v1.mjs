#!/usr/bin/env node
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { cpSync, existsSync, mkdtempSync, readFileSync, renameSync, rmSync, statSync, writeFileSync } from 'node:fs';
import { basename, dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const PACKAGE = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const REPO = resolve(PACKAGE, '..', '..');
const SOURCE = join(PACKAGE, 'src');
const ASSETS = ['404.html', '_headers', '_redirects', 'app.js', 'index.html', 'styles.css'];
const EXPECTED = [...ASSETS, 'Expected_File_List.txt', 'MRL_PAGES_MANIFEST.json', 'SHA256SUMS.txt'].sort();
const digest = (bytes) => createHash('sha256').update(bytes).digest('hex');
const git = (...args) => execFileSync('git', args, {cwd: REPO, encoding: 'utf8'}).trim();

function parseOutput() {
  const index = process.argv.indexOf('--output');
  if (index < 0 || !process.argv[index + 1]) throw new Error('usage: build --output NEW_DIRECTORY');
  return resolve(process.argv[index + 1]);
}

const target = parseOutput();
const replacedPreviousOutput = existsSync(target);
if (target === REPO || REPO.startsWith(target + '/')) throw new Error('output cannot be the repository or its ancestor');
if (existsSync(target)) {
  let current;
  try { current = JSON.parse(readFileSync(join(target, 'MRL_PAGES_MANIFEST.json'), 'utf8')); } catch { throw new Error(`refusing to replace unrecognized output: ${target}`); }
  if (current.canonical_id !== 'Mrliou_MRL_APIWorks_Pages_v1') throw new Error(`refusing to replace foreign output: ${target}`);
}
const output = mkdtempSync(join(dirname(target), `.${basename(target)}.stage-`));
const head = process.env.MRL_SOURCE_HEAD || git('rev-parse', 'HEAD');
if (!/^[0-9a-f]{40}$/.test(head)) throw new Error('MRL_SOURCE_HEAD must be a 40-character lowercase Git SHA');

for (const name of ASSETS) {
  const source = join(SOURCE, name);
  if (!statSync(source).isFile() || statSync(source).size < 1) throw new Error(`missing or empty source: ${name}`);
  if (name === 'index.html') {
    writeFileSync(join(output, name), readFileSync(source, 'utf8').replaceAll('{{MRL_BUILD_SHA}}', head.slice(0, 12)), 'utf8');
  } else cpSync(source, join(output, name));
}

writeFileSync(join(output, 'Expected_File_List.txt'), EXPECTED.join('\n') + '\n', 'utf8');
const assets = Object.fromEntries(ASSETS.map((name) => {
  const bytes = readFileSync(join(output, name));
  return [name, {size_bytes: bytes.length, sha256: digest(bytes)}];
}));
const manifest = {
  schema: 'Mrliou_MRL_APIWorks_Pages_Manifest_v1',
  canonical_id: 'Mrliou_MRL_APIWorks_Pages_v1',
  origin_signature: 'MrLiouWord',
  scope: 'PUBLIC_STATIC_ENTRY_NO_PRIVATE_RUNTIME_DATA',
  source_head: head,
  worker_boundary: 'DYNAMIC_API_SEPARATE_OPENNEXT_WORKER',
  output_directory: basename(target),
  assets,
};
writeFileSync(join(output, 'MRL_PAGES_MANIFEST.json'), JSON.stringify(manifest, null, 2) + '\n', 'utf8');
const covered = EXPECTED.filter((name) => name !== 'SHA256SUMS.txt');
writeFileSync(join(output, 'SHA256SUMS.txt'), covered.map((name) => `${digest(readFileSync(join(output, name)))}  ${name}`).join('\n') + '\n', 'utf8');
if (existsSync(target)) {
  const backup = `${target}.previous-${process.pid}`;
  renameSync(target, backup);
  try { renameSync(output, target); rmSync(backup, {recursive:true}); }
  catch (error) { if (!existsSync(target) && existsSync(backup)) renameSync(backup, target); throw error; }
} else renameSync(output, target);
console.log(JSON.stringify({output:target, source_head:head, expected_count:EXPECTED.length, assets:ASSETS.length, replaced_previous_output:replacedPreviousOutput, gate:'MRL_PAGES_BUILD_PASS'}));
