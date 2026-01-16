import { FlowContext } from '../types';
import { now, randomId } from '../utils';

export type NeuralLinkPayload = Record<string, unknown>;

export interface NeuralLinkPacket {
  id: string;
  type: string;
  payload: NeuralLinkPayload;
  context?: FlowContext;
  createdAt: number;
}

export type NeuralLinkHandler = (packet: NeuralLinkPacket) => void | Promise<void>;

interface NeuralLinkEnv {
  GITHUB_TOKEN?: string;
}

interface RequestInit {
  method?: string;
  headers?: Record<string, string>;
  body?: string;
}

interface RequestInfo {}

interface Response {
  ok: boolean;
  status: number;
  statusText?: string;
  headers?: { get(name: string): string | null };
  json(): Promise<unknown>;
}

declare function fetch(input: RequestInfo | string, init?: RequestInit): Promise<Response>;

export class NeuralLink {
  private readonly handlers = new Map<string, NeuralLinkHandler[]>();

  on(type: string, handler: NeuralLinkHandler): () => void {
    const existing = this.handlers.get(type) ?? [];
    existing.push(handler);
    this.handlers.set(type, existing);
    return () => this.off(type, handler);
  }

  off(type: string, handler: NeuralLinkHandler): void {
    const existing = this.handlers.get(type);
    if (!existing) return;
    this.handlers.set(
      type,
      existing.filter((candidate) => candidate !== handler),
    );
  }

  async transmit(type: string, payload: NeuralLinkPayload, context?: FlowContext): Promise<NeuralLinkPacket> {
    const packet: NeuralLinkPacket = {
      id: randomId(),
      type,
      payload,
      context,
      createdAt: now(),
    };
    const handlers = this.handlers.get(type) ?? [];
    for (const handler of handlers) {
      await handler(packet);
    }
    return packet;
  }
}

export class ParticleNeuralLink {
  constructor(
    private readonly env: NeuralLinkEnv,
    private readonly nodeId: string,
  ) {}

  async fireInternal(
    stub: { fetch(input: RequestInfo, init?: RequestInit): Promise<Response> },
    path: string,
    payload: Record<string, unknown>,
  ): Promise<Response> {
    return await stub.fetch(`https://internal${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Node-Id': this.nodeId },
      body: JSON.stringify(payload),
    });
  }

  async fireExternal(
    path: string,
    method: string,
    payload?: Record<string, unknown>,
  ): Promise<unknown | null> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'X-GitHub-Api-Version': '2022-11-28',
      Accept: 'application/vnd.github+json',
      'X-Node-Id': this.nodeId,
    };
    
    // Validate token presence for authenticated operations
    if (this.env.GITHUB_TOKEN) {
      headers.Authorization = `Bearer ${this.env.GITHUB_TOKEN}`;
    } else if (method !== 'GET' || !path.startsWith('/')) {
      // Warn if attempting non-public operations without token
      console.warn('⚠️ Attempting authenticated GitHub operation without token');
    }
    
    try {
      const response = await fetch(`https://api.github.com${path}`, {
        method,
        headers,
        body: payload ? JSON.stringify(payload) : undefined,
      });
      
      if (response.status === 400) {
        console.warn('⚠️ GitHub API 400 error - version may be unsupported or request invalid', {
          path,
          method,
          status: response.status
        });
        return null;
      }
      
      if (!response.ok) {
        // Try to get error details, but don't fail if response body is unavailable
        let errorDetail = 'Unknown error';
        try {
          const errorBody = await response.json() as { message?: string };
          errorDetail = errorBody.message || JSON.stringify(errorBody);
        } catch {
          errorDetail = `Status ${response.status}`;
        }
        throw new Error(`External call failed: ${response.status} - ${errorDetail}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('External call error:', { path, method, error });
      throw error;
    }
  }
}
