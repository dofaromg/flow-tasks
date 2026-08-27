import { readFileSync, existsSync } from 'node:fs';
import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
let P=0,F=0; const c=(n,cond,d)=>{if(cond){P++;console.log('  ✅',n);}else{F++;console.log('  ❌',n,d??'');}};
console.log('== nextjs-frontend structure ==');
const pkg = JSON.parse(readFileSync(join(ROOT,'package.json'),'utf8'));
c('package.json valid JSON', !!pkg);
c('has build script', pkg.scripts?.build === 'next build');
c('depends on next+react', !!pkg.dependencies?.next && !!pkg.dependencies?.react && !!pkg.dependencies?.['react-dom']);
const cfg = readFileSync(join(ROOT,'next.config.mjs'),'utf8');
c("next.config output: 'standalone' (matches Dockerfile)", /output:\s*'standalone'/.test(cfg));
for (const f of ['app/layout.js','app/page.js','app/api/health/route.js','app/globals.css']) c(`${f} exists`, existsSync(join(ROOT,f)));
// node --check on non-JSX files
for (const f of ['next.config.mjs','app/api/health/route.js']) {
  try { execSync(`node --check "${join(ROOT,f)}"`, {stdio:'pipe'}); c(`${f} node --check syntax ok`, true); }
  catch(e){ c(`${f} node --check`, false, String(e.stderr||e)); }
}
// JSX files: assert default export + react-shaped
for (const f of ['app/layout.js','app/page.js']) {
  const s = readFileSync(join(ROOT,f),'utf8');
  c(`${f} has default export`, /export default function/.test(s));
}
const route = readFileSync(join(ROOT,'app/api/health/route.js'),'utf8');
c('health route exports GET', /export function GET/.test(route));
console.log(`\n===== nextjs-frontend: ${P} passed, ${F} failed (note: 'next build' needs online npm, not run here) =====`);
process.exit(F?1:0);
