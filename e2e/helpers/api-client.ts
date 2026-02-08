import * as dotenv from 'dotenv';

dotenv.config({ path: '.env.test' });

export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl || process.env.BASE_URL || 'http://localhost:3000';
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
}
