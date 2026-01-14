import { FlowParticleHistory, FlowParticleSnapshot, FlowParticleState, FlowContext } from '../../types';
import { randomId, now } from '../../utils';
import { MemoryStorage } from '../../storage';

export class ParticleStore {
  constructor(private storage: MemoryStorage) {}

  create(content: string, context: FlowContext, summary?: string): FlowParticleSnapshot {
    const state: FlowParticleState = {
      id: randomId(),
      status: 'draft',
      content,
      summary,
      context,
      createdAt: now(),
      updatedAt: now(),
    };

    const snapshot: FlowParticleSnapshot = {
      id: state.id,
      history: [{ state, by: 'system', note: 'created' }],
      latest: state,
    };

    return this.storage.upsertParticle(snapshot);
  }

  collapse(id: string, by: string, note?: string): FlowParticleSnapshot {
    const current = this.storage.getParticle(id);
    if (!current) {
      throw new Error(`Particle ${id} not found`);
    }

    const nextState: FlowParticleState = {
      ...current.latest,
      status: 'collapsed',
      updatedAt: now(),
    };

    const historyEntry: FlowParticleHistory = { state: nextState, by, note };
    const updated: FlowParticleSnapshot = {
      ...current,
      latest: nextState,
      history: [...current.history, historyEntry],
    };

    return this.storage.upsertParticle(updated);
  }

  archive(id: string, by: string, note?: string): FlowParticleSnapshot {
    const current = this.storage.getParticle(id);
    if (!current) {
      throw new Error(`Particle ${id} not found`);
    }

    const nextState: FlowParticleState = {
      ...current.latest,
      status: 'archived',
      updatedAt: now(),
    };

    const historyEntry: FlowParticleHistory = { state: nextState, by, note };
    const updated: FlowParticleSnapshot = {
      ...current,
      latest: nextState,
      history: [...current.history, historyEntry],
    };

    return this.storage.upsertParticle(updated);
  }

  get(id: string): FlowParticleSnapshot | undefined {
    return this.storage.getParticle(id);
  }

  list(): FlowParticleSnapshot[] {
    return this.storage.listParticles();
  }
}
