"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.randomId = exports.now = void 0;
exports.chunkText = chunkText;
exports.shallowMerge = shallowMerge;
exports.ensure = ensure;
exports.hashPayload = hashPayload;
const crypto_1 = __importDefault(require("crypto"));
const now = () => Date.now();
exports.now = now;
const randomId = () => crypto_1.default.randomUUID();
exports.randomId = randomId;
function chunkText(text, size) {
    if (size <= 0)
        return [text];
    const normalized = text.trim();
    const result = [];
    for (let i = 0; i < normalized.length; i += size) {
        result.push(normalized.slice(i, i + size));
    }
    return result;
}
function shallowMerge(base, incoming) {
    return { ...base, ...incoming };
}
function ensure(value, message) {
    if (value === undefined || value === null) {
        throw new Error(message);
    }
    return value;
}
function hashPayload(payload) {
    const buffer = Buffer.from(JSON.stringify(payload));
    return crypto_1.default.createHash('sha256').update(buffer).digest('hex');
}
