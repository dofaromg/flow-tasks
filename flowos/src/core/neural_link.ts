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

  /**
   * Fire external API call with defensive error handling
   * 
   * @returns The response data on success, or an error object with details on failure
   * @throws Error for non-400 failures that should be handled by caller
   */
  async fireExternal(
    path: string,
    method: string,
    payload?: Record<string, unknown>,
  ): Promise<unknown | { error: string; status: number; details?: string }> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'X-GitHub-Api-Version': '2022-11-28',
      Accept: 'application/vnd.github+json',
      'X-Node-Id': this.nodeId,
    };
    
    // Validate token presence for authenticated operations
    if (this.env.GITHUB_TOKEN) {
      headers.Authorization = `Bearer ${this.env.GITHUB_TOKEN}`;
    } else if (method !== 'GET') {
      // Warn if attempting non-GET operations without token (likely require auth)
      console.warn('⚠️ Attempting authenticated GitHub operation without token', { path, method });
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
        return {
          error: 'Bad Request',
          status: 400,
          details: 'GitHub API version may be unsupported or request is invalid'
        };
      }
      
      if (!response.ok) {
        // Try to get error details from response
        let errorDetail = 'Unknown error';
        try {
          const errorBody = await response.json() as { message?: string };
          errorDetail = errorBody.message || JSON.stringify(errorBody);
        } catch {
          errorDetail = `Status ${response.status}`;
        }
        
        // Return error object instead of throwing for better error handling
        return {
          error: `GitHub API Error: ${response.status}`,
          status: response.status,
          details: errorDetail
        };
      }
      
      return await response.json();
    } catch (error) {
      console.error('External call error:', { path, method, error });
      // Return error object for network failures
      return {
        error: 'Network Error',
        status: 0,
        details: error instanceof Error ? error.message : String(error)
      };
    }
  ): Promise<unknown> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'X-GitHub-Api-Version': '2024-12-01',
      'X-Node-Id': this.nodeId,
    };
    if (this.env.GITHUB_TOKEN) {
      const rawToken = this.env.GITHUB_TOKEN.trim();
      const hasBearerPrefix = /^Bearer\s+/i.test(rawToken);
      headers.Authorization = hasBearerPrefix ? rawToken : `Bearer ${rawToken}`;
    }
    const response = await fetch(`https://api.github.com${path}`, {
      method,
      headers,
      body: payload ? JSON.stringify(payload) : undefined,
    });
    if (!response.ok) {
      let bodyDescription = '';
      try {
        const errorBody = await response.json();
        if (errorBody !== undefined && errorBody !== null) {
          bodyDescription = ` Response body: ${JSON.stringify(errorBody)}`;
        }
      } catch {
        // Ignore JSON parsing errors; keep the original status-focused message.
      }
      throw new Error(
        `External call failed for ${method} ${path} with status ${response.status}.${bodyDescription}`,
      );
      throw new Error(`External call failed: ${response.status}`);
    }
    return await response.json();
  }
}
