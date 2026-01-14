/**
 * 夥伴防禦性客戶端 (Partner Defensive Client)
 * 核心原則：鎖定時間維度，確保「怎麼過去，就怎麼回來」
 */

export interface ClientConfig {
  baseUrl: string;
  token?: string;
  externalVersions: {
    github: '2022-11-28';
    openai?: '2024-02-15-preview';
  };
  internalVersion: '4.0.0';
}

interface RequestInit {
  method?: string;
  headers?: Record<string, string>;
  body?: string;
}

interface RequestInfo {}

interface Response {
  ok: boolean;
  status: number;
  statusText: string;
  headers: { get(name: string): string | null };
  json(): Promise<unknown>;
}

declare function fetch(input: RequestInfo | string, init?: RequestInit): Promise<Response>;

export class ParticleDefensiveClient {
  private config: ClientConfig;

  constructor(config: ClientConfig) {
    this.config = config;
  }

  /**
   * 安全地呼叫 GitHub API (用於 VCS 系統)
   * 應用了我們剛才討論的 Header 鎖定策略
   */
  async callGitHub(
    endpoint: string,
    method: string = 'GET',
    body?: Record<string, unknown>,
  ): Promise<unknown | null> {
    const url = `${this.config.baseUrl}${endpoint}`;
    const headers: Record<string, string> = {
      'X-GitHub-Api-Version': this.config.externalVersions.github,
      Accept: 'application/vnd.github+json',
      'User-Agent': 'MrLiouWord-Particle-Edge/4.0.0',
      'Content-Type': 'application/json',
    };
    if (this.config.token) {
      headers.Authorization = `Bearer ${this.config.token}`;
    }

    try {
      const response = await fetch(url, {
        method,
        headers,
        body: body ? JSON.stringify(body) : undefined,
      });

      if (
        response.status === 400 &&
        response.headers.get('x-github-api-version') !== this.config.externalVersions.github
      ) {
        console.error(
          `⚠️ 警告：GitHub API 版本協定脫鉤。預期: ${this.config.externalVersions.github}`,
        );
        throw new Error('External_System_Protocol_Mismatch');
      }

      if (!response.ok) {
        throw new Error(`GitHub Error: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('粒子傳輸失敗 (GitHub):', error);
      return null;
    }
  }

  /**
   * 內部層級通訊 (Layer-to-Layer)
   * 例如 L2 Router 呼叫 L5 Durable Object
   */
  async callInternalLayer(layer: string, path: string, payload: Record<string, unknown>): Promise<unknown> {
    void layer;
    void path;
    void payload;
    return { ok: true, note: '模擬內部通訊成功' };
  }
}
