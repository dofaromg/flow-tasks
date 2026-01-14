import { FlowContext, FlowEvent, FlowSnapshot } from './types';
import { MemoryStorage } from './storage';
import { ParticleEngine } from './core/particles';
import { ParticleStore } from './core/particles/store';
import { MerkleChain } from './core/chains';
import { SeedRegistry } from './core/seeds';
import { PersonaRegistry } from './core/personas';
import { ConfigManager } from './core/config';
import { FlowGate, GateDecision } from './core/gate';
import { NeuralLink, NeuralLinkPacket } from './core/neural_link';
import { FlowLaw } from './lib/flow-law';
import { ConversationManager } from './app/conversations';
import { ProjectRegistry } from './app/projects';
import { ArtifactVault } from './app/artifacts';
import { MemorySystem } from './app/memory';
import { ToolRegistry } from './app/tools';
import { randomId, now } from './utils';

export interface NeuralSignalResult {
  decision: GateDecision;
  packet?: NeuralLinkPacket;
}

export class FlowOS {
  readonly storage: MemoryStorage;
  readonly particles: ParticleEngine;
  readonly particleStore: ParticleStore;
  readonly chain: MerkleChain;
  readonly seeds: SeedRegistry;
  readonly personas: PersonaRegistry;
  readonly config: ConfigManager;
  readonly gate: FlowGate;
  readonly neuralLink: NeuralLink;
  readonly flowLaw: FlowLaw;
  readonly conversations: ConversationManager;
  readonly projects: ProjectRegistry;
  readonly artifacts: ArtifactVault;
  readonly memory: MemorySystem;
  readonly tools: ToolRegistry;

  constructor() {
    this.storage = new MemoryStorage();
    this.particleStore = new ParticleStore();
    this.particles = new ParticleEngine(this.particleStore);
    this.chain = new MerkleChain();
    this.seeds = new SeedRegistry();
    this.personas = new PersonaRegistry();
    this.config = new ConfigManager();
    this.gate = new FlowGate();
    this.neuralLink = new NeuralLink();
    this.flowLaw = new FlowLaw();
    this.conversations = new ConversationManager(this.storage);
    this.projects = new ProjectRegistry(this.storage);
    this.artifacts = new ArtifactVault(this.storage);
    this.memory = new MemorySystem(this.storage);
    this.tools = new ToolRegistry();
  }

  createContext(partial: Partial<FlowContext> = {}): FlowContext {
    return {
      id: partial.id ?? randomId(),
      createdAt: partial.createdAt ?? now(),
      ...partial,
    };
  }

  dispatch(eventType: string, payload: Record<string, unknown>, context: FlowContext): FlowEvent {
    const event: FlowEvent = { id: randomId(), type: eventType, payload, createdAt: now() };
    this.chain.append(event, context);
    return event;
  }

  enforce(context?: FlowContext) {
    return this.flowLaw.evaluate(this.particles.listParticles(), context);
  }

  async emitSignal(
    type: string,
    payload: Record<string, unknown>,
    context?: FlowContext,
  ): Promise<NeuralSignalResult> {
    const decision = this.gate.evaluate(payload, context);
    if (!decision.allowed) {
      return { decision };
    }
    const packet = await this.neuralLink.transmit(type, payload, context);
    return { decision, packet };
  }

  snapshot(): FlowSnapshot {
    const snapshot = this.storage.snapshot();
    return {
      ...snapshot,
      particles: this.particles.listParticles(),
    };
  }
}

export * from './types';
export * from './utils';
export * from './core/config';
export * from './core/gate';
export * from './core/neural_link';
export * from './adapters';
