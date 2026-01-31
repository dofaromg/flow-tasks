export interface EnvoySignal {
  cluster: string;
  metadata?: Record<string, string>;
}

export interface EnvoyAdapter {
  emit(signal: EnvoySignal): Promise<void>;
}
