#!/usr/bin/env node
import { lstatSync, readFileSync, readdirSync } from 'node:fs';
import { dirname, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const PACKAGE = resolve(dirname(fileURLToPath(import.meta.url)), '..');
function walk(directory) {
  return readdirSync(directory, {withFileTypes:true}).flatMap((entry) => {
    const path = resolve(directory, entry.name);
    return entry.isDirectory() ? walk(path) : [relative(PACKAGE, path).replaceAll('\\', '/')];
  });
}
const expected = [
  'EXPECTED_FILE_LIST.txt','Mrliou_MRL_Dual_Target_Change_Expected_File_List.txt','README.md','docs/Mrliou_MRL_Dual_Target_Deployment_v1.md',
  'scripts/Mrliou_MRL_build_pages_v1.mjs','scripts/Mrliou_MRL_verify_pages_source_v1.mjs',
  'scripts/Mrliou_MRL_verify_pages_v1.mjs','src/404.html','src/_headers','src/_redirects',
  'src/app.js','src/index.html','src/styles.css','tests/pages_static.test.mjs',
].sort();
const declaredExpected = readFileSync(resolve(PACKAGE, 'EXPECTED_FILE_LIST.txt'), 'utf8').trim().split(/\r?\n/).filter(Boolean).sort();
const actual = walk(PACKAGE).sort();
const missing = expected.filter((name) => !actual.includes(name));
const extra = actual.filter((name) => !expected.includes(name));
const empty = actual.filter((name) => lstatSync(resolve(PACKAGE, name)).size === 0);
const linked = actual.filter((name) => lstatSync(resolve(PACKAGE, name)).isSymbolicLink());
const declaredMismatch = JSON.stringify(declaredExpected) === JSON.stringify(expected) ? [] : ['EXPECTED_FILE_LIST.txt does not match canonical source inventory'];
const failures = [...missing, ...extra, ...empty, ...linked, ...declaredMismatch];
console.log(JSON.stringify({scope:'MRL_PAGES_SOURCE_INTEGRITY',expected_count:expected.length,actual_count:actual.length,missing,extra,empty,linked,declared_mismatch:declaredMismatch,coverage_percent:expected.length?(expected.length-missing.length)*100/expected.length:0,integrity_gate:failures.length?'FAIL':'PASS'}, null, 2));
process.exitCode = failures.length ? 1 : 0;
