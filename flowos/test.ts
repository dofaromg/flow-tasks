// Test for FlowOS Neural Link System (v4.0.0)
// This file validates the core neural link functionality

import { NeuralLink, ParticleNeuralLink, NeuralLinkPacket } from './src/core/neural_link';
import { ConfigManager } from './src/core/config';
import { FlowGate, GateEngine } from './src/core/gate';

const FLOWOS_VERSION = '4.0.0';

async function runTests() {
  // Test NeuralLink event system
  const link = new NeuralLink();
  const packets: NeuralLinkPacket[] = [];

  link.on('test-event', async (packet) => {
    packets.push(packet);
    console.log('Received packet:', packet.type);
  });

  await link.transmit('test-event', { message: 'Hello Neural Link' });

  if (packets.length > 0 && packets[0].type === 'test-event') {
    console.log('✓ NeuralLink event transmission working');
  } else {
    console.error('✗ NeuralLink test failed');
  }

  // Test ConfigManager
  const config = new ConfigManager({ version: FLOWOS_VERSION });
  config.update({ philosophy: '怎麼過去，就怎麼回來' });
  const version = config.get('version');
  const philosophy = config.get('philosophy');

  if (version === FLOWOS_VERSION && philosophy === '怎麼過去，就怎麼回來') {
    console.log('✓ ConfigManager working');
  } else {
    console.error('✗ ConfigManager test failed');
  }

  // Test GateEngine
  const gate = new GateEngine();
  gate.register((payload) => {
    if (payload.blocked) {
      return { allowed: false, reason: 'Test block' };
    }
    return null;
  });

  const allowedDecision = gate.evaluate({ test: true });
  const blockedDecision = gate.evaluate({ blocked: true });

  if (allowedDecision.allowed && !blockedDecision.allowed) {
    console.log('✓ GateEngine working');
  } else {
    console.error('✗ GateEngine test failed');
  }

  // Test GateEngine terminal deny behavior (deny overrides allow)
  const terminalGate = new GateEngine();
  terminalGate.register((payload) => {
    // First check: allow if trusted
    if (payload.trusted) {
      return { allowed: true };
    }
    return null;
  });
  terminalGate.register((payload) => {
    // Second check: deny if blocked (should override earlier allow)
    if (payload.blocked) {
      return { allowed: false, reason: 'blocked' };
    }
    return null;
  });

  // Test case from PR description: trusted=true, blocked=true
  const terminalDenyDecision = terminalGate.evaluate({ trusted: true, blocked: true });

  if (!terminalDenyDecision.allowed && terminalDenyDecision.reason === 'blocked') {
    console.log('✓ GateEngine terminal deny behavior working (deny overrides allow)');
  } else {
    console.error('✗ GateEngine terminal deny test failed');
  }

  console.log(`\nFlowOS Neural Link System v${FLOWOS_VERSION} - Tests Complete`);
  console.log('Philosophy: 怎麼過去，就怎麼回來');
}

runTests().catch(console.error);
