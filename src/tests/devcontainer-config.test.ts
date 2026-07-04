import { readFileSync } from 'fs';
import { resolve } from 'path';

describe('Devcontainer config', () => {
  test('should be valid JSON without conflict markers', () => {
    const configPath = resolve(process.cwd(), '.devcontainer/devcontainer.json');
    const content = readFileSync(configPath, 'utf8');

    expect(() => JSON.parse(content)).not.toThrow();
    expect(content).not.toContain('<<<<<<<');
    expect(content).not.toContain('=======');
    expect(content).not.toContain('>>>>>>>');
  });
});
