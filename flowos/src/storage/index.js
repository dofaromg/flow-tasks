"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.MemoryStorage = void 0;
const utils_1 = require("../utils");
class MemoryStorage {
    constructor() {
        this.particles = new Map();
        this.personas = new Map();
        this.seeds = new Map();
        this.conversations = new Map();
        this.projects = new Map();
        this.artifacts = new Map();
        this.memories = new Map();
    }
    upsertParticle(snapshot) {
        const persisted = { ...snapshot, latest: { ...snapshot.latest, updatedAt: (0, utils_1.now)() } };
        this.particles.set(snapshot.id, persisted);
        return persisted;
    }
    getParticle(id) {
        return this.particles.get(id);
    }
    listParticles() {
        return [...this.particles.values()];
    }
    upsertPersona(record) {
        this.personas.set(record.profile.id, record);
        return record;
    }
    listPersonas() {
        return [...this.personas.values()];
    }
    upsertSeed(seed) {
        this.seeds.set(seed.id, seed);
        return seed;
    }
    listSeeds() {
        return [...this.seeds.values()];
    }
    upsertConversation(thread) {
        this.conversations.set(thread.id, thread);
        return thread;
    }
    getConversation(id) {
        return this.conversations.get(id);
    }
    listConversations() {
        return [...this.conversations.values()];
    }
    upsertProject(project) {
        this.projects.set(project.id, project);
        return project;
    }
    listProjects() {
        return [...this.projects.values()];
    }
    upsertArtifact(record) {
        this.artifacts.set(record.id, record);
        return record;
    }
    listArtifacts() {
        return [...this.artifacts.values()];
    }
    upsertMemory(memory) {
        const item = memory.id ? memory : { ...memory, id: (0, utils_1.randomId)(), createdAt: (0, utils_1.now)() };
        this.memories.set(item.id, item);
        return item;
    }
    listMemories(scope) {
        const entries = [...this.memories.values()];
        if (!scope)
            return entries;
        return entries.filter((entry) => entry.scope === scope);
    }
    snapshot() {
        return {
            particles: this.listParticles(),
            personas: this.listPersonas(),
            seeds: this.listSeeds(),
            conversations: this.listConversations(),
            projects: this.listProjects(),
            artifacts: this.listArtifacts(),
            memories: this.listMemories(),
        };
    }
}
exports.MemoryStorage = MemoryStorage;
