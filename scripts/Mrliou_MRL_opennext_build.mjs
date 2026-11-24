// origin_signature: MrLiouWord
// OpenNext packaging for the existing flow-tasks / mrlflow-tasks Workers.
//
// Workers Builds runs `npm run build`, then `npx wrangler deploy`. Wrangler hands an OpenNext
// project to `opennextjs-cloudflare deploy`, which skips the wrangler.jsonc custom build and
// needs `.open-next/` to exist already. `--postbuild` produces it there, and only there
// (WORKERS_CI=1), so local, CI and Docker `npm run build` stay `next build` only.
//
// Two entries, one shape:
//   --postbuild       `next build` has just finished (npm postbuild hook), so OpenNext packages
//                     that output with --skipNextBuild: one Next.js build, no nested npm run.
//   build:cloudflare  manual / wrangler.jsonc build.command entry: OpenNext runs the full build,
//                     which calls `npm run build` again; MRL_OPENNEXT_BUILD stops that nested
//                     postbuild from recursing.
import { spawnSync } from 'node:child_process';

const GUARD = 'MRL_OPENNEXT_BUILD';
const postbuild = process.argv.includes('--postbuild');

if (postbuild && (process.env.WORKERS_CI !== '1' || process.env[GUARD] === '1')) process.exit(0);

const args = ['opennextjs-cloudflare', 'build', ...(postbuild ? ['--skipNextBuild'] : [])];

console.log(`MRL OpenNext build start (${postbuild ? 'Workers Builds postbuild, reusing next build output' : 'build:cloudflare'})`);
const result = spawnSync('npx', args, {
  stdio: 'inherit',
  shell: process.platform === 'win32',
  env: { ...process.env, [GUARD]: '1' },
});

if (result.error) {
  console.error(`MRL OpenNext build could not start opennextjs-cloudflare: ${result.error.message}`);
  process.exit(1);
}
if (result.status !== 0) {
  console.error(`MRL OpenNext build failed: opennextjs-cloudflare build exited ${result.status ?? `by signal ${result.signal}`}`);
  process.exit(result.status || 1);
}
console.log('MRL OpenNext build done: .open-next is ready for deploy');
