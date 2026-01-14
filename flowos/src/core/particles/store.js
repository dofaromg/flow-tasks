"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ParticleStore = void 0;
const utils_1 = require("../../utils");
class ParticleStore {
    constructor() {
        this.snapshots = new Map();
    }
    create(content, context, summary) {
        const state = {
            id: (0, utils_1.randomId)(),
            status: 'draft',
            content,
            summary,
            context,
            createdAt: (0, utils_1.now)(),
            updatedAt: (0, utils_1.now)(),
        };
        const snapshot = {
            id: state.id,
            history: [{ state, by: 'system', note: 'created' }],
            latest: state,
        };
        this.snapshots.set(snapshot.id, snapshot);
        return snapshot;
    }
    collapse(id, by, note) {
        const current = this.snapshots.get(id);
        if (!current) {
            throw new Error(`Particle ${id} not found`);
        }
        const nextState = {
            ...current.latest,
            status: 'collapsed',
            updatedAt: (0, utils_1.now)(),
        };
        const historyEntry = { state: nextState, by, note };
        const updated = {
            ...current,
            latest: nextState,
            history: [...current.history, historyEntry],
        };
        this.snapshots.set(id, updated);
        return updated;
    }
    archive(id, by, note) {
        const current = this.snapshots.get(id);
        if (!current) {
            throw new Error(`Particle ${id} not found`);
        }
        const nextState = {
            ...current.latest,
            status: 'archived',
            updatedAt: (0, utils_1.now)(),
        };
        const historyEntry = { state: nextState, by, note };
        const updated = {
            ...current,
            latest: nextState,
            history: [...current.history, historyEntry],
        };
        this.snapshots.set(id, updated);
        return updated;
    }
    get(id) {
        return this.snapshots.get(id);
    }
    list() {
        return [...this.snapshots.values()];
    }
}
exports.ParticleStore = ParticleStore;
