// vector-attention-engine — core attention math (pure, dependency-free).
// origin_signature: MrLiouWord
//
// Real scaled dot-product attention and cosine similarity. Kept in a separate
// module with no Workers globals so it can be unit-tested directly in Node.

export class VectorError extends Error {}

export function dot(a: number[], b: number[]): number {
  if (a.length !== b.length) throw new VectorError(`dim_mismatch:${a.length}!=${b.length}`);
  let s = 0;
  for (let i = 0; i < a.length; i++) s += a[i] * b[i];
  return s;
}

export function norm(a: number[]): number {
  return Math.sqrt(dot(a, a));
}

export function cosineSimilarity(a: number[], b: number[]): number {
  const na = norm(a);
  const nb = norm(b);
  if (na === 0 || nb === 0) return 0;
  return dot(a, b) / (na * nb);
}

// Numerically stable softmax.
export function softmax(scores: number[]): number[] {
  if (scores.length === 0) return [];
  const max = Math.max(...scores);
  const exps = scores.map((s) => Math.exp(s - max));
  const sum = exps.reduce((acc, v) => acc + v, 0);
  return exps.map((v) => v / sum);
}

export interface AttentionResult {
  output: number[];
  weights: number[];
}

// Single-query scaled dot-product attention:
//   weights = softmax(Q·Kᵢ / sqrt(d))
//   output  = Σ weightsᵢ · Vᵢ
export function scaledDotProductAttention(query: number[], keys: number[][], values: number[][]): AttentionResult {
  if (keys.length === 0) throw new VectorError('empty_keys');
  if (keys.length !== values.length) throw new VectorError(`keys_values_mismatch:${keys.length}!=${values.length}`);
  const d = query.length;
  if (d === 0) throw new VectorError('empty_query');
  const scale = Math.sqrt(d);
  const scores = keys.map((k) => dot(query, k) / scale);
  const weights = softmax(scores);
  const dv = values[0].length;
  const output = new Array<number>(dv).fill(0);
  for (let i = 0; i < values.length; i++) {
    if (values[i].length !== dv) throw new VectorError('ragged_values');
    for (let j = 0; j < dv; j++) output[j] += weights[i] * values[i][j];
  }
  return { output, weights };
}

export interface Ranked {
  id: string;
  score: number;
}

// Cosine top-k over a labelled corpus.
export function topKSimilar(query: number[], corpus: { id: string; vector: number[] }[], k: number): Ranked[] {
  const ranked = corpus.map((c) => ({ id: c.id, score: cosineSimilarity(query, c.vector) }));
  ranked.sort((a, b) => b.score - a.score);
  return ranked.slice(0, Math.max(0, k));
}
