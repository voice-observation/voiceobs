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
