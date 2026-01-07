/**
 * Type-safe API client for voiceobs server.
 *
 * In development, requests are proxied through Next.js to avoid CORS issues.
 * The proxy is configured in next.config.js to forward /api/* to the voiceobs server.
 *
 * Currently uses mock data stubs for test suites, scenarios, executions, pipelines, personas, and reports.
 */

import type {
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
  PersonaCreateRequest,
  PersonaUpdateRequest,
  PersonasListResponse,
  Report,
  ReportGenerateRequest,
  ReportGenerateResponse,
  ScheduledReport,
  ScheduledReportCreateRequest,
  ScheduledReportsListResponse,
  ReportHistoryResponse,
  ReportHistoryFilters,
} from "./types";

import {
  mockTestSuites,
  mockTestScenarios,
  mockTestExecutions,
  mockPipelines,
  mockPersonas,
  mockReports,
  mockScheduledReports,
  mockReportHistory,
} from "./mockData";

// Get API URL - use proxy on client-side, direct URL on server-side
const getApiBaseUrl = (): string => {
  // Client-side: use Next.js proxy
  if (typeof window !== "undefined") {
    return "/api";
  }
  // Server-side: use direct URL
  // Next.js provides process.env - using type assertion for server-side only
  // @ts-expect-error - process.env is available in Next.js server-side context
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8765";
};

// Simulate network delay (optional, for realism)
const simulateDelay = (ms: number = 300): Promise<void> => {
  return new Promise((resolve) => setTimeout(resolve, ms));
};

// In-memory storage for created/updated entities
const inMemoryStore = {
  testSuites: [...mockTestSuites],
  testScenarios: [...mockTestScenarios],
  testExecutions: [...mockTestExecutions],
  pipelines: [...mockPipelines],
  personas: [...mockPersonas],
  reports: [...mockReports],
  scheduledReports: [...mockScheduledReports],
  reportHistory: [...mockReportHistory],
};

export interface ApiError {
  error: string;
  message: string;
  detail?: string;
}

export interface ConversationSummary {
  id: string;
  turn_count: number;
  span_count: number;
  has_failures: boolean;
}

export interface ConversationsListResponse {
  count: number;
  conversations: ConversationSummary[];
}

export interface TurnResponse {
  id: string;
  actor: string;
  turn_index: number | null;
  duration_ms: number | null;
  transcript: string | null;
  attributes: Record<string, unknown>;
}

export interface StageMetricsResponse {
  stage_type: string;
  count: number;
  mean_ms: number | null;
  p50_ms: number | null;
  p95_ms: number | null;
  p99_ms: number | null;
}

export interface TurnMetricsResponse {
  silence_samples: number;
  silence_mean_ms: number | null;
  silence_p95_ms: number | null;
  total_agent_turns: number;
  interruptions: number;
  interruption_rate: number | null;
}

export interface EvalMetricsResponse {
  total_evals: number;
  intent_correct_count: number;
  intent_incorrect_count: number;
  intent_correct_rate: number | null;
  intent_failure_rate: number | null;
  avg_relevance_score: number | null;
  min_relevance_score: number | null;
  max_relevance_score: number | null;
}

export interface AnalysisSummary {
  total_spans: number;
  total_conversations: number;
  total_turns: number;
}

export interface AnalysisResponse {
  summary: AnalysisSummary;
  stages: {
    asr: StageMetricsResponse;
    llm: StageMetricsResponse;
    tts: StageMetricsResponse;
  };
  turns: TurnMetricsResponse;
  eval: EvalMetricsResponse;
}

export interface ConversationDetail {
  id: string;
  turns: TurnResponse[];
  span_count: number;
  analysis: AnalysisResponse | null;
}

export interface FailureResponse {
  id: string;
  type: string;
  severity: string;
  message: string;
  conversation_id: string | null;
  turn_id: string | null;
  turn_index: number | null;
  signal_name: string | null;
  signal_value: number | null;
  threshold: number | null;
}

export interface FailuresListResponse {
  count: number;
  failures: FailureResponse[];
  by_severity: Record<string, number>;
  by_type: Record<string, number>;
}

class ApiClient {
  private maxRetries: number = 3;
  private retryDelay: number = 1000;

  private getBaseUrl(): string {
    return getApiBaseUrl();
  }

  private async fetchWithRetry(
    endpoint: string,
    options: RequestInit = {},
    retries: number = this.maxRetries
  ): Promise<Response> {
    const url = `${this.getBaseUrl()}${endpoint}`;

    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          "Content-Type": "application/json",
          ...options.headers,
        },
      });

      if (!response.ok) {
        if (response.status >= 500 && retries > 0) {
          // Retry on server errors
          await new Promise((resolve) => setTimeout(resolve, this.retryDelay));
          return this.fetchWithRetry(endpoint, options, retries - 1);
        }

        let error: ApiError;
        try {
          error = await response.json();
        } catch {
          error = {
            error: "unknown",
            message: `HTTP ${response.status}: ${response.statusText}`,
          };
        }
        throw new Error(error.message || `API request failed: ${response.statusText}`);
      }

      return response;
    } catch (error) {
      if (retries > 0 && error instanceof TypeError) {
        // Network error, retry
        await new Promise((resolve) => setTimeout(resolve, this.retryDelay));
        return this.fetchWithRetry(endpoint, options, retries - 1);
      }
      throw error;
    }
  }

  private async get<T>(endpoint: string): Promise<T> {
    const response = await this.fetchWithRetry(endpoint, { method: "GET" });
    return response.json();
  }

  // Conversations API
  async listConversations(): Promise<ConversationsListResponse> {
    return this.get<ConversationsListResponse>("/conversations");
  }

  async getConversation(conversationId: string): Promise<ConversationDetail> {
    return this.get<ConversationDetail>(`/conversations/${conversationId}`);
  }

  // Failures API
  async listFailures(severity?: string, type?: string): Promise<FailuresListResponse> {
    const params = new URLSearchParams();
    if (severity) params.append("severity", severity);
    if (type) params.append("type", type);
    const query = params.toString();
    return this.get<FailuresListResponse>(`/failures${query ? `?${query}` : ""}`);
  }

  // Analysis API
  async analyzeAll(): Promise<AnalysisResponse> {
    return this.get<AnalysisResponse>("/analyze");
  }

  async analyzeConversation(conversationId: string): Promise<AnalysisResponse> {
    return this.get<AnalysisResponse>(`/analyze/${conversationId}`);
  }

  // Health check
  async healthCheck(): Promise<{ status: string; version: string; timestamp: string }> {
    return this.get<{ status: string; version: string; timestamp: string }>("/health");
  }

  // Test Suites API (stubs with mock data)
  async listTestSuites(): Promise<TestSuitesListResponse> {
    await simulateDelay();
    return {
      count: inMemoryStore.testSuites.length,
      suites: inMemoryStore.testSuites,
    };
  }

  async getTestSuite(id: string): Promise<TestSuite> {
    await simulateDelay();
    const suite = inMemoryStore.testSuites.find((s) => s.id === id);
    if (!suite) {
      throw new Error(`Test suite '${id}' not found`);
    }
    return suite;
  }

  async createTestSuite(data: TestSuiteCreateRequest): Promise<TestSuite> {
    await simulateDelay(500);
    const newSuite: TestSuite = {
      id: `suite-${Date.now()}`,
      name: data.name,
      description: data.description || null,
      status: "pending",
      created_at: new Date().toISOString(),
    };
    inMemoryStore.testSuites.push(newSuite);
    return newSuite;
  }

  async updateTestSuite(id: string, data: TestSuiteUpdateRequest): Promise<TestSuite> {
    await simulateDelay(400);
    const index = inMemoryStore.testSuites.findIndex((s) => s.id === id);
    if (index === -1) {
      throw new Error(`Test suite '${id}' not found`);
    }
    const suite = inMemoryStore.testSuites[index];
    inMemoryStore.testSuites[index] = {
      ...suite,
      ...(data.name !== undefined && data.name !== null && { name: data.name }),
      ...(data.description !== undefined && { description: data.description }),
      ...(data.status !== undefined && data.status !== null && { status: data.status as TestSuite["status"] }),
    };
    return inMemoryStore.testSuites[index];
  }

  async deleteTestSuite(id: string): Promise<void> {
    await simulateDelay(300);
    const index = inMemoryStore.testSuites.findIndex((s) => s.id === id);
    if (index === -1) {
      throw new Error(`Test suite '${id}' not found`);
    }
    inMemoryStore.testSuites.splice(index, 1);
    // Also delete associated scenarios
    inMemoryStore.testScenarios = inMemoryStore.testScenarios.filter(
      (s) => s.suite_id !== id
    );
  }

  // Test Scenarios API (stubs with mock data)
  async listTestScenarios(filters?: TestScenarioFilters): Promise<TestScenariosListResponse> {
    await simulateDelay();
    let scenarios = inMemoryStore.testScenarios;
    if (filters?.suite_id) {
      scenarios = scenarios.filter((s) => s.suite_id === filters.suite_id);
    }
    return {
      count: scenarios.length,
      scenarios,
    };
  }

  async getTestScenario(id: string): Promise<TestScenario> {
    await simulateDelay();
    const scenario = inMemoryStore.testScenarios.find((s) => s.id === id);
    if (!scenario) {
      throw new Error(`Test scenario '${id}' not found`);
    }
    return scenario;
  }

  async createTestScenario(data: TestScenarioCreateRequest): Promise<TestScenario> {
    await simulateDelay(500);
    // Verify suite exists
    const suite = inMemoryStore.testSuites.find((s) => s.id === data.suite_id);
    if (!suite) {
      throw new Error(`Test suite '${data.suite_id}' not found`);
    }
    const newScenario: TestScenario = {
      id: `scenario-${Date.now()}`,
      suite_id: data.suite_id,
      name: data.name,
      goal: data.goal,
      persona_json: data.persona_json || {},
      max_turns: data.max_turns || null,
      timeout: data.timeout || null,
    };
    inMemoryStore.testScenarios.push(newScenario);
    return newScenario;
  }

  async updateTestScenario(id: string, data: TestScenarioUpdateRequest): Promise<TestScenario> {
    await simulateDelay(400);
    const index = inMemoryStore.testScenarios.findIndex((s) => s.id === id);
    if (index === -1) {
      throw new Error(`Test scenario '${id}' not found`);
    }
    const scenario = inMemoryStore.testScenarios[index];
    inMemoryStore.testScenarios[index] = {
      ...scenario,
      ...(data.name !== undefined && data.name !== null && { name: data.name }),
      ...(data.goal !== undefined && data.goal !== null && { goal: data.goal }),
      ...(data.persona_json !== undefined && { persona_json: data.persona_json || {} }),
      ...(data.max_turns !== undefined && { max_turns: data.max_turns }),
      ...(data.timeout !== undefined && { timeout: data.timeout }),
    };
    return inMemoryStore.testScenarios[index];
  }

  async deleteTestScenario(id: string): Promise<void> {
    await simulateDelay(300);
    const index = inMemoryStore.testScenarios.findIndex((s) => s.id === id);
    if (index === -1) {
      throw new Error(`Test scenario '${id}' not found`);
    }
    inMemoryStore.testScenarios.splice(index, 1);
  }

  // Test Executions API (stubs with mock data)
  async listTestExecutions(filters?: TestExecutionFilters): Promise<TestExecutionsListResponse> {
    await simulateDelay();
    let executions = inMemoryStore.testExecutions;
    if (filters?.scenario_id) {
      executions = executions.filter((e) => e.scenario_id === filters.scenario_id);
    }
    if (filters?.status) {
      executions = executions.filter((e) => e.status === filters.status);
    }
    if (filters?.suite_id) {
      // Filter by suite_id through scenarios
      const suiteScenarioIds = inMemoryStore.testScenarios
        .filter((s) => s.suite_id === filters.suite_id)
        .map((s) => s.id);
      executions = executions.filter((e) => suiteScenarioIds.includes(e.scenario_id));
    }
    return {
      count: executions.length,
      executions,
    };
  }

  async getTestExecution(id: string): Promise<TestExecution> {
    await simulateDelay();
    const execution = inMemoryStore.testExecutions.find((e) => e.id === id);
    if (!execution) {
      throw new Error(`Test execution '${id}' not found`);
    }
    return execution;
  }

  async runTestExecution(scenarioId: string): Promise<TestRunResponse> {
    await simulateDelay(800);
    // Verify scenario exists
    const scenario = inMemoryStore.testScenarios.find((s) => s.id === scenarioId);
    if (!scenario) {
      throw new Error(`Test scenario '${scenarioId}' not found`);
    }
    // Create a new execution
    const newExecution: TestExecution = {
      id: `execution-${Date.now()}`,
      scenario_id: scenarioId,
      conversation_id: null,
      status: "queued",
      started_at: null,
      completed_at: null,
      result_json: {},
    };
    inMemoryStore.testExecutions.push(newExecution);
    // Simulate execution starting
    setTimeout(() => {
      const exec = inMemoryStore.testExecutions.find((e) => e.id === newExecution.id);
      if (exec) {
        exec.status = "running";
        exec.started_at = new Date().toISOString();
      }
    }, 1000);
    // Simulate completion after estimated duration
    const estimatedDuration = (scenario.timeout || 300) * 1000;
    setTimeout(() => {
      const exec = inMemoryStore.testExecutions.find((e) => e.id === newExecution.id);
      if (exec) {
        exec.status = "completed";
        exec.completed_at = new Date().toISOString();
        exec.conversation_id = `conv-${Date.now()}`;
        exec.result_json = {
          passed: Math.random() > 0.2, // 80% pass rate
          score: 0.7 + Math.random() * 0.3,
          duration_ms: estimatedDuration,
          turns_completed: Math.floor((scenario.max_turns || 10) * 0.8),
        };
      }
    }, estimatedDuration);
    return {
      execution_id: newExecution.id,
      status: "queued",
      scenarios_count: 1,
      estimated_duration: scenario.timeout || 300,
    };
  }

  // Pipelines API (stubs with mock data)
  async listPipelines(): Promise<PipelinesListResponse> {
    await simulateDelay();
    return {
      count: inMemoryStore.pipelines.length,
      pipelines: inMemoryStore.pipelines,
    };
  }

  async getPipeline(id: string): Promise<Pipeline> {
    await simulateDelay();
    const pipeline = inMemoryStore.pipelines.find((p) => p.id === id);
    if (!pipeline) {
      throw new Error(`Pipeline '${id}' not found`);
    }
    return pipeline;
  }

  async createPipeline(data: PipelineCreateRequest): Promise<Pipeline> {
    await simulateDelay(500);
    const newPipeline: Pipeline = {
      id: `pipeline-${Date.now()}`,
      name: data.name,
      description: data.description || null,
      config: data.config || {},
      status: data.status || "active",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    inMemoryStore.pipelines.push(newPipeline);
    return newPipeline;
  }

  async updatePipeline(id: string, data: PipelineUpdateRequest): Promise<Pipeline> {
    await simulateDelay(400);
    const index = inMemoryStore.pipelines.findIndex((p) => p.id === id);
    if (index === -1) {
      throw new Error(`Pipeline '${id}' not found`);
    }
    const pipeline = inMemoryStore.pipelines[index];
    inMemoryStore.pipelines[index] = {
      ...pipeline,
      ...(data.name !== undefined && data.name !== null && { name: data.name }),
      ...(data.description !== undefined && { description: data.description }),
      ...(data.config !== undefined && { config: data.config || {} }),
      ...(data.status !== undefined && data.status !== null && { status: data.status as Pipeline["status"] }),
      updated_at: new Date().toISOString(),
    };
    return inMemoryStore.pipelines[index];
  }

  async deletePipeline(id: string): Promise<void> {
    await simulateDelay(300);
    const index = inMemoryStore.pipelines.findIndex((p) => p.id === id);
    if (index === -1) {
      throw new Error(`Pipeline '${id}' not found`);
    }
    inMemoryStore.pipelines.splice(index, 1);
  }

  // Personas API (stubs with mock data)
  async listPersonas(): Promise<PersonasListResponse> {
    await simulateDelay();
    return {
      count: inMemoryStore.personas.length,
      personas: inMemoryStore.personas,
    };
  }

  async getPersona(id: string): Promise<Persona> {
    await simulateDelay();
    const persona = inMemoryStore.personas.find((p) => p.id === id);
    if (!persona) {
      throw new Error(`Persona '${id}' not found`);
    }
    return persona;
  }

  async createPersona(data: PersonaCreateRequest): Promise<Persona> {
    await simulateDelay(500);
    // Validate trait values
    if (data.aggression < 0 || data.aggression > 1) {
      throw new Error("aggression must be between 0 and 1");
    }
    if (data.patience < 0 || data.patience > 1) {
      throw new Error("patience must be between 0 and 1");
    }
    if (data.verbosity < 0 || data.verbosity > 1) {
      throw new Error("verbosity must be between 0 and 1");
    }
    const newPersona: Persona = {
      id: `persona-${Date.now()}`,
      name: data.name,
      description: data.description || null,
      aggression: data.aggression,
      patience: data.patience,
      verbosity: data.verbosity,
      traits: data.traits || [],
      is_predefined: false,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    inMemoryStore.personas.push(newPersona);
    return newPersona;
  }

  async updatePersona(id: string, data: PersonaUpdateRequest): Promise<Persona> {
    await simulateDelay(400);
    const index = inMemoryStore.personas.findIndex((p) => p.id === id);
    if (index === -1) {
      throw new Error(`Persona '${id}' not found`);
    }
    const persona = inMemoryStore.personas[index];
    if (persona.is_predefined) {
      throw new Error("Cannot update predefined persona");
    }
    // Validate trait values if provided
    if (data.aggression !== undefined && data.aggression !== null && (data.aggression < 0 || data.aggression > 1)) {
      throw new Error("aggression must be between 0 and 1");
    }
    if (data.patience !== undefined && data.patience !== null && (data.patience < 0 || data.patience > 1)) {
      throw new Error("patience must be between 0 and 1");
    }
    if (data.verbosity !== undefined && data.verbosity !== null && (data.verbosity < 0 || data.verbosity > 1)) {
      throw new Error("verbosity must be between 0 and 1");
    }
    inMemoryStore.personas[index] = {
      ...persona,
      ...(data.name !== undefined && data.name !== null && { name: data.name }),
      ...(data.description !== undefined && { description: data.description }),
      ...(data.aggression !== undefined && data.aggression !== null && { aggression: data.aggression }),
      ...(data.patience !== undefined && data.patience !== null && { patience: data.patience }),
      ...(data.verbosity !== undefined && data.verbosity !== null && { verbosity: data.verbosity }),
      ...(data.traits !== undefined && { traits: data.traits || [] }),
      updated_at: new Date().toISOString(),
    };
    return inMemoryStore.personas[index];
  }

  async deletePersona(id: string): Promise<void> {
    await simulateDelay(300);
    const index = inMemoryStore.personas.findIndex((p) => p.id === id);
    if (index === -1) {
      throw new Error(`Persona '${id}' not found`);
    }
    const persona = inMemoryStore.personas[index];
    if (persona.is_predefined) {
      throw new Error("Cannot delete predefined persona");
    }
    inMemoryStore.personas.splice(index, 1);
  }

  // Reports API (stubs with mock data)
  async generateReport(config: ReportGenerateRequest): Promise<ReportGenerateResponse> {
    await simulateDelay(600);
    const newReport: Report = {
      id: `report-${Date.now()}`,
      name: config.name,
      type: config.type,
      format: config.format || "json",
      status: "generating",
      config: config.config || {},
      generated_at: null,
      download_url: null,
      created_at: new Date().toISOString(),
    };
    inMemoryStore.reports.push(newReport);
    // Simulate report generation completion
    setTimeout(() => {
      const report = inMemoryStore.reports.find((r) => r.id === newReport.id);
      if (report) {
        report.status = "completed";
        report.generated_at = new Date().toISOString();
        report.download_url = `/api/reports/${report.id}/download`;
      }
      // Add to history
      inMemoryStore.reportHistory.unshift({
        id: `history-${Date.now()}`,
        report_id: newReport.id,
        name: newReport.name,
        status: "completed",
        generated_at: new Date().toISOString(),
        download_url: `/api/reports/${newReport.id}/download`,
      });
    }, 3000);
    return {
      report_id: newReport.id,
      status: "generating",
      estimated_completion_time: new Date(Date.now() + 3000).toISOString(),
    };
  }

  async listScheduledReports(): Promise<ScheduledReportsListResponse> {
    await simulateDelay();
    return {
      count: inMemoryStore.scheduledReports.length,
      schedules: inMemoryStore.scheduledReports,
    };
  }

  async createSchedule(data: ScheduledReportCreateRequest): Promise<ScheduledReport> {
    await simulateDelay(500);
    const newSchedule: ScheduledReport = {
      id: `schedule-${Date.now()}`,
      name: data.name,
      report_type: data.report_type,
      format: data.format || "json",
      schedule: data.schedule,
      config: data.config || {},
      is_active: data.is_active !== undefined ? data.is_active : true,
      last_run: null,
      next_run: null, // Would calculate from cron expression in real implementation
      created_at: new Date().toISOString(),
    };
    inMemoryStore.scheduledReports.push(newSchedule);
    return newSchedule;
  }

  async getReportHistory(filters?: ReportHistoryFilters): Promise<ReportHistoryResponse> {
    await simulateDelay();
    let reports = inMemoryStore.reportHistory;
    if (filters?.status) {
      reports = reports.filter((r) => r.status === filters.status);
    }
    if (filters?.type) {
      // Filter by type through report lookup
      reports = reports.filter((r) => {
        const report = inMemoryStore.reports.find((rep) => rep.id === r.report_id);
        return report?.type === filters.type;
      });
    }
    if (filters?.date_from) {
      const fromDate = new Date(filters.date_from);
      reports = reports.filter((r) => {
        if (!r.generated_at) return false;
        return new Date(r.generated_at) >= fromDate;
      });
    }
    if (filters?.date_to) {
      const toDate = new Date(filters.date_to);
      reports = reports.filter((r) => {
        if (!r.generated_at) return false;
        return new Date(r.generated_at) <= toDate;
      });
    }
    return {
      count: reports.length,
      reports,
    };
  }

  async downloadReport(id: string): Promise<Blob> {
    await simulateDelay(800);
    const report = inMemoryStore.reports.find((r) => r.id === id);
    if (!report) {
      throw new Error(`Report '${id}' not found`);
    }
    if (report.status !== "completed" || !report.download_url) {
      throw new Error(`Report '${id}' is not ready for download`);
    }
    // Simulate file download - return a mock blob
    const mockContent = JSON.stringify({
      report_id: report.id,
      name: report.name,
      type: report.type,
      generated_at: report.generated_at,
      data: "Mock report data...",
    });
    return new Blob([mockContent], { type: "application/json" });
  }
}

export const api = new ApiClient();
