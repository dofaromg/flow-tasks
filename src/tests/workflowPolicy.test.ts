/**
 * Regression guard for repository Actions policy.
 *
 * The repository currently permits GitHub-owned and dofaromg-owned actions.
 * This test keeps the WebGPU workflow executable without weakening that policy,
 * while retaining locally generated coverage as a GitHub artifact.
 * Workflow execution also exercises the current Jest CLI contract.
 */

import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

describe('WebGPU workflow action policy', () => {
  const workflowPath = resolve(
    process.cwd(),
    '.github/workflows/webgpu-neural-network-ci.yml'
  );
  const workflow = readFileSync(workflowPath, 'utf8');

  test('uses only permitted action owners', () => {
    const actionRefs = [...workflow.matchAll(/^\s*uses:\s*([^\s#]+)\s*$/gm)].map(
      (match) => match[1]
    );

    expect(actionRefs.length).toBeGreaterThan(0);
    expect(actionRefs.every((ref) => /^(actions|dofaromg)\//.test(ref))).toBe(true);
  });

  test('generates and retains coverage evidence', () => {
    expect(workflow).toContain('npm test -- --coverage --ci');
    expect(workflow).toContain('uses: actions/upload-artifact@v4');
    expect(workflow).toContain('name: test-results');
    expect(workflow).toMatch(/^\s*coverage\/\s*$/m);
  });

  test('runs when its own workflow definition changes', () => {
    const occurrences =
      workflow.match(/\.github\/workflows\/webgpu-neural-network-ci\.yml/g) ?? [];

    expect(occurrences).toHaveLength(2);
  });
});
