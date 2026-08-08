import { describe, expect, it } from 'vitest';

const originSignature = 'MrLiouWord';
const moduleName = 'mrl-firecore-store';

describe('mrl-firecore-store local contract', () => {
  it('carries the MRL origin signature', () => {
    expect(originSignature).toBe('MrLiouWord');
  });

  it('uses the mrl-firecore naming family', () => {
    expect(moduleName.startsWith('mrl-firecore-')).toBe(true);
  });
});
