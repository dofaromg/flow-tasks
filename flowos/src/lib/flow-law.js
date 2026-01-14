"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.FlowLaw = void 0;
class FlowLaw {
    evaluate(particles, context) {
        const violations = [];
        const uncollapsed = particles.filter((particle) => particle.latest.status === 'draft');
        if (uncollapsed.length > 10) {
            violations.push({
                code: 'PARTICLE_OVERFLOW',
                message: 'Too many draft particles without collapse',
                context,
            });
        }
        const orphaned = particles.filter((particle) => !particle.latest.context.persona);
        if (orphaned.length) {
            violations.push({
                code: 'ORPHANED_PARTICLE',
                message: 'Particles should reference a persona to maintain narrative consistency',
                context,
            });
        }
        return { passed: violations.length === 0, violations };
    }
}
exports.FlowLaw = FlowLaw;
