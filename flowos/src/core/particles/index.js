"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ParticleEngine = void 0;
class ParticleEngine {
    constructor(store) {
        this.store = store;
    }
    createParticle(content, context, summary) {
        return this.store.create(content, context, summary);
    }
    collapseParticle(id, by, note) {
        return this.store.collapse(id, by, note);
    }
    archiveParticle(id, by, note) {
        return this.store.archive(id, by, note);
    }
    getParticle(id) {
        return this.store.get(id);
    }
    listParticles() {
        return this.store.list();
    }
}
exports.ParticleEngine = ParticleEngine;
