/**
 * Main API client that aggregates all entity-specific API clients.
 *
 * Usage:
 *   import { api } from '@/lib/api';
 *   const personas = await api.personas.listPersonas();
 *   const conversations = await api.conversations.listConversations();
 */

import { BaseApiClient } from "./base";
import { PersonasApi } from "./personas";
import { ConversationsApi } from "./conversations";
import { TestSuitesApi } from "./testSuites";
import { TestScenariosApi } from "./testScenarios";
import { TestExecutionsApi } from "./testExecutions";
import { PipelinesApi } from "./pipelines";
import { ReportsApi } from "./reports";

/**
 * Main API client class that provides access to all entity-specific APIs.
 */
class ApiClient extends BaseApiClient {
  public readonly personas: PersonasApi;
  public readonly conversations: ConversationsApi;
  public readonly testSuites: TestSuitesApi;
  public readonly testScenarios: TestScenariosApi;
  public readonly testExecutions: TestExecutionsApi;
  public readonly pipelines: PipelinesApi;
  public readonly reports: ReportsApi;

  constructor() {
    super();
    this.personas = new PersonasApi();
    this.conversations = new ConversationsApi();
    this.testSuites = new TestSuitesApi();
    this.testScenarios = new TestScenariosApi();
    this.testExecutions = new TestExecutionsApi();
    this.pipelines = new PipelinesApi();
    this.reports = new ReportsApi();
  }

  /**
   * Health check endpoint.
   */
  async healthCheck(): Promise<{ status: string; version: string; timestamp: string }> {
    return this.get<{ status: string; version: string; timestamp: string }>("/health");
  }
}

// Export singleton instance
export const api = new ApiClient();

// Export individual API classes for direct instantiation if needed
export { PersonasApi } from "./personas";
export { ConversationsApi } from "./conversations";
export { TestSuitesApi } from "./testSuites";
export { TestScenariosApi } from "./testScenarios";
export { TestExecutionsApi } from "./testExecutions";
export { PipelinesApi } from "./pipelines";
export { ReportsApi } from "./reports";

// Export types
export type { ApiError } from "./base";
export type * from "./conversations";

// Re-export all types from types.ts for convenience
export type {
  TestSuite,
  TestSuiteCreateRequest,
  TestSuiteUpdateRequest,
  TestSuitesListResponse,
  TestScenario,
  TestScenarioCreateRequest,
  TestScenarioUpdateRequest,
  TestScenariosListResponse,
  TestScenarioFilters,
  TestExecution,
  TestExecutionsListResponse,
  TestExecutionFilters,
  TestRunRequest,
  TestRunResponse,
  TestSummaryResponse,
  Pipeline,
  PipelineCreateRequest,
  PipelineUpdateRequest,
  PipelinesListResponse,
  Persona,
  PersonaListItem,
  PersonaCreateRequest,
  PersonaUpdateRequest,
  PersonasListResponse,
  PersonaAudioPreviewResponse,
  Report,
  ReportGenerateRequest,
  ReportGenerateResponse,
  ScheduledReport,
  ScheduledReportCreateRequest,
  ScheduledReportsListResponse,
  ReportHistoryResponse,
  ReportHistoryFilters,
} from "../types";
