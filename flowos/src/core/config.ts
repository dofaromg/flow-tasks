export type ConfigSnapshot = Record<string, unknown>;

export type ConfigListener = (next: ConfigSnapshot, previous: ConfigSnapshot) => void;

export class ConfigManager {
  private snapshot: ConfigSnapshot;
  private readonly listeners = new Set<ConfigListener>();

  constructor(initial: ConfigSnapshot = {}) {
    this.snapshot = { ...initial };
  }

  get<T = unknown>(key: string, fallback?: T): T | undefined {
    const value = this.snapshot[key];
    if (value === undefined) return fallback;
    return value as T;
  }

  all(): ConfigSnapshot {
    return { ...this.snapshot };
  }

  update(partial: ConfigSnapshot): void {
    const previous = { ...this.snapshot };
    this.snapshot = { ...this.snapshot, ...partial };
    this.notify(previous);
  }

  subscribe(listener: ConfigListener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  async reload(loader: () => ConfigSnapshot | Promise<ConfigSnapshot>): Promise<ConfigSnapshot> {
    const next = await loader();
    this.update(next);
    return this.all();
  }

  private notify(previous: ConfigSnapshot): void {
    for (const listener of this.listeners) {
      listener(this.snapshot, previous);
    }
  }
}
