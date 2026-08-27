// vector-attention-engine — minimal ambient types for offline typecheck.
// origin_signature: MrLiouWord
export {};
declare global {
  interface KVNamespace {
    get(key: string): Promise<string | null>;
    put(key: string, value: string): Promise<void>;
    delete(key: string): Promise<void>;
  }
  interface R2Bucket {
    get(key: string): Promise<unknown>;
    put(key: string, value: unknown): Promise<unknown>;
  }
}
