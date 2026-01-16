export type ConfigSnapshot = Record<string, unknown>;

export type ConfigListener = (next: ConfigSnapshot, previous: ConfigSnapshot) => void;

/**
 * ConfigManager handles runtime configuration with change notifications.
 * All configuration changes are merged with existing values (not replaced).
 */
export class ConfigManager {
  private snapshot: ConfigSnapshot;
  private readonly listeners = new Set<ConfigListener>();

  constructor(initial: ConfigSnapshot = {}) {
    this.snapshot = { ...initial };
  }

  /**
   * Get a configuration value by key
   * @param key - Configuration key to retrieve
   * @param fallback - Optional fallback value if key is not found
   * @returns The configuration value or fallback
   */
  get<T = unknown>(key: string, fallback?: T): T | undefined {
    const value = this.snapshot[key];
    if (value === undefined) return fallback;
    return value as T;
  }

  /**
   * Get a copy of the entire configuration snapshot
   * @returns Immutable copy of current configuration
   */
  all(): ConfigSnapshot {
    return { ...this.snapshot };
  }

  /**
   * Update configuration with partial values (merges with existing config)
   * @param partial - Partial configuration to merge
   */
  update(partial: ConfigSnapshot): void {
    const previous = this.snapshot;
    this.snapshot = { ...previous, ...partial };
    this.notify(previous);
  }

  /**
   * Subscribe to configuration changes
   * @param listener - Callback function to be called on config changes
   * @returns Unsubscribe function
   */
  subscribe(listener: ConfigListener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  /**
   * Reload configuration from a loader function.
   * Note: The loaded config is MERGED with existing values, not replaced.
   * @param loader - Function that returns new configuration
   * @returns Promise resolving to the updated configuration
   */
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
