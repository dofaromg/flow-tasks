export interface JetStreamSignal {
  subject: string;
  payload: Record<string, unknown>;
}

export interface JetStreamAdapter {
  publish(signal: JetStreamSignal): Promise<void>;
}
