/**
 * Test Scenarios API client - integrates with backend /api/v1/tests/scenarios endpoints.
 */

import { BaseApiClient } from "./base";
import type {
  TestScenario,
  TestScenarioCreateRequest,
  TestScenarioUpdateRequest,
  TestScenariosListResponse,
  TestScenarioFilters,
} from "../types";

const API_BASE = "/api/v1/tests/scenarios";

export class TestScenariosApi extends BaseApiClient {
  /**
   * List all test scenarios with optional filtering and pagination.
   * GET /api/v1/tests/scenarios?suite_id={suite_id}&status={status}&limit={limit}&offset={offset}
   */
  async listTestScenarios(filters?: TestScenarioFilters): Promise<TestScenariosListResponse> {
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
    const url = queryString ? `${API_BASE}?${queryString}` : API_BASE;
    return this.get<TestScenariosListResponse>(url);
  }

  /**
   * Get a test scenario by ID.
   * GET /api/v1/tests/scenarios/{scenario_id}
   */
  async getTestScenario(id: string): Promise<TestScenario> {
    return this.get<TestScenario>(`${API_BASE}/${id}`);
  }

  /**
   * Create a new test scenario.
   * POST /api/v1/tests/scenarios
   */
  async createTestScenario(data: TestScenarioCreateRequest): Promise<TestScenario> {
    return this.post<TestScenario>(API_BASE, data);
  }

  /**
   * Update a test scenario.
   * PUT /api/v1/tests/scenarios/{scenario_id}
   */
  async updateTestScenario(id: string, data: TestScenarioUpdateRequest): Promise<TestScenario> {
    return this.put<TestScenario>(`${API_BASE}/${id}`, data);
  }

  /**
   * Delete a test scenario.
   * DELETE /api/v1/tests/scenarios/{scenario_id}
   */
  async deleteTestScenario(id: string): Promise<void> {
    return this.delete(`${API_BASE}/${id}`);
  }
}
