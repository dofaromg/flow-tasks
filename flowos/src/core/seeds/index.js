"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SeedRegistry = void 0;
const utils_1 = require("../../utils");
class SeedRegistry {
    constructor() {
        this.seeds = new Map();
    }
    registerSeed(seed) {
        const definition = {
            ...seed,
            id: seed.id ?? (0, utils_1.randomId)(),
            migrations: seed.migrations ?? [],
        };
        this.seeds.set(definition.id, definition);
        return definition;
    }
    addMigration(seedId, migration) {
        const seed = this.seeds.get(seedId);
        if (!seed) {
            throw new Error(`Seed ${seedId} not found`);
        }
        const record = { ...migration, id: (0, utils_1.randomId)(), createdAt: (0, utils_1.now)() };
        seed.migrations.push(record);
        return seed;
    }
    listSeeds() {
        return [...this.seeds.values()];
    }
}
exports.SeedRegistry = SeedRegistry;
