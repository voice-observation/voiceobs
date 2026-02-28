/**
 * Test Executions API client.
 */

import { BaseApiClient } from "./base";
import type { TestExecution, TestExecutionsListResponse, TestExecutionFilters } from "../types";

export class TestExecutionsApi extends BaseApiClient {
  async listTestExecutions(
    orgId: string,
    filters?: TestExecutionFilters
  ): Promise<TestExecutionsListResponse> {
    const params = new URLSearchParams();
    if (filters?.scenario_id) params.set("scenario_id", filters.scenario_id);
    if (filters?.status) params.set("status", filters.status);
    if (filters?.suite_id) params.set("suite_id", filters.suite_id);
    const query = params.toString() ? `?${params.toString()}` : "";
    return this.get<TestExecutionsListResponse>(`/api/v1/orgs/${orgId}/executions${query}`);
  }

  async getTestExecution(orgId: string, id: string): Promise<TestExecution> {
    return this.get<TestExecution>(`/api/v1/orgs/${orgId}/executions/${id}`);
  }
}
