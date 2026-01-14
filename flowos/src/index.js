"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __exportStar = (this && this.__exportStar) || function(m, exports) {
    for (var p in m) if (p !== "default" && !Object.prototype.hasOwnProperty.call(exports, p)) __createBinding(exports, m, p);
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.FlowOS = void 0;
const storage_1 = require("./storage");
const particles_1 = require("./core/particles");
const store_1 = require("./core/particles/store");
const chains_1 = require("./core/chains");
const seeds_1 = require("./core/seeds");
const personas_1 = require("./core/personas");
const config_1 = require("./core/config");
const gate_1 = require("./core/gate");
const neural_link_1 = require("./core/neural_link");
const flow_law_1 = require("./lib/flow-law");
const conversations_1 = require("./app/conversations");
const projects_1 = require("./app/projects");
const artifacts_1 = require("./app/artifacts");
const memory_1 = require("./app/memory");
const tools_1 = require("./app/tools");
const utils_1 = require("./utils");
class FlowOS {
    constructor() {
        this.storage = new storage_1.MemoryStorage();
        this.particleStore = new store_1.ParticleStore();
        this.particles = new particles_1.ParticleEngine(this.particleStore);
        this.chain = new chains_1.MerkleChain();
        this.seeds = new seeds_1.SeedRegistry();
        this.personas = new personas_1.PersonaRegistry();
        this.config = new config_1.ConfigManager();
        this.gate = new gate_1.FlowGate();
        this.neuralLink = new neural_link_1.NeuralLink();
        this.flowLaw = new flow_law_1.FlowLaw();
        this.conversations = new conversations_1.ConversationManager(this.storage);
        this.projects = new projects_1.ProjectRegistry(this.storage);
        this.artifacts = new artifacts_1.ArtifactVault(this.storage);
        this.memory = new memory_1.MemorySystem(this.storage);
        this.tools = new tools_1.ToolRegistry();
    }
    createContext(partial = {}) {
        return {
            id: partial.id ?? (0, utils_1.randomId)(),
            createdAt: partial.createdAt ?? (0, utils_1.now)(),
            ...partial,
        };
    }
    dispatch(eventType, payload, context) {
        const event = { id: (0, utils_1.randomId)(), type: eventType, payload, createdAt: (0, utils_1.now)() };
        this.chain.append(event, context);
        return event;
    }
    enforce(context) {
        return this.flowLaw.evaluate(this.particles.listParticles(), context);
    }
    async emitSignal(type, payload, context) {
        const decision = this.gate.evaluate(payload, context);
        if (!decision.allowed) {
            return { decision };
        }
        const packet = await this.neuralLink.transmit(type, payload, context);
        return { decision, packet };
    }
    snapshot() {
        const snapshot = this.storage.snapshot();
        return {
            ...snapshot,
            particles: this.particles.listParticles(),
        };
    }
}
exports.FlowOS = FlowOS;
__exportStar(require("./types"), exports);
__exportStar(require("./utils"), exports);
__exportStar(require("./core/config"), exports);
__exportStar(require("./core/gate"), exports);
__exportStar(require("./core/neural_link"), exports);
__exportStar(require("./adapters"), exports);
