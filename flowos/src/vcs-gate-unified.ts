import { ParticleDefensiveClient } from './core/defensive_client';

/**
 * Enhanced VCS Commit Handler with configurable repository
 * 
 * This handler provides defensive GitHub synchronization for VCS commits.
 * It can be used via the `/vcs/commit_defensive` route in the main application.
 * 
 * Environment variables required:
 * - GITHUB_TOKEN: GitHub personal access token for API authentication
 * - ENABLE_GITHUB_SYNC: Set to true to enable GitHub synchronization
 * - GITHUB_REPO: Repository in format "owner/repo" (defaults to "mrliou/particles")
 * 
 * @param request - The incoming request with commit data
 * @param env - Environment configuration including GitHub token and sync settings
 * @returns A Response indicating success or failure
 */
export async function handleVCSCommit(
  request: { json(): Promise<unknown> },
  env: {
    GITHUB_TOKEN?: string;
    ENABLE_GITHUB_SYNC?: boolean;
    GITHUB_REPO?: string;
  }
): Promise<Response> {
  const defensiveClient = new ParticleDefensiveClient({
    baseUrl: 'https://api.github.com',
    token: env.GITHUB_TOKEN,
    externalVersions: { github: '2022-11-28' },
    internalVersion: '4.0.0',
  });

  const body = (await request.json()) as { files?: unknown };

  if (env.ENABLE_GITHUB_SYNC) {
    // Use configured repo or default to mrliou/particles
    const repo = env.GITHUB_REPO || 'mrliou/particles';
    const repoPath = `/repos/${repo}/git/blobs`;
    
    try {
      await defensiveClient.callGitHub(repoPath, 'POST', {
        content: JSON.stringify(body.files ?? {}),
        encoding: 'utf-8',
      });
    } catch (error) {
      console.warn('GitHub sync failed, but particle system remains intact:', error);
    }
  }

  return Response.json({
    ok: true,
    philosophy: '怎麼過去，就怎麼回來 (Defensive Mode Active)',
  });
}
