// MrLiouWord Particle Edge v4.0.0 (Unified ASI Node)
// Integrate: Traffic Gate + Neural Link + Particle Core

import { ParticleNeuralLink } from './core/neural_link';

// ============================================
// 1. Environment Definition (per wrangler.toml)
// ============================================
export interface Env {
  MRLIOUWORD_VAULT: KVNamespace;
  PARTICLE_AUTH_VAULT: KVNamespace;
  GATE_CONFIG: KVNamespace;
  DB: D1Database;
  PARTICLES: R2Bucket;
  GATE_ENGINE?: DurableObjectNamespace;

  // Secrets & Vars
  MASTER_KEY: string;
  GITHUB_TOKEN?: string;
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
        if (!env.GATE_ENGINE) {
          return Response.json(
            {
              error: 'GATE_ENGINE_NOT_CONFIGURED',
              message: 'Gate engine Durable Object is not bound; /gate/ endpoint is disabled.',
              path,
            },
            { status: 501 },
          );
        }
        const gateStub = env.GATE_ENGINE.idFromName('global-gate').getStub();
        const payload = await safeJson(request);
        return (await synapse.fireInternal(gateStub, path, payload)) as Response;
      }

      // D. Core business logic
      const persona = new Persona(env.MRLIOUWORD_VAULT);
      const vcs = new VersionControl(env.MRLIOUWORD_VAULT, synapse);

      const key = request.headers.get('X-Master-Key');
      const publicPaths = ['/', '/status', '/heartbeat', '/world/heartbeat', '/frequencies'];
      if (
        env.MASTER_KEY &&
        key !== env.MASTER_KEY &&
        !publicPaths.includes(path) &&
        !path.startsWith('/auth/init')
      ) {
        return Response.json({ error: 'Unauthorized', origin: env.ORIGIN }, { status: 401 });
      }

      // VCS - Sync GitHub
      if (path === '/vcs/sync_github') {
        const githubData = await synapse.fireExternal('/user/repos', 'GET');
        return Response.json({ success: true, github_data: githubData });
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
  } catch (error) {
    console.error('Failed to parse JSON request body in safeJson:', error);
    return {};
  }
}

// ============================================
// 4. Improved VersionControl (Neural Link injected)
// ============================================
export class VersionControl {
  constructor(
    private kv: KVNamespace,
    private synapse: ParticleNeuralLink,
  ) {}

  async syncToGitHub(repo: string, commitData: Record<string, unknown>) {
    return await this.synapse.fireExternal(`/repos/${repo}/git/commits`, 'POST', commitData);
  }

  async init() {
    return { success: true, msg: 'VCS Initialized (Stub)' };
  }

  async add(path: string, content: string) {
    void path;
    void content;
    return { success: true };
  }

  async commit(msg: string, pid: string) {
    void msg;
    void pid;
    return { success: true, hash: 'new_hash' };
  }

  async status() {
    return { head: 'latest' };
  }
}

// ============================================
// 5. Other Classes (Memory, Persona, Auth)
// Note: These are stub implementations awaiting full implementation.
// Methods return minimal/hardcoded values for scaffolding purposes.
// ============================================
export class Memory {
  constructor(private kv: KVNamespace) {
    void this.kv;
  }
}

export class Persona {
  constructor(private kv: KVNamespace) {
    void this.kv;
  }

  async wake(message: string) {
    return { awakened: true, message };
  }

  async list() {
    return [];
  }
}

export class Auth {
  constructor(private kv: KVNamespace) {
    void this.kv;
  }
}

// ============================================
// 6. Worker Runtime Types (stubs for build-time)
// Note: These type stubs are minimal definitions for build-time checks.
// For production use, consider installing @cloudflare/workers-types package
// to get complete, up-to-date type definitions for Cloudflare Workers runtime.
// ============================================
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
  readonly status: number;
  readonly statusText: string;
  readonly ok: boolean;
  readonly headers: Headers;
  json<T = unknown>(): Promise<T>;
  text(): Promise<string>;
}

declare const Response: {
  new (body?: BodyInit | null, init?: ResponseInit): Response;
  json(data: unknown, init?: ResponseInit): Response;
};

// ============================================
// 7. Public API Exports
// ============================================
export { ParticleNeuralLink } from './core/neural_link';
export { GateEngine, FlowGate } from './core/gate';
export { ConfigManager } from './core/config';
