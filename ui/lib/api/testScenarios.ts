/**
 * Test Scenarios API client - integrates with backend /api/v1/orgs/{orgId}/test-scenarios endpoints.
 */

import { BaseApiClient } from "./base";
import type {
  TestScenario,
  TestScenarioCreateRequest,
  TestScenarioUpdateRequest,
  TestScenariosListResponse,
  TestScenarioFilters,
} from "../types";

export class TestScenariosApi extends BaseApiClient {
  private getBase(orgId: string): string {
    return `/api/v1/orgs/${orgId}/test-scenarios`;
  }

  /**
   * List all test scenarios with optional filtering and pagination.
   * GET /api/v1/orgs/{orgId}/test-scenarios?suite_id={suite_id}&status={status}&limit={limit}&offset={offset}
   */
  async listTestScenarios(
    orgId: string,
    filters?: TestScenarioFilters
  ): Promise<TestScenariosListResponse> {
    const params = new URLSearchParams();
    if (filters?.suite_id) {
      params.append("suite_id", filters.suite_id);
    }
    if (filters?.persona_id) {
      params.append("persona_id", filters.persona_id);
    }
    if (filters?.status) {
      params.append("status", filters.status);
    }
    if (filters?.intent) {
      params.append("intent", filters.intent);
    }
    if (filters?.tag) {
      params.append("tag", filters.tag);
    }
    if (filters?.search) {
      params.append("search", filters.search);
    }
    if (filters?.limit !== undefined) {
      params.append("limit", String(filters.limit));
    }
    if (filters?.offset !== undefined) {
      params.append("offset", String(filters.offset));
    }
    const queryString = params.toString();
    const base = this.getBase(orgId);
    const url = queryString ? `${base}?${queryString}` : base;
    return this.get<TestScenariosListResponse>(url);
  }

  /**
   * Get a test scenario by ID.
   * GET /api/v1/orgs/{orgId}/test-scenarios/{scenario_id}
   */
  async getTestScenario(orgId: string, id: string): Promise<TestScenario> {
    return this.get<TestScenario>(`${this.getBase(orgId)}/${id}`);
  }

  /**
   * Create a new test scenario.
   * POST /api/v1/orgs/{orgId}/test-scenarios
   */
  async createTestScenario(orgId: string, data: TestScenarioCreateRequest): Promise<TestScenario> {
    return this.post<TestScenario>(this.getBase(orgId), data);
  }

  /**
   * Update a test scenario.
   * PUT /api/v1/orgs/{orgId}/test-scenarios/{scenario_id}
   */
  async updateTestScenario(
    orgId: string,
    id: string,
    data: TestScenarioUpdateRequest
  ): Promise<TestScenario> {
    return this.put<TestScenario>(`${this.getBase(orgId)}/${id}`, data);
  }

  /**
   * Delete a test scenario.
   * DELETE /api/v1/orgs/{orgId}/test-scenarios/{scenario_id}
   */
  async deleteTestScenario(orgId: string, id: string): Promise<void> {
    return this.delete(`${this.getBase(orgId)}/${id}`);
  }
}
