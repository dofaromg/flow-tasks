/**
 * Envoy Adapter Interface (Placeholder)
 * 
 * This adapter is designed for future integration with Envoy proxy for service mesh capabilities.
 * Currently a placeholder interface for planned future implementation.
 * 
 * TODO: Implement EnvoyAdapter when service mesh integration is needed
 */

export interface EnvoySignal {
  cluster: string;
  metadata?: Record<string, string>;
}

export interface EnvoyAdapter {
  emit(signal: EnvoySignal): Promise<void>;
}
