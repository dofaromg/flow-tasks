"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.MerkleChain = void 0;
const crypto_1 = __importDefault(require("crypto"));
const utils_1 = require("../../utils");
class MerkleChain {
    constructor() {
        this.links = [];
    }
    append(event, context) {
        const parent = this.links.length ? this.links[this.links.length - 1].hash : undefined;
        const payload = { event, context, parent };
        const hash = crypto_1.default.createHash('sha256').update(JSON.stringify(payload)).digest('hex');
        const link = { hash, parent, context, event, createdAt: Date.now() };
        this.links.push(link);
        return link;
    }
    verify() {
        for (let i = 0; i < this.links.length; i += 1) {
            const link = this.links[i];
            const expectedHash = crypto_1.default
                .createHash('sha256')
                .update(JSON.stringify({ event: link.event, context: link.context, parent: link.parent }))
                .digest('hex');
            if (expectedHash !== link.hash) {
                return false;
            }
            if (i > 0 && this.links[i - 1].hash !== link.parent) {
                return false;
            }
        }
        return true;
    }
    trace(limit = 10) {
        return this.links.slice(-limit);
    }
    digest() {
        if (!this.links.length)
            return (0, utils_1.hashPayload)({});
        return this.links[this.links.length - 1].hash;
    }
}
exports.MerkleChain = MerkleChain;
