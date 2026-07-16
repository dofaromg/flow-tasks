/**
 * Kubernetes Adapter Interface (Placeholder)
 * 
 * This adapter is designed for future integration with Kubernetes for workload deployment.
 * Currently a placeholder interface for planned future implementation.
 * 
 * TODO: Implement K8sAdapter when Kubernetes deployment integration is needed
 */

export interface K8sSignal {
  namespace: string;
  workload: string;
  labels?: Record<string, string>;
}

export interface K8sAdapter {
  deploy(signal: K8sSignal): Promise<void>;
}
