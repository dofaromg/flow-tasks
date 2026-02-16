// MrLiouWord Particle Edge v4.0.0 (Unified ASI Node)
// Integrate: Traffic Gate + Neural Link + Particle Core
// Architecture: L0-L7 MrLiouWord Particle System
// Philosophy: "怎麼過去，就怎麼回來" (How you go is how you come back)

import { ParticleNeuralLink } from './core/neural_link';
import { GateEngine } from './core/gate';
import { ParticleEngine } from './core/particles';
import { ParticleStore } from './core/particles/store';

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
        
        // Check if response is an error object
        if (githubData && typeof githubData === 'object' && 'error' in githubData) {
          const errorData = githubData as { error: string; status: number; details?: string };
          return Response.json({ 
            success: false, 
            error: errorData.error,
            details: errorData.details,
            message: 'Failed to sync with GitHub'
          }, { status: errorData.status || 503 });
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
import { FlowContext, FlowEvent, FlowSnapshot } from './types';
import { MemoryStorage } from './storage';
import { ParticleEngine } from './core/particles';
import { ParticleStore } from './core/particles/store';
import { MerkleChain } from './core/chains';
import { SeedRegistry } from './core/seeds';
import { PersonaRegistry } from './core/personas';
import { ConfigManager } from './core/config';
import { FlowGate, GateDecision } from './core/gate';
import { NeuralLink, NeuralLinkPacket } from './core/neural_link';
import { FlowLaw } from './lib/flow-law';
import { ConversationManager } from './app/conversations';
import { ProjectRegistry } from './app/projects';
import { ArtifactVault } from './app/artifacts';
import { MemorySystem } from './app/memory';
import { MerkleChain } from './core/chains';
import { FlowLaw } from './lib/flow-law';
import { MemoryStorage } from './storage';
import { FlowContext, FlowSnapshot, FlowLawResult } from './types';
import { randomId, now } from './utils';

// ============================================
// 1. Main FlowOS Class (for local/library usage)
// Implements L2 (PARTICLE) and L3 (LAW) layers
// Integrates all core subsystems with complete reversibility
// ============================================
export class FlowOS {
  private storage: MemoryStorage;
  public readonly particles: ParticleEngine;
  public readonly conversations: ConversationManager;
  public readonly projects: ProjectRegistry;
  public readonly artifacts: ArtifactVault;
  public readonly memory: MemorySystem;
  public readonly chain: MerkleChain;
  private flowLaw: FlowLaw;

  constructor() {
    this.storage = new MemoryStorage();
    const particleStore = new ParticleStore(this.storage);
    this.particles = new ParticleEngine(particleStore);
export interface NeuralSignalResult {
  decision: GateDecision;
  packet?: NeuralLinkPacket;
}

export class FlowOS {
  readonly storage: MemoryStorage;
  readonly particles: ParticleEngine;
  readonly particleStore: ParticleStore;
  readonly chain: MerkleChain;
  readonly seeds: SeedRegistry;
  readonly personas: PersonaRegistry;
  readonly config: ConfigManager;
  readonly gate: FlowGate;
  readonly neuralLink: NeuralLink;
  readonly flowLaw: FlowLaw;
  readonly conversations: ConversationManager;
  readonly projects: ProjectRegistry;
  readonly artifacts: ArtifactVault;
  readonly memory: MemorySystem;
  readonly tools: ToolRegistry;

  constructor() {
    this.storage = new MemoryStorage();
    this.particleStore = new ParticleStore();
    this.particles = new ParticleEngine(this.particleStore);
    this.chain = new MerkleChain();
    this.seeds = new SeedRegistry();
    this.personas = new PersonaRegistry();
    this.config = new ConfigManager();
    this.gate = new FlowGate();
    this.neuralLink = new NeuralLink();
    this.flowLaw = new FlowLaw();
    this.conversations = new ConversationManager(this.storage);
    this.projects = new ProjectRegistry(this.storage);
    this.artifacts = new ArtifactVault(this.storage);
    this.memory = new MemorySystem(this.storage);
    this.chain = new MerkleChain();
    this.flowLaw = new FlowLaw();
  }
  return json(await vcs.status());
}

  createContext(options: { persona?: string; project?: string; seed?: string; metadata?: Record<string, unknown> }): FlowContext {
    return {
      id: randomId(),
      persona: options.persona,
      project: options.project,
      seed: options.seed,
      createdAt: now(),
      metadata: options.metadata,
    };
async function handleR2(path: string, request: Request, env: Env) {
  void request;
  if (path === '/r2/list') {
    const list = await env.PARTICLES.list({ limit: 100 });
    return json({ count: list.objects.length, objects: list.objects });
  }
  return json({ error: 'R2 Path Not Found' }, 404);
}

  snapshot(): FlowSnapshot {
    return this.storage.snapshot();
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

  enforce(context?: FlowContext): FlowLawResult {
    const particles = this.particles.listParticles();
    return this.flowLaw.evaluate(particles, context);
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
/**
 * Version Control system with GitHub integration
 * 
 * Note: The add, commit, and status methods are stub implementations that provide
 * the VCS interface but don't yet interact with actual KV storage. These stubs
 * allow the application to accept VCS operations without failing, while the actual
 * implementation is being developed.
 * 
 * TODO: Implement actual VCS logic when KV storage patterns are finalized
 * - Store files in KV with path as key
 * - Create commit records with timestamps and persona info
 * - Track HEAD and branch references
 */
class VersionControl {
  constructor(
    private kv: KVNamespace,
    private synapse: ParticleNeuralLink,
  ) {}

  async syncToGitHub(repo: string, commitData: Record<string, unknown>) {
    return await this.synapse.fireExternal(`/repos/${repo}/git/commits`, 'POST', commitData);
  async emitSignal(
    type: string,
    payload: Record<string, unknown>,
    context?: FlowContext,
  ): Promise<NeuralSignalResult> {
    const decision = this.gate.evaluate(payload, context);
    if (!decision.allowed) {
      return { decision };
    }
    const packet = await this.neuralLink.transmit(type, payload, context);
    return { decision, packet };
  }
}

// ============================================
// 2. Environment Definition (per wrangler 2.json)
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
  VERSION: string;
  ORIGIN: string;
}

// ============================================
// 3. Core Brain (Main Entry for Edge Worker)
// L4 (WORLD) layer: External connections and routing
// L3 (LAW) layer: Authorization and business logic
// L2 (PARTICLE) layer: Subsystem orchestration
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
        const id = env.GATE_ENGINE.idFromName('global-gate');
        const gateStub = env.GATE_ENGINE.get(id);
        const payload = await safeJson(request);
        return await synapse.fireInternal(gateStub, path, payload);
      }

      // D. Core business logic
      // Following L2 PARTICLE layer principle: instantiate only needed functional particles
      // Future integration points for worker entrypoint (when implemented):
      // - Memory: Worker-scoped MemorySystem instance for request-level state persistence
      // - Auth: Authentication particle for user/token verification in worker context
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
        return json({ error: 'Unauthorized', origin: env.ORIGIN }, 401);
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
// 4. Business Adapters
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
// 5. Version Control System
// L3 (LAW) layer: Version control business logic
// L4 (WORLD) layer: GitHub integration via neural link
// Implements reversible state tracking ("怎麼過去，就怎麼回來")
// ============================================
class VersionControl {
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

  async add(_path: string, _content: string) {
    // TODO: Implement VCS add functionality
    return { success: true };
  }

  async commit(_msg: string, _pid: string) {
    // TODO: Implement VCS commit functionality
    return { success: true, hash: 'new_hash' };
  }

  async status() {
    return { head: 'latest' };
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
// ============================================
/**
 * Stub implementations for core FlowOS services
 * 
 * These classes provide minimal implementations to support the worker architecture.
 * For full-featured implementations, use the FlowOS class exported from flowos.ts.
 * 
 * Memory: KV-based memory storage for conversation context and state
 * TODO: Implement memory storage, retrieval, and archival patterns
 * 
 * Persona: KV-based persona storage for AI character definitions
 * TODO: Implement persona CRUD operations and wake/sleep state management
 * 
 * Auth: KV-based authentication token storage
 * TODO: Implement token generation, validation, and expiration
 */
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

// ============================================
// 6. Runtime Type Declarations
// ============================================
/**
 * Cloudflare Workers Runtime Types
 * 
 * IMPORTANT: These are minimal type stubs for local development.
 * 
 * RECOMMENDED: Install @cloudflare/workers-types for production use:
 *   npm install --save-dev @cloudflare/workers-types
 * 
 * Then add to tsconfig.json:
 *   "compilerOptions": {
 *     "types": ["@cloudflare/workers-types"]
 *   }
 * 
 * This avoids type conflicts and ensures you have the latest Cloudflare Workers APIs.
 * The stubs below are provided only as fallback for environments without the package.
 */

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

// ============================================
// 6. Persona System
// L2 (PARTICLE) layer: Identity and consciousness particle
// Implements consciousness-carrier separation principle
// ============================================
class Persona {
  constructor(private _kv: KVNamespace) {}

  async wake(message: string) {
    return { awakened: true, message };
  }

  async list() {
    return [];
  }
}

// ============================================
// 7. Worker Runtime Types (stubs for build-time)
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
  get(id: DurableObjectId): DurableObjectStub;
}

// Opaque identifier for Durable Objects in Cloudflare Workers runtime
interface DurableObjectId {}

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
export * from './types';
export * from './utils';
export * from './core/config';
export * from './core/gate';
export * from './core/neural_link';
export * from './adapters';
