// MRL FireCore — minimal ambient Cloudflare Workers types.
// origin_signature: MrLiouWord
//
// The FireCore modules keep `dependencies: {}` (zero external packages). Rather
// than pull @cloudflare/workers-types over the network, we declare only the
// surface actually used by the edge layer. This keeps `tsc --noEmit` green with
// no install step and documents the exact runtime contract the edge relies on.

export {};

declare global {
  interface D1Result<T = Record<string, unknown>> {
    results: T[];
    success: boolean;
    meta: { changes?: number; last_row_id?: number; duration?: number };
  }

  interface D1PreparedStatement {
    bind(...values: unknown[]): D1PreparedStatement;
    first<T = Record<string, unknown>>(colName?: string): Promise<T | null>;
    run<T = Record<string, unknown>>(): Promise<D1Result<T>>;
    all<T = Record<string, unknown>>(): Promise<D1Result<T>>;
  }

  interface D1Database {
    prepare(query: string): D1PreparedStatement;
    batch<T = Record<string, unknown>>(statements: D1PreparedStatement[]): Promise<D1Result<T>[]>;
    exec(query: string): Promise<{ count: number; duration: number }>;
  }

  interface KVNamespace {
    get(key: string, type?: 'text'): Promise<string | null>;
    put(key: string, value: string, options?: { expirationTtl?: number }): Promise<void>;
    delete(key: string): Promise<void>;
  }

  interface R2Object {
    key: string;
    size: number;
    etag: string;
    uploaded: Date;
  }

  interface R2Bucket {
    head(key: string): Promise<R2Object | null>;
    get(key: string): Promise<(R2Object & { body: ReadableStream }) | null>;
    put(key: string, value: ArrayBuffer | ReadableStream | string): Promise<R2Object>;
    delete(key: string): Promise<void>;
    list(options?: { prefix?: string; limit?: number; cursor?: string }): Promise<{
      objects: R2Object[];
      truncated: boolean;
      cursor?: string;
    }>;
  }

  interface ExecutionContext {
    waitUntil(promise: Promise<unknown>): void;
    passThroughOnException(): void;
  }
}
