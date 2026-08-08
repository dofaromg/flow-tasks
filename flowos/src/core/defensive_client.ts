/**
 * 夥伴防禦性客戶端 (Partner Defensive Client)
 * 核心原則：鎖定時間維度，確保「怎麼過去，就怎麼回來」
 */

/**
 * Configuration for the defensive client
 * 
 * Recommended API versions:
 * - GitHub: '2022-11-28' (locked for stability)
 * - OpenAI: '2024-02-15-preview'
 * - Internal: '4.0.0'
 * 
 * Note: Version strings can be overridden for testing, but production should use recommended values
 */
export interface ClientConfig {
  baseUrl: string;
  token?: string;
  externalVersions: {
    github: string; // Recommended: '2022-11-28'
    openai?: string; // Recommended: '2024-02-15-preview'
  };
  internalVersion: string; // Recommended: '4.0.0'
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
   * 
   * @returns The response data on success, or an error object with details on failure
   */
  async callGitHub(
    endpoint: string,
    method: string = 'GET',
    body?: Record<string, unknown>,
  ): Promise<unknown | { error: string; status: number; details?: string }> {
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
        return {
          error: 'External_System_Protocol_Mismatch',
          status: 400,
          details: `Expected API version: ${this.config.externalVersions.github}`
        };
      }

      if (!response.ok) {
        // Try to get error details from response
        let errorDetail = 'Unknown error';
        try {
          const errorBody = await response.json() as { message?: string };
          errorDetail = errorBody.message || JSON.stringify(errorBody);
        } catch {
          errorDetail = response.statusText || `Status ${response.status}`;
        }
        
        return {
          error: `GitHub Error: ${response.status}`,
          status: response.status,
          details: errorDetail
        };
      }

      return await response.json();
    } catch (error) {
      console.error('粒子傳輸失敗 (GitHub):', error);
      return {
        error: 'Network Error',
        status: 0,
        details: error instanceof Error ? error.message : String(error)
      };
    }
  }

  /**
   * Internal layer communication (Layer-to-Layer)
   * Example: L2 Router calling L5 Durable Object
   * 
   * Note: This is currently a stub implementation.
   * TODO: Implement actual internal layer communication when needed.
   */
  async callInternalLayer(layer: string, path: string, payload: Record<string, unknown>): Promise<unknown> {
    // Debug logging (only in development)
    if (process?.env?.NODE_ENV === 'development') {
      console.log(`Internal call to ${layer}${path} (stub)`);
    }
    void layer;
    void path;
    void payload;
    return { ok: true, note: 'Simulated internal communication success (stub)' };
  }
}
