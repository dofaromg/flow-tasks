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

interface FetchResponse {
  ok: boolean;
  status: number;
  json(): Promise<unknown>;
}

declare function fetch(input: RequestInfo | string, init?: RequestInit): Promise<FetchResponse>;

/**
 * NeuralLink provides an event-driven communication system for FlowOS components.
 * Components can register handlers for specific event types and transmit packets.
 */
export class NeuralLink {
  private readonly handlers = new Map<string, NeuralLinkHandler[]>();

  /**
   * Register a handler for a specific event type
   * @param type - Event type to listen for
   * @param handler - Handler function to be called when event is transmitted
   * @returns Unsubscribe function
   */
  on(type: string, handler: NeuralLinkHandler): () => void {
    const existing = this.handlers.get(type) ?? [];
    existing.push(handler);
    this.handlers.set(type, existing);
    return () => this.off(type, handler);
  }

  /**
   * Unregister a handler for a specific event type
   * @param type - Event type
   * @param handler - Handler function to remove
   */
  off(type: string, handler: NeuralLinkHandler): void {
    const existing = this.handlers.get(type);
    if (!existing) return;
    this.handlers.set(
      type,
      existing.filter((candidate) => candidate !== handler),
    );
  }

  /**
   * Transmit a packet to all registered handlers for the given type
   * @param type - Event type
   * @param payload - Data payload for the event
   * @param context - Optional FlowContext for the event
   * @returns The transmitted packet
   */
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

/**
 * ParticleNeuralLink extends neural communication with internal and external service calls.
 * Supports Durable Object communication and GitHub API integration.
 */
export class ParticleNeuralLink {
  constructor(
    private readonly env: NeuralLinkEnv,
    private readonly nodeId: string,
  ) {}

  /**
   * Fire an internal call to a Durable Object stub
   * @param stub - Durable Object stub with fetch method
   * @param path - Request path
   * @param payload - Request payload
   * @returns Response from the Durable Object
   */
  async fireInternal(
    stub: { fetch(input: RequestInfo, init?: RequestInit): Promise<any> },
    path: string,
    payload: Record<string, unknown>,
  ): Promise<any> {
    return await stub.fetch(`https://internal${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Node-Id': this.nodeId },
      body: JSON.stringify(payload),
    });
  }

  /**
   * Fire an external call to GitHub API
   * @param path - GitHub API path (e.g., '/repos/owner/repo')
   * @param method - HTTP method
   * @param payload - Optional request payload
   * @returns Response data from GitHub API
   * @throws Error with detailed message if request fails
   */
  async fireExternal(
    path: string,
    method: string,
    payload?: Record<string, unknown>,
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
        bodyDescription = ` Response body: ${JSON.stringify(errorBody)}`;
      } catch {
        // Ignore JSON parsing errors; keep bodyDescription as empty string
      }
      throw new Error(
        `External call failed for ${method} ${path} with status ${response.status}.${bodyDescription}`,
      );
    }
    return await response.json();
  }
}
