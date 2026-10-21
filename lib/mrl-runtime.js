import { readFileSync } from 'fs';
import { join } from 'path';

const SNAPSHOT_PATH = join(process.cwd(), 'mrl_runtime_state.json');

let cached = null;
let cachedAt = 0;
const TTL = 5000;

export function getRuntimeSnapshot() {
  const now = Date.now();
  if (cached && now - cachedAt < TTL) return cached;
  try {
    const raw = readFileSync(SNAPSHOT_PATH, 'utf-8');
    cached = JSON.parse(raw);
    cachedAt = now;
    return cached;
  } catch {
    return null;
  }
}
