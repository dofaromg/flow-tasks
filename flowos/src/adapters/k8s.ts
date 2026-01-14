export interface K8sSignal {
  namespace: string;
  workload: string;
  labels?: Record<string, string>;
}

export interface K8sAdapter {
  deploy(signal: K8sSignal): Promise<void>;
}
