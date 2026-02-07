/**
 * Auth API client for user and organization management.
 */

import { BaseApiClient } from "./base";

export interface UserResponse {
  id: string;
  email: string;
  name: string | null;
  avatar_url: string | null;
  auth_provider: string;
  is_active: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export interface OrgSummary {
  id: string;
  name: string;
  role: string;
}

export interface ActiveOrgResponse {
  id: string;
  name: string;
}

export interface AuthMeResponse {
  user: UserResponse;
  active_org: ActiveOrgResponse | null;
  orgs: OrgSummary[];
}

export interface UserUpdateRequest {
  name?: string;
  avatar_url?: string;
  last_active_org_id?: string;
}

export class AuthApi extends BaseApiClient {
  /**
   * Get current user profile with organizations.
   * This also triggers user upsert and org creation on the backend.
   * Returns null if unauthorized (doesn't redirect - lets caller handle it).
   */
  async getMe(): Promise<AuthMeResponse | null> {
    try {
      // Skip automatic redirect on 401 - we handle it gracefully
      return await this.get<AuthMeResponse>("/v1/auth/me", { skipRedirectOn401: true });
    } catch (err) {
      // Return null on auth errors instead of throwing
      if (err instanceof Error && err.message === "Unauthorized") {
        return null;
      }
      throw err;
    }
  }

  /**
   * Update current user profile.
   */
  async updateMe(data: UserUpdateRequest): Promise<UserResponse> {
    return this.patch<UserResponse>("/v1/auth/me", data);
  }

  /**
   * Create a new organization.
   */
  async createOrg(name: string): Promise<OrgSummary> {
    return this.post<OrgSummary>("/v1/orgs", { name });
  }
}
