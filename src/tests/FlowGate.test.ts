import { FlowGate } from '../../flowos/src/core/gate';

describe('FlowGate', () => {
  it('allows a payload when no checks are registered', () => {
    expect(new FlowGate().evaluate({})).toEqual({ allowed: true });
  });

  it('returns the first explicit allow decision when every check allows', () => {
    const gate = new FlowGate();

    gate.register(() => null);
    gate.register(() => ({ allowed: true, reason: 'first allow', throttleMs: 25 }));
    gate.register(() => ({ allowed: true, reason: 'second allow' }));

    expect(gate.evaluate({ operation: 'publish' })).toEqual({
      allowed: true,
      reason: 'first allow',
      throttleMs: 25,
    });
  });

  it('continues past allow decisions and returns a later denial', () => {
    const gate = new FlowGate();

    gate.register(() => ({ allowed: true, reason: 'preliminary allow' }));
    gate.register(() => null);
    gate.register(() => ({ allowed: false, reason: 'policy denied' }));

    expect(gate.evaluate({ operation: 'delete' })).toEqual({
      allowed: false,
      reason: 'policy denied',
    });
  });

  it('stops evaluating checks after the first denial', () => {
    const gate = new FlowGate();
    const laterCheck = jest.fn(() => ({ allowed: true }));

    gate.register(() => ({ allowed: false, reason: 'blocked' }));
    gate.register(laterCheck);

    expect(gate.evaluate({})).toEqual({ allowed: false, reason: 'blocked' });
    expect(laterCheck).not.toHaveBeenCalled();
  });
});
