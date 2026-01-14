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
    let allowDecision: GateDecision | null = null;

    for (const check of this.checks) {
      const decision = check(payload, context);

      // Skip checks that choose not to make a decision
      if (!decision) {
        continue;
      }

      // Deny decisions are terminal and override any prior allows
      if (decision.allowed === false) {
        return decision;
      }

      // Remember the first explicit allow, but keep evaluating in case a later check denies
      if (!allowDecision) {
        allowDecision = decision;
      }
    }

    // If we saw at least one explicit allow, use it; otherwise fall back to default allow
    return allowDecision ?? { allowed: true };
  }
}

export class GateEngine extends FlowGate {}
