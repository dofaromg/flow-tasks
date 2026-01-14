"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArtifactVault = void 0;
const utils_1 = require("../../utils");
class ArtifactVault {
    constructor(storage) {
        this.storage = storage;
    }
    registerArtifact(project, name, description) {
        const record = {
            id: (0, utils_1.randomId)(),
            project,
            name,
            description,
            versions: [],
        };
        return this.storage.upsertArtifact(record);
    }
    addVersion(artifactId, version, metadata) {
        const existing = this.storage.listArtifacts().find((artifact) => artifact.id === artifactId);
        if (!existing) {
            throw new Error(`Artifact ${artifactId} not found`);
        }
        const versionEntry = {
            id: (0, utils_1.randomId)(),
            artifact: artifactId,
            version,
            createdAt: (0, utils_1.now)(),
            metadata,
        };
        const updated = { ...existing, versions: [...existing.versions, versionEntry] };
        return this.storage.upsertArtifact(updated);
    }
    listArtifacts() {
        return this.storage.listArtifacts();
    }
}
exports.ArtifactVault = ArtifactVault;
