/**
 * Test Suites API client - integrates with backend /api/v1/tests/suites endpoints.
 */

import { BaseApiClient } from "./base";
import type {
  TestSuite,
  TestSuiteCreateRequest,
  TestSuiteUpdateRequest,
  TestSuitesListResponse,
  GenerationStatusResponse,
  GenerateScenariosRequest,
} from "../types";

const API_BASE = "/api/v1/tests/suites";

export class TestSuitesApi extends BaseApiClient {
  /**
   * List all test suites.
   * GET /api/v1/tests/suites
   */
  async listTestSuites(): Promise<TestSuitesListResponse> {
    return this.get<TestSuitesListResponse>(API_BASE);
  }

  /**
   * Get a test suite by ID.
   * GET /api/v1/tests/suites/{suite_id}
   */
  async getTestSuite(id: string): Promise<TestSuite> {
    return this.get<TestSuite>(`${API_BASE}/${id}`);
  }

  /**
   * Create a new test suite.
   * POST /api/v1/tests/suites
   */
  async createTestSuite(data: TestSuiteCreateRequest): Promise<TestSuite> {
    return this.post<TestSuite>(API_BASE, data);
  }

  /**
   * Update a test suite.
   * PUT /api/v1/tests/suites/{suite_id}
   */
  async updateTestSuite(id: string, data: TestSuiteUpdateRequest): Promise<TestSuite> {
    return this.put<TestSuite>(`${API_BASE}/${id}`, data);
  }

  /**
   * Delete a test suite.
   * DELETE /api/v1/tests/suites/{suite_id}
   */
  async deleteTestSuite(id: string): Promise<void> {
    return this.delete(`${API_BASE}/${id}`);
  }

  /**
   * Get the generation status for a test suite.
   * GET /api/v1/tests/suites/{suite_id}/generation-status
   */
  async getGenerationStatus(id: string): Promise<GenerationStatusResponse> {
    return this.get<GenerationStatusResponse>(`${API_BASE}/${id}/generation-status`);
  }

  /**
   * Generate more scenarios for a test suite.
   * Returns 400 if generation is already in progress.
   * POST /api/v1/tests/suites/{suite_id}/generate-scenarios
   */
  async generateMoreScenarios(
    id: string,
    request?: GenerateScenariosRequest
  ): Promise<GenerationStatusResponse> {
    return this.post<GenerationStatusResponse>(
      `${API_BASE}/${id}/generate-scenarios`,
      request || {}
    );
  }
}
