"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.GateEngine = exports.FlowGate = void 0;
class FlowGate {
    constructor() {
        this.checks = [];
    }
    register(check) {
        this.checks.push(check);
    }
    evaluate(payload, context) {
        for (const check of this.checks) {
            const decision = check(payload, context);
            if (decision) {
                return decision;
            }
        }
        return { allowed: true };
    }
}
exports.FlowGate = FlowGate;
class GateEngine extends FlowGate {
}
exports.GateEngine = GateEngine;
