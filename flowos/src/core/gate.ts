import { FlowContext } from '../types';

export interface GateDecision {
  allowed: boolean;
  reason?: string;
  throttleMs?: number;
}

export type GateCheck = (payload: Record<string, unknown>, context?: FlowContext) => GateDecision | null;

export class FlowGate {
  private readonly checks: GateCheck[] = [];

  register(check: GateCheck): void {
    this.checks.push(check);
  }

  evaluate(payload: Record<string, unknown>, context?: FlowContext): GateDecision {
    let firstAllowDecision: GateDecision | null = null;

    for (const check of this.checks) {
      const decision = check(payload, context);
      if (!decision) {
        continue;
      }

      if (!decision.allowed) {
        return decision;
      }

      if (!firstAllowDecision) {
        firstAllowDecision = decision;
      }
    }

    return firstAllowDecision ?? { allowed: true };
  }
}

export class GateEngine extends FlowGate {}
