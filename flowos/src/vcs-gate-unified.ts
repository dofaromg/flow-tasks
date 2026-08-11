import { ParticleDefensiveClient } from './core/defensive_client';

type CommitFile = {
  path: string;
  content: string;
};

type CommitRequest = {
  files?: Record<string, string> | CommitFile[];
  message?: string;
  branch?: string;
};

type GitHubError = {
  error: string;
  status: number;
  details?: string;
};

type GitHubContentResponse = {
  sha?: string;
};

/**
 * Commit Claude/agent task output to GitHub through the Contents API.
 *
 * Required environment variables:
 * - GITHUB_TOKEN
 * - GITHUB_REPO (owner/repo)
 * - ENABLE_GITHUB_SYNC=true
 */
export async function handleVCSCommit(
  request: { json(): Promise<unknown> },
  env: {
    GITHUB_TOKEN?: string;
    ENABLE_GITHUB_SYNC?: boolean;
    GITHUB_REPO?: string;
  },
): Promise<Response> {
  if (!env.ENABLE_GITHUB_SYNC) {
    return Response.json(
      { ok: false, error: 'GITHUB_SYNC_DISABLED' },
      { status: 503 },
    );
  }

  if (!env.GITHUB_TOKEN || !env.GITHUB_REPO) {
    return Response.json(
      {
        ok: false,
        error: 'GITHUB_CONFIGURATION_MISSING',
        required: ['GITHUB_TOKEN', 'GITHUB_REPO'],
      },
      { status: 503 },
    );
  }

  let body: CommitRequest;
  try {
    body = (await request.json()) as CommitRequest;
  } catch {
    return Response.json(
      { ok: false, error: 'INVALID_JSON_BODY' },
      { status: 400 },
    );
  }

  const files = normalizeFiles(body.files);
  if (files.length === 0) {
    return Response.json(
      { ok: false, error: 'NO_FILES_TO_COMMIT' },
      { status: 400 },
    );
  }

  const defensiveClient = new ParticleDefensiveClient({
    baseUrl: 'https://api.github.com',
    token: env.GITHUB_TOKEN,
    externalVersions: { github: '2022-11-28' },
    internalVersion: '4.0.0',
  });

  const repo = env.GITHUB_REPO;
  const branch = body.branch || 'main';
  const message = body.message || 'chore: submit Claude task output';
  const committed: Array<{ path: string; commitSha?: string }> = [];

  for (const file of files) {
    const encodedPath = file.path
      .split('/')
      .map((segment) => encodeURIComponent(segment))
      .join('/');
    const endpoint = `/repos/${repo}/contents/${encodedPath}`;

    const existing = await defensiveClient.callGitHub(
      `${endpoint}?ref=${encodeURIComponent(branch)}`,
      'GET',
    );

    let existingSha: string | undefined;
    if (!isGitHubError(existing)) {
      existingSha = (existing as GitHubContentResponse | null)?.sha;
    } else if (existing.status !== 404) {
      return githubFailure(file.path, existing);
    }

    const payload: Record<string, unknown> = {
      message,
      branch,
      content: utf8ToBase64(file.content),
    };
    if (existingSha) payload.sha = existingSha;

    const result = await defensiveClient.callGitHub(endpoint, 'PUT', payload);
    if (isGitHubError(result)) {
      return githubFailure(file.path, result);
    }

    const commitSha = extractCommitSha(result);
    committed.push({ path: file.path, commitSha });
  }

  return Response.json({
    ok: true,
    repository: repo,
    branch,
    committed,
    count: committed.length,
  });
}

function normalizeFiles(files: CommitRequest['files']): CommitFile[] {
  if (Array.isArray(files)) {
    return files.filter(
      (file): file is CommitFile =>
        Boolean(file) &&
        typeof file.path === 'string' &&
        file.path.trim().length > 0 &&
        typeof file.content === 'string',
    );
  }

  if (files && typeof files === 'object') {
    return Object.entries(files)
      .filter(([path, content]) => path.trim().length > 0 && typeof content === 'string')
      .map(([path, content]) => ({ path, content }));
  }

  return [];
}

function isGitHubError(value: unknown): value is GitHubError {
  return Boolean(
    value &&
      typeof value === 'object' &&
      'error' in value &&
      'status' in value,
  );
}

function extractCommitSha(value: unknown): string | undefined {
  if (!value || typeof value !== 'object') return undefined;
  const commit = (value as { commit?: { sha?: unknown } }).commit;
  return typeof commit?.sha === 'string' ? commit.sha : undefined;
}

function githubFailure(path: string, error: GitHubError): Response {
  return Response.json(
    {
      ok: false,
      error: 'GITHUB_COMMIT_FAILED',
      path,
      status: error.status,
      details: error.details || error.error,
    },
    { status: error.status >= 400 && error.status < 600 ? error.status : 502 },
  );
}

function utf8ToBase64(value: string): string {
  const bytes = new TextEncoder().encode(value);
  const chunkSize = 0x8000;
  const chunks: string[] = [];
  for (let i = 0; i < bytes.length; i += chunkSize) {
    const chunk = bytes.subarray(i, i + chunkSize);
    chunks.push(String.fromCharCode.apply(null, Array.from(chunk)));
  }
  return btoa(chunks.join(''));
}
