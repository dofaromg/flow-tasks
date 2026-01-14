"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.MemorySystem = void 0;
const utils_1 = require("../../utils");
class MemorySystem {
    constructor(storage) {
        this.storage = storage;
    }
    remember(scope, topic, payload) {
        const entry = {
            id: (0, utils_1.randomId)(),
            scope,
            topic,
            payload,
            createdAt: (0, utils_1.now)(),
        };
        return this.storage.upsertMemory(entry);
    }
    recall(scope) {
        return this.storage.listMemories(scope);
    }
}
exports.MemorySystem = MemorySystem;
