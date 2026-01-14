"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ProjectRegistry = void 0;
const utils_1 = require("../../utils");
class ProjectRegistry {
    constructor(storage) {
        this.storage = storage;
    }
    registerProject(name, description) {
        const project = {
            id: (0, utils_1.randomId)(),
            name,
            description,
            createdAt: (0, utils_1.now)(),
        };
        return this.storage.upsertProject(project);
    }
    listProjects() {
        return this.storage.listProjects();
    }
}
exports.ProjectRegistry = ProjectRegistry;
