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

  /**
   * Evaluate all registered gate checks against the payload and context.
   * Checks are evaluated sequentially. If a check returns an explicit deny (allowed: false),
   * evaluation stops immediately and the deny decision is returned.
   * If a check returns an allow decision, it continues to subsequent checks in case a later check denies.
   * If all checks return null or only allow decisions, returns the first allow or a default allow.
   */
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
