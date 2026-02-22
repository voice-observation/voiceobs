/**
 * Test Suites API client - integrates with backend /api/v1/orgs/{orgId}/test-suites endpoints.
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

export class TestSuitesApi extends BaseApiClient {
  private basePath(orgId: string): string {
    return `/api/v1/orgs/${orgId}/test-suites`;
  }

  /**
   * List all test suites.
   * GET /api/v1/orgs/{orgId}/test-suites
   */
  async listTestSuites(orgId: string): Promise<TestSuitesListResponse> {
    return this.get<TestSuitesListResponse>(this.basePath(orgId));
  }

  /**
   * Get a test suite by ID.
   * GET /api/v1/orgs/{orgId}/test-suites/{suite_id}
   */
  async getTestSuite(orgId: string, id: string): Promise<TestSuite> {
    return this.get<TestSuite>(`${this.basePath(orgId)}/${id}`);
  }

  /**
   * Create a new test suite.
   * POST /api/v1/orgs/{orgId}/test-suites
   */
  async createTestSuite(orgId: string, data: TestSuiteCreateRequest): Promise<TestSuite> {
    return this.post<TestSuite>(this.basePath(orgId), data);
  }

  /**
   * Update a test suite.
   * PUT /api/v1/orgs/{orgId}/test-suites/{suite_id}
   */
  async updateTestSuite(
    orgId: string,
    id: string,
    data: TestSuiteUpdateRequest
  ): Promise<TestSuite> {
    return this.put<TestSuite>(`${this.basePath(orgId)}/${id}`, data);
  }

  /**
   * Delete a test suite.
   * DELETE /api/v1/orgs/{orgId}/test-suites/{suite_id}
   */
  async deleteTestSuite(orgId: string, id: string): Promise<void> {
    return this.delete(`${this.basePath(orgId)}/${id}`);
  }

  /**
   * Get the generation status for a test suite.
   * GET /api/v1/orgs/{orgId}/test-suites/{suite_id}/generation-status
   */
  async getGenerationStatus(orgId: string, id: string): Promise<GenerationStatusResponse> {
    return this.get<GenerationStatusResponse>(`${this.basePath(orgId)}/${id}/generation-status`);
  }

  /**
   * Generate more scenarios for a test suite.
   * Returns 400 if generation is already in progress.
   * POST /api/v1/orgs/{orgId}/test-suites/{suite_id}/generate-scenarios
   */
  async generateMoreScenarios(
    orgId: string,
    id: string,
    request?: GenerateScenariosRequest
  ): Promise<GenerationStatusResponse> {
    return this.post<GenerationStatusResponse>(
      `${this.basePath(orgId)}/${id}/generate-scenarios`,
      request || {}
    );
  }
}
