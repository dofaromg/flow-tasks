import { FlowContext } from '../types';

export interface GateDecision {
  allowed: boolean;
  reason?: string;
  throttleMs?: number;
}

export type GateCheck = (payload: Record<string, unknown>, context?: FlowContext) => GateDecision | null;

/**
 * FlowGate provides request filtering and throttling through pluggable gate checks.
 * Deny decisions are terminal, while allow decisions continue evaluation.
 */
export class FlowGate {
  private readonly checks: GateCheck[] = [];

  /**
   * Register a new gate check function
   * @param check - Function that evaluates a payload and returns a decision or null
   */
  register(check: GateCheck): void {
    this.checks.push(check);
  }

  /**
   * Evaluate all registered checks against a payload.
   * Deny decisions are terminal and returned immediately.
   * Allow decisions continue evaluation in case a later check denies.
   * @param payload - Data to evaluate
   * @param context - Optional FlowContext
   * @returns Final gate decision
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
