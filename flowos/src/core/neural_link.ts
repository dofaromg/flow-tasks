interface NeuralLinkEnv {
  GITHUB_TOKEN?: string;
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
  statusText?: string;
  headers?: { get(name: string): string | null };
  json(): Promise<unknown>;
}

declare function fetch(input: RequestInfo | string, init?: RequestInit): Promise<Response>;

export class ParticleNeuralLink {
  constructor(
    private readonly env: NeuralLinkEnv,
    private readonly nodeId: string,
  ) {}

  async fireInternal(
    stub: { fetch(input: RequestInfo, init?: RequestInit): Promise<Response> },
    path: string,
    payload: Record<string, unknown>,
  ): Promise<Response> {
    return await stub.fetch(`https://internal${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Node-Id': this.nodeId },
      body: JSON.stringify(payload),
    });
  }

  /**
   * Fire external API call with defensive error handling
   * 
   * @returns The response data on success, or an error object with details on failure
   * @throws Error for non-400 failures that should be handled by caller
   */
  async fireExternal(
    path: string,
    method: string,
    payload?: Record<string, unknown>,
  ): Promise<unknown | { error: string; status: number; details?: string }> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'X-GitHub-Api-Version': '2022-11-28',
      Accept: 'application/vnd.github+json',
      'X-Node-Id': this.nodeId,
    };
    
    // Validate token presence for authenticated operations
    if (this.env.GITHUB_TOKEN) {
      headers.Authorization = `Bearer ${this.env.GITHUB_TOKEN}`;
    } else if (method !== 'GET') {
      // Warn if attempting non-GET operations without token (likely require auth)
      console.warn('⚠️ Attempting authenticated GitHub operation without token', { path, method });
    }
    
    try {
      const response = await fetch(`https://api.github.com${path}`, {
        method,
        headers,
        body: payload ? JSON.stringify(payload) : undefined,
      });
      
      if (response.status === 400) {
        console.warn('⚠️ GitHub API 400 error - version may be unsupported or request invalid', {
          path,
          method,
          status: response.status
        });
        return {
          error: 'Bad Request',
          status: 400,
          details: 'GitHub API version may be unsupported or request is invalid'
        };
      }
      
      if (!response.ok) {
        // Try to get error details from response
        let errorDetail = 'Unknown error';
        try {
          const errorBody = await response.json() as { message?: string };
          errorDetail = errorBody.message || JSON.stringify(errorBody);
        } catch {
          errorDetail = `Status ${response.status}`;
        }
        
        // Return error object instead of throwing for better error handling
        return {
          error: `GitHub API Error: ${response.status}`,
          status: response.status,
          details: errorDetail
        };
      }
      
      return await response.json();
    } catch (error) {
      console.error('External call error:', { path, method, error });
      // Return error object for network failures
      return {
        error: 'Network Error',
        status: 0,
        details: error instanceof Error ? error.message : String(error)
      };
    }
  }
}
