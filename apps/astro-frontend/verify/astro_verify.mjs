import { readFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
const PAGES = join(dirname(fileURLToPath(import.meta.url)), '..', 'src', 'pages');
const index = readFileSync(join(PAGES, 'index.astro'), 'utf8');
const hrefs = [...index.matchAll(/href="([^"]+)"/g)].map((m) => m[1]);
let P=0,F=0; const c=(n,cond,d)=>{if(cond){P++;console.log('  ✅',n);}else{F++;console.log('  ❌',n,d??'');}};
console.log('== astro-frontend link resolution ==');
for (const h of hrefs) {
  if (h.startsWith('mailto:')) { c(`mailto ok: ${h}`, true); continue; }
  const route = h === '/' ? 'index' : h.replace(/^\//, '');
  const file = join(PAGES, `${route}.astro`);
  c(`link ${h} -> ${route}.astro exists`, existsSync(file), file);
}
// every page imports the Layout and has a title
for (const route of ['index','particle_core','private-development','local-dev']) {
  const src = readFileSync(join(PAGES, `${route}.astro`), 'utf8');
  c(`${route} uses Layout`, src.includes("import Layout"));
  c(`${route} has title`, /<Layout title=/.test(src));
}
console.log(`\n===== astro-frontend: ${P} passed, ${F} failed =====`);
process.exit(F?1:0);
