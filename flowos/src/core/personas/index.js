"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.PersonaRegistry = void 0;
const utils_1 = require("../../utils");
class PersonaRegistry {
    constructor() {
        this.personas = new Map();
    }
    registerPersona(profile, triangle) {
        const persona = {
            profile: { ...profile, id: profile.id ?? (0, utils_1.randomId)() },
            triangle,
            seeds: [],
        };
        this.personas.set(persona.profile.id, persona);
        return persona;
    }
    linkSeed(personaId, seedId) {
        const persona = this.personas.get(personaId);
        if (!persona) {
            throw new Error(`Persona ${personaId} not found`);
        }
        if (!persona.seeds.includes(seedId)) {
            persona.seeds.push(seedId);
        }
        return persona;
    }
    listPersonas() {
        return [...this.personas.values()];
    }
}
exports.PersonaRegistry = PersonaRegistry;
