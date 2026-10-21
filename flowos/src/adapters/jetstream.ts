/**
 * JetStream Adapter Interface (Placeholder)
 * 
 * This adapter is designed for future integration with NATS JetStream for event streaming.
 * Currently a placeholder interface for planned future implementation.
 * 
 * TODO: Implement JetStreamAdapter when event streaming integration is needed
 */

export interface JetStreamSignal {
  subject: string;
  payload: Record<string, unknown>;
}

export interface JetStreamAdapter {
  publish(signal: JetStreamSignal): Promise<void>;
}
