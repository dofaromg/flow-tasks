// MrLiouWord Particle Edge v4.0.0 (Unified ASI Node)
// Integrate: Traffic Gate + Neural Link + Particle Core

import { ParticleNeuralLink } from './core/neural_link';
import { GateEngine } from './core/gate';
import { handleVCSCommit } from './vcs-gate-unified';

// Export FlowOS class for backward compatibility
export { FlowOS } from './flowos';

// Export defensive client
export * from './core/defensive_client';

// Export VCS gate handler
export { handleVCSCommit } from './vcs-gate-unified';

// ============================================
// 1. Environment Definition (per wrangler 2.json)
// ============================================
export interface Env {
  MRLIOUWORD_VAULT: KVNamespace;
  PARTICLE_AUTH_VAULT: KVNamespace;
  GATE_CONFIG: KVNamespace;
  DB: D1Database;
  PARTICLES: R2Bucket;
  GATE_ENGINE: DurableObjectNamespace;

  // Secrets & Vars
  MASTER_KEY: string;
  GITHUB_TOKEN?: string;
  ENABLE_GITHUB_SYNC?: boolean;
  GITHUB_REPO?: string; // Format: "owner/repo" (e.g., "mrliou/particles")
  VERSION: string;
  ORIGIN: string;
}

// ============================================
// 2. Core Brain (Main Entry)
// ============================================
export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    // A. Build neural link (Synapse)
    const synapse = new ParticleNeuralLink(env, 'Edge-Node-L2');
    const gateEngine = new GateEngine();
    const url = new URL(request.url);
    const path = url.pathname;

    try {
      // B. System heartbeat
      if (path === '/heartbeat' || request.headers.get('X-Check-Pulse')) {
        return Response.json({
          status: 'ALIVE',
          version: env.VERSION || '4.0.0',
          origin: env.ORIGIN || 'MrLiouWord',
          philosophy: '怎麼過去，就怎麼回來',
          github_lock: '2022-11-28',
        });
      }

      // C. Traffic Gate
      if (path.startsWith('/gate/')) {
        const gateStub = env.GATE_ENGINE.idFromName('global-gate').getStub();
        const payload = await safeJson(request);
        return await synapse.fireInternal(gateStub, path, payload);
      }

      // D. Core business logic
      // Note: These instances are created for future integration
      // Current routes use them selectively based on path
      const memory = new Memory(env.MRLIOUWORD_VAULT);
      const persona = new Persona(env.MRLIOUWORD_VAULT);
      const auth = new Auth(env.PARTICLE_AUTH_VAULT || env.MRLIOUWORD_VAULT);
      const vcs = new VersionControl(env.MRLIOUWORD_VAULT, synapse);

      // TODO: Integrate auth, gateEngine, and memory into request flow
      void auth; // Auth will be used for token validation in future
      void gateEngine; // Gate engine will be used for traffic control
      void memory; // Memory system for context retention

      const key = request.headers.get('X-Master-Key') || url.searchParams.get('key');
      const publicPaths = ['/', '/status', '/heartbeat', '/world/heartbeat', '/frequencies'];
      
      // Security Note: This is a basic auth check
      // TODO: Consider implementing rate limiting, JWT tokens, or OAuth for production
      if (
        env.MASTER_KEY &&
        key !== env.MASTER_KEY &&
        !publicPaths.includes(path) &&
        !path.startsWith('/auth/init')
      ) {
        return new Response(JSON.stringify({ error: 'Unauthorized', origin: env.ORIGIN }), { status: 401 });
      }

      // VCS - Sync GitHub
      if (path === '/vcs/sync_github') {
        const githubData = await synapse.fireExternal('/user/repos', 'GET');
        if (githubData === null) {
          return Response.json({ 
            success: false, 
            error: 'Failed to sync with GitHub',
            message: 'GitHub API returned an error or is unavailable'
          }, { status: 503 });
        }
        return Response.json({ success: true, github_data: githubData });
      }

      // VCS - Defensive Commit Handler with GitHub sync
      // Note: This route is protected by the authentication check above (line 85-92)
      if (path === '/vcs/commit_defensive' && request.method === 'POST') {
        return handleVCSCommit(request, env);
      }

      if (path.startsWith('/vcs/')) {
        return handleVCS(path, request, vcs);
      }

      if (path.startsWith('/r2/')) {
        return handleR2(path, request, env);
      }

      if (path.startsWith('/persona/')) {
        return handlePersona(path, request, persona);
      }

      return Response.json({
        name: 'MrLiouWord Particle Edge',
        version: env.VERSION,
        mode: 'ASI Neural Link Active',
      });
    } catch (error: unknown) {
      console.error('Critical Failure:', error);
      return new Response(
        JSON.stringify({
          error: 'ASI_SYNAPSE_FAILURE',
          message: 'Neural link severed to preserve integrity.',
          trace: String(error),
        }),
        { status: 503 },
      );
    }
    // Note: ctx.waitUntil could be used for background cleanup tasks if needed
  },
};

// ============================================
// 3. Business Adapters
// ============================================
async function handleVCS(path: string, request: Request, vcs: VersionControl) {
  const body = async () => safeJson(request);

  if (path === '/vcs/init' && request.method === 'POST') return json(await vcs.init());
  if (path === '/vcs/add' && request.method === 'POST') {
    const b = (await body()) as { path?: string; content?: string };
    return json(await vcs.add(b.path ?? '', b.content ?? ''));
  }
  if (path === '/vcs/commit' && request.method === 'POST') {
    const b = (await body()) as { message?: string; persona_id?: string };
    return json(await vcs.commit(b.message ?? '', b.persona_id ?? ''));
  }
  return json(await vcs.status());
}

async function handleR2(path: string, request: Request, env: Env) {
  void request;
  if (path === '/r2/list') {
    const list = await env.PARTICLES.list({ limit: 100 });
    return json({ count: list.objects.length, objects: list.objects });
  }
  return json({ error: 'R2 Path Not Found' }, 404);
}

async function handlePersona(path: string, request: Request, persona: Persona) {
  const body = async () => safeJson(request);
  if (path === '/persona/wake' && request.method === 'POST') {
    const b = (await body()) as { message?: string };
    return json(await persona.wake(b.message ?? ''));
  }
  return json({ personas: await persona.list() });
}

const json = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });

async function safeJson(request: Request): Promise<Record<string, unknown>> {
  try {
    return (await request.json()) as Record<string, unknown>;
  } catch {
    return {};
  }
}

// ============================================
// 4. VersionControl (with Neural Link integration)
// ============================================
class VersionControl {
  constructor(
    private kv: KVNamespace,
    private synapse: ParticleNeuralLink,
  ) {}

  async syncToGitHub(repo: string, commitData: Record<string, unknown>) {
    return await this.synapse.fireExternal(`/repos/${repo}/git/commits`, 'POST', commitData);
  }

  // Note: The following methods are stub implementations
  // They provide the interface for VCS operations but don't yet interact with actual storage
  // TODO: Implement actual VCS logic when KV storage patterns are finalized

  async init() {
    return { success: true, msg: 'VCS Initialized (Stub)' };
  }

  async add(path: string, content: string) {
    // TODO: Store file in KV with path as key
    if (process?.env?.NODE_ENV === 'development') {
      console.log(`VCS add: ${path} (stub)`);
    }
    void path;
    void content;
    return { success: true };
  }

  async commit(msg: string, pid: string) {
    // TODO: Create commit record in KV and optionally sync to GitHub
    if (process?.env?.NODE_ENV === 'development') {
      console.log(`VCS commit: ${msg} by ${pid} (stub)`);
    }
    void msg;
    void pid;
    return { success: true, hash: 'new_hash' };
  }

  async status() {
    // TODO: Retrieve current VCS state from KV
    return { head: 'latest' };
  }
}

// ============================================
// 5. Support Classes (Memory, Persona, Auth)
// Note: These are minimal stub implementations
// Full implementation available via FlowOS class exported above
// ============================================
class Memory {
  constructor(private kv: KVNamespace) {
    // TODO: Implement KV-based memory storage
    void this.kv;
  }
}

class Persona {
  constructor(private kv: KVNamespace) {
    // TODO: Implement KV-based persona storage
    void this.kv;
  }

  async wake(message: string) {
    return { awakened: true, message };
  }

  async list() {
    return [];
  }
}

class Auth {
  constructor(private kv: KVNamespace) {
    // TODO: Implement KV-based auth token storage
    void this.kv;
  }
}

// Note: Worker runtime types are provided by @cloudflare/workers-types
// The following types are minimal stubs for local development if the package is not installed
// Consider installing @cloudflare/workers-types to avoid conflicts

// Minimal type stubs (use @cloudflare/workers-types in production)
interface KVNamespace {
  get(key: string): Promise<string | null>;
  put(key: string, value: string): Promise<void>;
}

interface D1Database {
  prepare(query: string): unknown;
}

interface R2Bucket {
  list(options?: { limit?: number }): Promise<{ objects: Array<{ key: string }> }>;
}

interface DurableObjectNamespace {
  idFromName(name: string): DurableObjectId;
}

interface DurableObjectId {
  getStub(): DurableObjectStub;
}

interface DurableObjectStub {
  fetch(input: RequestInfo, init?: RequestInit): Promise<Response>;
}

interface ExecutionContext {
  waitUntil(promise: Promise<unknown>): void;
}

interface RequestInit {
  method?: string;
  headers?: Record<string, string>;
  body?: string;
}

interface RequestInfo {}

interface ResponseInit {
  status?: number;
  headers?: Record<string, string>;
}

type BodyInit = string;

interface Headers {
  get(name: string): string | null;
}

interface Request {
  headers: Headers;
  method: string;
  url: string;
  json(): Promise<unknown>;
}

interface Response {
  ok: boolean;
  status: number;
  json(): Promise<unknown>;
}

declare const Response: {
  new (body?: BodyInit | null, init?: ResponseInit): Response;
  json(data: unknown, init?: ResponseInit): Response;
};
