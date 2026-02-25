import * as dotenv from 'dotenv';

dotenv.config({ path: '.env.test' });

/**
 * API client for E2E tests (runs in Node.js, outside the browser).
 *
 * Calls the backend directly (default: http://localhost:8765). Next.js rewrites
 * do not properly proxy POST/PUT/DELETE to external URLs, so going through
 * BASE_URL (frontend proxy) causes "Method Not Allowed" for API calls.
 *
 * Set API_URL in .env.test if your backend runs on a different port.
 */
const DEFAULT_API_URL = 'http://localhost:8765';

export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl?: string) {
    this.baseUrl =
      baseUrl || process.env.API_URL || DEFAULT_API_URL;
  }

  /**
   * Delete an organization by ID
   * Requires authentication token
   */
  async deleteOrganization(orgId: string, authToken: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/api/v1/orgs/${orgId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok && response.status !== 404) {
      throw new Error(`Failed to delete org ${orgId}: ${response.statusText}`);
    }
  }

  /**
   * Get current user's organizations
   */
  async getUserOrgs(authToken: string): Promise<any[]> {
    const response = await fetch(`${this.baseUrl}/api/v1/orgs`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to get orgs: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * List personas for an organization
   */
  async listPersonas(
    orgId: string,
    authToken: string,
    isActive?: boolean
  ): Promise<any[]> {
    const params = new URLSearchParams();
    if (isActive !== undefined) {
      params.append('is_active', String(isActive));
    }
    const query = params.toString();
    const url = `${this.baseUrl}/api/v1/orgs/${orgId}/personas${query ? `?${query}` : ''}`;

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to list personas: ${response.statusText}`);
    }

    const data = await response.json();
    return data.personas || [];
  }

  /**
   * Get a specific persona by ID
   */
  async getPersona(orgId: string, personaId: string, authToken: string): Promise<any> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/orgs/${orgId}/personas/${personaId}`,
      {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to get persona: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * Create a new persona
   */
  async createPersona(orgId: string, data: any, authToken: string): Promise<any> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/orgs/${orgId}/personas`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to create persona: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * Update an existing persona
   */
  async updatePersona(
    orgId: string,
    personaId: string,
    data: any,
    authToken: string
  ): Promise<any> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/orgs/${orgId}/personas/${personaId}`,
      {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to update persona: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * Delete a persona (hard delete - backend does not support soft delete)
   */
  async deletePersona(
    orgId: string,
    personaId: string,
    authToken: string
  ): Promise<void> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/orgs/${orgId}/personas/${personaId}`,
      {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok && response.status !== 404) {
      throw new Error(`Failed to delete persona: ${response.statusText}`);
    }
  }

  /**
   * Set a persona as the default
   */
  async setPersonaDefault(
    orgId: string,
    personaId: string,
    authToken: string
  ): Promise<any> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/orgs/${orgId}/personas/${personaId}/set-default`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({}),
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to set default persona: ${response.statusText}`);
    }

    return await response.json();
  }

  // ─── Agents ────────────────────────────────────────

  /**
   * List agents for an organization
   */
  async listAgents(orgId: string, authToken: string): Promise<any[]> {
    const response = await fetch(`${this.baseUrl}/api/v1/orgs/${orgId}/agents`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to list agents: ${response.statusText}`);
    }

    const data = await response.json();
    return data.agents || [];
  }

  /**
   * Create an agent in an organization.
   * Pass bypassVerification to skip real verification for test speed.
   */
  async createAgent(
    orgId: string,
    data: any,
    authToken: string,
    options?: { bypassVerification?: 'verified' | 'failed' }
  ): Promise<any> {
    const headers: Record<string, string> = {
      'Authorization': `Bearer ${authToken}`,
      'Content-Type': 'application/json',
    };
    if (options?.bypassVerification) {
      headers['X-Test-Bypass'] = `verification:${options.bypassVerification}`;
    }

    const response = await fetch(`${this.baseUrl}/api/v1/orgs/${orgId}/agents`, {
      method: 'POST',
      headers,
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const errorBody = await response.text();
      throw new Error(`Failed to create agent (${response.status}): ${errorBody}`);
    }

    return await response.json();
  }

  /**
   * Get a specific agent by ID
   */
  async getAgent(orgId: string, agentId: string, authToken: string): Promise<any> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/orgs/${orgId}/agents/${agentId}`,
      {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to get agent: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * Get verification status for an agent
   */
  async getAgentVerificationStatus(
    orgId: string,
    agentId: string,
    authToken: string
  ): Promise<{ status: string; attempts?: number; reasoning?: string; transcript?: string; last_verification_at?: string; error?: string }> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/orgs/${orgId}/agents/${agentId}/verification-status`,
      {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to get verification status: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * Poll for verification status until verified, failed, or timeout.
   * @param timeoutMs Total wait time (default 120000)
   * @param intervalMs Poll interval (default 3000)
   * @returns Final status object; status will be "verified", "failed", or last observed if timeout
   */
  async waitForVerification(
    orgId: string,
    agentId: string,
    authToken: string,
    timeoutMs: number = 120000,
    intervalMs: number = 3000
  ): Promise<{ status: string; attempts?: number; reasoning?: string; transcript?: string; last_verification_at?: string; error?: string }> {
    const start = Date.now();
    while (Date.now() - start < timeoutMs) {
      const result = await this.getAgentVerificationStatus(orgId, agentId, authToken);
      if (result.status === 'verified' || result.status === 'failed') {
        return result;
      }
      await new Promise((r) => setTimeout(r, intervalMs));
    }
    return await this.getAgentVerificationStatus(orgId, agentId, authToken);
  }

  /**
   * Update an agent.
   * Pass bypassVerification to skip real re-verification when contact info changes.
   */
  async updateAgent(
    orgId: string,
    agentId: string,
    data: any,
    authToken: string,
    options?: { bypassVerification?: 'verified' | 'failed' }
  ): Promise<any> {
    const headers: Record<string, string> = {
      'Authorization': `Bearer ${authToken}`,
      'Content-Type': 'application/json',
    };
    if (options?.bypassVerification) {
      headers['X-Test-Bypass'] = `verification:${options.bypassVerification}`;
    }

    const response = await fetch(
      `${this.baseUrl}/api/v1/orgs/${orgId}/agents/${agentId}`,
      {
        method: 'PUT',
        headers,
        body: JSON.stringify(data),
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to update agent: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * Delete an agent
   */
  async deleteAgent(orgId: string, agentId: string, authToken: string): Promise<void> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/orgs/${orgId}/agents/${agentId}`,
      {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to delete agent: ${response.statusText}`);
    }
  }

  // ─── Test Suites ───────────────────────────────────

  /**
   * List test suites for an organization
   */
  async listTestSuites(orgId: string, authToken: string): Promise<any[]> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/orgs/${orgId}/test-suites`,
      {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to list test suites: ${response.statusText}`);
    }

    const data = await response.json();
    return data.suites || [];
  }

  /**
   * Create a test suite
   */
  async createTestSuite(orgId: string, data: any, authToken: string): Promise<any> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/orgs/${orgId}/test-suites`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      }
    );

    if (!response.ok) {
      const errorBody = await response.text();
      throw new Error(`Failed to create test suite (${response.status}): ${errorBody}`);
    }

    return await response.json();
  }

  /**
   * Get a test suite by ID
   */
  async getTestSuite(orgId: string, suiteId: string, authToken: string): Promise<any> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/orgs/${orgId}/test-suites/${suiteId}`,
      {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to get test suite: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * Update a test suite
   */
  async updateTestSuite(
    orgId: string,
    suiteId: string,
    data: any,
    authToken: string
  ): Promise<any> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/orgs/${orgId}/test-suites/${suiteId}`,
      {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to update test suite: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * Delete a test suite.
   * Throws on 4xx/5xx (including 404) so callers can distinguish failure from success.
   */
  async deleteTestSuite(
    orgId: string,
    suiteId: string,
    authToken: string
  ): Promise<void> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/orgs/${orgId}/test-suites/${suiteId}`,
      {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to delete test suite: ${response.status} ${response.statusText}`);
    }
  }

  /**
   * Get generation status of a test suite.
   * Used for polling until generation completes.
   */
  async getGenerationStatus(
    orgId: string,
    suiteId: string,
    authToken: string
  ): Promise<{ status: string; scenario_count: number; error: string | null }> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/orgs/${orgId}/test-suites/${suiteId}/generation-status`,
      {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to get generation status: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * Poll until test suite generation completes (status becomes "ready" or "generation_failed").
   * @param timeoutMs Maximum time to wait (default 120s)
   * @param intervalMs Polling interval (default 2s)
   */
  async waitForGeneration(
    orgId: string,
    suiteId: string,
    authToken: string,
    timeoutMs: number = 120000,
    intervalMs: number = 2000,
  ): Promise<{ status: string; scenario_count: number }> {
    const start = Date.now();
    while (Date.now() - start < timeoutMs) {
      const result = await this.getGenerationStatus(orgId, suiteId, authToken);
      if (result.status === 'ready' || result.status === 'generation_failed') {
        return { status: result.status, scenario_count: result.scenario_count };
      }
      await new Promise((r) => setTimeout(r, intervalMs));
    }
    throw new Error(`Generation timed out after ${timeoutMs}ms for suite ${suiteId}`);
  }

  /**
   * Set persona active/inactive status
   */
  async setPersonaActive(
    orgId: string,
    personaId: string,
    isActive: boolean,
    authToken: string
  ): Promise<any> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/orgs/${orgId}/personas/${personaId}/active`,
      {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ is_active: isActive }),
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to set persona active status: ${response.statusText}`);
    }

    return await response.json();
  }
}
