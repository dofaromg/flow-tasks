"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ConfigManager = void 0;
class ConfigManager {
    constructor(initial = {}) {
        this.listeners = new Set();
        this.snapshot = { ...initial };
    }
    get(key, fallback) {
        const value = this.snapshot[key];
        if (value === undefined)
            return fallback;
        return value;
    }
    all() {
        return { ...this.snapshot };
    }
    update(partial) {
        const previous = this.snapshot;
        this.snapshot = { ...previous, ...partial };
        this.notify(previous);
    }
    subscribe(listener) {
        this.listeners.add(listener);
        return () => this.listeners.delete(listener);
    }
    async reload(loader) {
        const next = await loader();
        this.update(next);
        return this.all();
    }
    notify(previous) {
        for (const listener of this.listeners) {
            listener(this.snapshot, previous);
        }
    }
}
exports.ConfigManager = ConfigManager;
