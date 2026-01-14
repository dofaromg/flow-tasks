"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ToolRegistry = void 0;
const utils_1 = require("../../utils");
class ToolRegistry {
    constructor() {
        this.tools = new Map();
    }
    registerTool(tool) {
        const record = { ...tool, id: tool.id ?? (0, utils_1.randomId)() };
        this.tools.set(record.id, record);
        return record;
    }
    invokeTool(id, payload) {
        const tool = this.tools.get(id);
        if (!tool) {
            return Promise.reject(new Error(`Tool ${id} not found`));
        }
        return Promise.resolve(tool.handler(payload));
    }
    listTools() {
        return [...this.tools.values()];
    }
}
exports.ToolRegistry = ToolRegistry;
