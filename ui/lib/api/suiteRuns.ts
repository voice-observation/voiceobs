/**
 * Suite Runs API client.
 * Integrates with backend /api/v1/orgs/{orgId}/suite-runs endpoints.
 */

import { BaseApiClient } from "./base";
import type { SuiteRun, SuiteRunTriggerResponse } from "../types";

export class SuiteRunsApi extends BaseApiClient {
  /**
   * Run all scenarios in a test suite.
   * POST /api/v1/orgs/{orgId}/test-suites/{suiteId}/run
   */
  async runSuite(orgId: string, suiteId: string): Promise<SuiteRunTriggerResponse> {
    return this.post<SuiteRunTriggerResponse>(
      `/api/v1/orgs/${orgId}/test-suites/${suiteId}/run`,
      {}
    );
  }

  /**
   * Run a single test scenario.
   * POST /api/v1/orgs/{orgId}/test-scenarios/{scenarioId}/run
   */
  async runScenario(orgId: string, scenarioId: string): Promise<SuiteRunTriggerResponse> {
    return this.post<SuiteRunTriggerResponse>(
      `/api/v1/orgs/${orgId}/test-scenarios/${scenarioId}/run`,
      {}
    );
  }

  /**
   * Get suite run status with all execution details.
   * GET /api/v1/orgs/{orgId}/suite-runs/{runId}
   */
  async getSuiteRun(orgId: string, runId: string): Promise<SuiteRun> {
    return this.get<SuiteRun>(`/api/v1/orgs/${orgId}/suite-runs/${runId}`);
  }

  /**
   * Cancel a suite run.
   * POST /api/v1/orgs/{orgId}/suite-runs/{runId}/cancel
   */
  async cancelSuiteRun(orgId: string, runId: string): Promise<SuiteRun> {
    return this.post<SuiteRun>(`/api/v1/orgs/${orgId}/suite-runs/${runId}/cancel`, {});
  }

  /**
   * Get pre-signed audio URL for an execution.
   * GET /api/v1/orgs/{orgId}/executions/{executionId}/audio
   */
  async getExecutionAudioUrl(orgId: string, executionId: string): Promise<{ url: string }> {
    return this.get<{ url: string }>(`/api/v1/orgs/${orgId}/executions/${executionId}/audio`);
  }
}
