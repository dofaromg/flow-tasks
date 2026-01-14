// Note: The FlowOS class-based API has been replaced with a Cloudflare Worker-based architecture.
// This test file needs to be rewritten for the new Worker fetch() API.
// The old FlowOS class is no longer available.

// Example of how to test the new Worker architecture:
// Use Miniflare or wrangler dev for local testing, or write unit tests for individual components.

// TODO: Implement proper Worker-based tests using Miniflare or Vitest
// See: https://developers.cloudflare.com/workers/testing/

/*
import { FlowOS } from './src';

const flow = new FlowOS();
const context = flow.createContext({ persona: 'demo-persona' });

const particle = flow.particles.createParticle('Hello FlowOS', context, 'intro message');
flow.particles.collapseParticle(particle.id, 'demo');

const conversation = flow.conversations.startConversation(context);
flow.conversations.appendMessage(conversation.id, 'user', 'Hello there', context);

const project = flow.projects.registerProject('FlowOS Sandbox', 'Playground for FlowOS runtime');
const artifact = flow.artifacts.registerArtifact(project.id, 'Transcript');
flow.artifacts.addVersion(artifact.id, 'v1');

flow.memory.remember('project', 'first-run', { project: project.name, conversation: conversation.id });

console.log('Flow snapshot:', JSON.stringify(flow.snapshot(), null, 2));
console.log('Chain digest:', flow.chain.digest());
console.log('FlowLaw:', flow.enforce());
*/

console.log('Test file disabled - Worker architecture needs new testing approach');
