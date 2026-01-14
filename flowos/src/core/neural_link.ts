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
  ): Promise<unknown> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'X-GitHub-Api-Version': '2024-11-28',
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
    }
    return await response.json();
  }
}
