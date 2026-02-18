# FlowOS - Lightweight Runtime Skeleton

FlowOS is a modular runtime system that provides core building blocks for the FlowAgent architecture. It can run both as a Cloudflare Workers edge deployment and as a local library.

## Architecture

FlowOS consists of two main components:

### 1. FlowOS Class (Local/Library Usage)

The main `FlowOS` class orchestrates all subsystems and provides a unified API:

```typescript
import { FlowOS } from './src';

const flow = new FlowOS();

// Create a context
const context = flow.createContext({ 
  persona: 'demo-persona',
  project: 'my-project'
});

// Create and manage particles
const particle = flow.particles.createParticle('Hello FlowOS', context, 'intro message');
flow.particles.collapseParticle(particle.id, 'demo');

// Start conversations
const conversation = flow.conversations.startConversation(context);
flow.conversations.appendMessage(conversation.id, 'user', 'Hello there', context);

// Manage projects and artifacts
const project = flow.projects.registerProject('FlowOS Sandbox', 'Playground for FlowOS runtime');
const artifact = flow.artifacts.registerArtifact(project.id, 'Transcript');
flow.artifacts.addVersion(artifact.id, 'v1');

// Store memories
flow.memory.remember('project', 'first-run', { 
  project: project.name, 
  conversation: conversation.id 
});

// Get system snapshot
console.log('Flow snapshot:', JSON.stringify(flow.snapshot(), null, 2));

// Check flow law compliance
console.log('FlowLaw:', flow.enforce());

// Access Merkle chain digest
console.log('Chain digest:', flow.chain.digest());
```

### 2. Edge Worker (Cloudflare Workers)

FlowOS also exports a default edge worker handler for Cloudflare Workers deployment:

- **Endpoint**: Deployed as `flowos-neural-gate` worker
- **Features**:
  - Neural link integration for external API calls (GitHub, etc.)
  - Traffic gate with Durable Objects
  - Version control system (VCS) integration
  - Persona management
  - R2 bucket integration
  - Master key authentication

## Core Components

### Particle Engine
Manages particle lifecycle: creation, collapse, archival, and state tracking with full history.

```typescript
flow.particles.createParticle(content, context, summary);
flow.particles.collapseParticle(particleId, by, note);
flow.particles.archiveParticle(particleId, by, note);
flow.particles.listParticles();
```

### Conversation Manager
Handles conversation threads and messages with persona and project associations.

```typescript
flow.conversations.startConversation(context);
flow.conversations.appendMessage(threadId, author, content, context);
flow.conversations.list();
```

### Project Registry
Registers and manages projects with metadata.

```typescript
flow.projects.registerProject(name, description);
flow.projects.listProjects();
```

### Artifact Vault
Manages versioned artifacts within projects.

```typescript
flow.artifacts.registerArtifact(projectId, name, description);
flow.artifacts.addVersion(artifactId, version, metadata);
flow.artifacts.listArtifacts();
```

### Memory System
Stores and retrieves memories across different scopes (conversation, project, global).

```typescript
flow.memory.remember(scope, topic, payload);
flow.memory.recall(scope);
```

### Merkle Chain
Provides cryptographic verification of event sequences.

```typescript
flow.chain.append(event, context);
flow.chain.verify();
flow.chain.digest();
```

### FlowLaw
Validates system state against predefined rules to maintain consistency.

```typescript
const result = flow.enforce(context);
// Returns: { passed: boolean, violations: FlowLawViolation[] }
```

## Building and Testing

```bash
# Build TypeScript
npm run build

# Run demo (manual validation script, not automated tests)
npm run test

# Type check without emitting files
npm run typecheck
```

Note: `npm run test` runs a demonstration script (`test.ts`) that exercises the core FlowOS functionality. It's not an automated test suite, but rather a manual validation tool.

## Storage

All data is stored in-memory using the `MemoryStorage` class, which provides:
- Particle snapshots
- Persona records
- Seed definitions
- Conversation threads
- Project metadata
- Artifact records
- Memory entries

The storage system supports full state snapshots for backup and restoration.

## Configuration

For edge worker deployment, configure `wrangler.toml`:

```toml
name = "flowos-neural-gate"
main = "src/index.ts"
compatibility_date = "2024-12-01"
compatibility_flags = ["nodejs_compat"]
```

## Environment Variables (Edge Worker)

- `MASTER_KEY`: Authentication key for protected endpoints
- `GITHUB_TOKEN`: GitHub API token for VCS operations
- `VERSION`: FlowOS version identifier
- `ORIGIN`: Origin identifier (e.g., "MrLiouWord")

## Philosophy

FlowOS follows the MrLiouWord principle: **"怎麼過去，就怎麼回來"** (How it went, so it shall return)

This reflects the system's commitment to maintaining consistency, traceability, and reversibility through:
- Comprehensive history tracking
- Merkle chain verification
- Flow law enforcement
- Snapshot capabilities

## License

See LICENSE files in the repository root.
