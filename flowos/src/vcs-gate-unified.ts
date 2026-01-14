import { ParticleDefensiveClient } from './core/defensive_client';

export interface Env {
  GITHUB_TOKEN?: string;
  ENABLE_GITHUB_SYNC?: boolean;
}

interface Request {
  json(): Promise<unknown>;
}

interface ResponseInit {
  status?: number;
  headers?: Record<string, string>;
}

interface Response {
  json(): Promise<unknown>;
}

declare const Response: {
  json(data: unknown, init?: ResponseInit): Response;
};

/**
 * 增強版的 VCS Commit 處理器
 */
export async function handleVCSCommit(request: Request, env: Env): Promise<Response> {
  const defensiveClient = new ParticleDefensiveClient({
    baseUrl: 'https://api.github.com',
    token: env.GITHUB_TOKEN,
    externalVersions: { github: '2022-11-28' },
    internalVersion: '4.0.0',
  });

  const body = (await request.json()) as { files?: unknown };

  if (env.ENABLE_GITHUB_SYNC) {
    try {
      await defensiveClient.callGitHub('/repos/mrliou/particles/git/blobs', 'POST', {
        content: JSON.stringify(body.files ?? {}),
        encoding: 'utf-8',
      });
    } catch (error) {
      console.warn('GitHub 同步失敗，但粒子系統保持完整', error);
    }
  }

  return Response.json({
    ok: true,
    philosophy: '怎麼過去，就怎麼回來 (Defensive Mode Active)',
  });
}
