"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ParticleNeuralLink = exports.NeuralLink = void 0;
const utils_1 = require("../utils");
class NeuralLink {
    constructor() {
        this.handlers = new Map();
    }
    on(type, handler) {
        const existing = this.handlers.get(type) ?? [];
        existing.push(handler);
        this.handlers.set(type, existing);
        return () => this.off(type, handler);
    }
    off(type, handler) {
        const existing = this.handlers.get(type);
        if (!existing)
            return;
        this.handlers.set(type, existing.filter((candidate) => candidate !== handler));
    }
    async transmit(type, payload, context) {
        const packet = {
            id: (0, utils_1.randomId)(),
            type,
            payload,
            context,
            createdAt: (0, utils_1.now)(),
        };
        const handlers = this.handlers.get(type) ?? [];
        for (const handler of handlers) {
            await handler(packet);
        }
        return packet;
    }
}
exports.NeuralLink = NeuralLink;
class ParticleNeuralLink {
    constructor(env, nodeId) {
        this.env = env;
        this.nodeId = nodeId;
    }
    async fireInternal(stub, path, payload) {
        return await stub.fetch(`https://internal${path}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-Node-Id': this.nodeId },
            body: JSON.stringify(payload),
        });
    }
    async fireExternal(path, method, payload) {
        const headers = {
            'Content-Type': 'application/json',
            'X-GitHub-Api-Version': '2022-11-28',
            'X-Node-Id': this.nodeId,
        };
        if (this.env.GITHUB_TOKEN) {
            headers.Authorization = `Bearer ${this.env.GITHUB_TOKEN}`;
        }
        const response = await fetch(`https://api.github.com${path}`, {
            method,
            headers,
            body: payload ? JSON.stringify(payload) : undefined,
        });
        if (!response.ok) {
            throw new Error(`External call failed: ${response.status}`);
        }
        return await response.json();
    }
}
exports.ParticleNeuralLink = ParticleNeuralLink;
