/**
 * TypeScript types for voiceobs API responses.
 * These types match the backend Pydantic models.
 */

// Test Suite Types
export interface TestSuite {
  id: string;
  name: string;
  description: string | null;
  status: "pending" | "running" | "completed" | "failed";
  created_at: string | null;
}

export interface TestSuiteCreateRequest {
  name: string;
  description?: string | null;
}

export interface TestSuiteUpdateRequest {
  name?: string | null;
  description?: string | null;
  status?: string | null;
}

export interface TestSuitesListResponse {
  count: number;
  suites: TestSuite[];
}

// Test Scenario Types
export interface TestScenario {
  id: string;
  suite_id: string;
  name: string;
  goal: string;
  persona_json: Record<string, unknown>;
  max_turns: number | null;
  timeout: number | null;
}

export interface TestScenarioCreateRequest {
  suite_id: string;
  name: string;
  goal: string;
  persona_json?: Record<string, unknown>;
  max_turns?: number | null;
  timeout?: number | null;
}

export interface TestScenarioUpdateRequest {
  name?: string | null;
  goal?: string | null;
  persona_json?: Record<string, unknown> | null;
  max_turns?: number | null;
  timeout?: number | null;
}

export interface TestScenariosListResponse {
  count: number;
  scenarios: TestScenario[];
}

export interface TestScenarioFilters {
  suite_id?: string;
}

// Test Execution Types
export interface TestExecution {
  id: string;
  scenario_id: string;
  conversation_id: string | null;
  status: "queued" | "running" | "completed" | "failed";
  started_at: string | null;
  completed_at: string | null;
  result_json: Record<string, unknown>;
}

export interface TestExecutionsListResponse {
  count: number;
  executions: TestExecution[];
}

export interface TestExecutionFilters {
  suite_id?: string;
  scenario_id?: string;
  status?: string;
}

export interface TestRunRequest {
  suite_id?: string | null;
  scenarios?: string[] | null;
  max_workers?: number;
}

export interface TestRunResponse {
  execution_id: string;
  status: string;
  scenarios_count: number;
  estimated_duration: number | null;
}

export interface TestSummaryResponse {
  total: number;
  passed: number;
  failed: number;
  pass_rate: number | null;
  avg_duration_ms: number | null;
  avg_latency_ms: number | null;
}

// Pipeline Types
export interface Pipeline {
  id: string;
  name: string;
  description: string | null;
  config: Record<string, unknown>;
  status: "active" | "inactive" | "archived";
  created_at: string | null;
  updated_at: string | null;
}

export interface PipelineCreateRequest {
  name: string;
  description?: string | null;
  config?: Record<string, unknown>;
  status?: "active" | "inactive";
}

export interface PipelineUpdateRequest {
  name?: string | null;
  description?: string | null;
  config?: Record<string, unknown> | null;
  status?: "active" | "inactive" | "archived" | null;
}

export interface PipelinesListResponse {
  count: number;
  pipelines: Pipeline[];
}

// Persona Types
// PersonaListItem - used in list responses (simplified model)
export interface PersonaListItem {
  id: string;
  name: string;
  description: string | null;
  aggression: number; // 0-1
  patience: number; // 0-1
  verbosity: number; // 0-1
  traits: string[];
  preview_audio_url: string | null;
  preview_audio_text: string | null;
  is_active: boolean;
}

// PersonaResponse - full persona model with all fields (UI-facing, excludes backend config)
export interface Persona {
  id: string;
  name: string;
  description: string | null;
  aggression: number; // 0-1
  patience: number; // 0-1
  verbosity: number; // 0-1
  traits: string[];
  preview_audio_url: string | null;
  preview_audio_text: string | null;
  metadata: Record<string, unknown>;
  created_at: string | null;
  updated_at: string | null;
  created_by: string | null;
  is_active: boolean;
}

export interface PersonaCreateRequest {
  name: string;
  description?: string | null;
  aggression?: number; // 0-1, optional
  patience?: number; // 0-1, optional
  verbosity?: number; // 0-1, optional
  traits?: string[];
  metadata?: Record<string, unknown>;
  created_by?: string | null;
  tts_provider?: string;
  tts_config?: Record<string, unknown>;
}

export interface PersonaUpdateRequest {
  name?: string | null;
  description?: string | null;
  aggression?: number | null; // 0-1
  patience?: number | null; // 0-1
  verbosity?: number | null; // 0-1
  traits?: string[] | null;
  metadata?: Record<string, unknown> | null;
}

export interface PersonasListResponse {
  count: number;
  personas: PersonaListItem[];
}

export interface PersonaAudioPreviewResponse {
  audio_url: string;
  text: string;
  format: string;
}

// Report Types
export interface Report {
  id: string;
  name: string;
  type: "summary" | "detailed" | "comparison" | "trend";
  format: "json" | "pdf" | "csv" | "html";
  status: "pending" | "generating" | "completed" | "failed";
  config: Record<string, unknown>;
  generated_at: string | null;
  download_url: string | null;
  created_at: string | null;
}

export interface ReportGenerateRequest {
  name: string;
  type: "summary" | "detailed" | "comparison" | "trend";
  format?: "json" | "pdf" | "csv" | "html";
  config?: Record<string, unknown>;
  filters?: {
    suite_id?: string;
    scenario_id?: string;
    date_from?: string;
    date_to?: string;
  };
}

export interface ReportGenerateResponse {
  report_id: string;
  status: string;
  estimated_completion_time: string | null;
}

export interface ScheduledReport {
  id: string;
  name: string;
  report_type: "summary" | "detailed" | "comparison" | "trend";
  format: "json" | "pdf" | "csv" | "html";
  schedule: string; // Cron expression
  config: Record<string, unknown>;
  is_active: boolean;
  last_run: string | null;
  next_run: string | null;
  created_at: string | null;
}

export interface ScheduledReportCreateRequest {
  name: string;
  report_type: "summary" | "detailed" | "comparison" | "trend";
  format?: "json" | "pdf" | "csv" | "html";
  schedule: string; // Cron expression
  config?: Record<string, unknown>;
  is_active?: boolean;
}

export interface ScheduledReportsListResponse {
  count: number;
  schedules: ScheduledReport[];
}

export interface ReportHistoryItem {
  id: string;
  report_id: string;
  name: string;
  status: "pending" | "generating" | "completed" | "failed";
  generated_at: string | null;
  download_url: string | null;
}

export interface ReportHistoryResponse {
  count: number;
  reports: ReportHistoryItem[];
}

export interface ReportHistoryFilters {
  date_from?: string;
  date_to?: string;
  status?: string;
  type?: string;
}

// Agent Types
export interface Agent {
  id: string;
  name: string;
  description: string | null;
  phone_number: string | null;
  status: "active" | "inactive" | "archived";
  config: Record<string, unknown>;
  created_at: string | null;
  updated_at: string | null;
  // Optional metrics fields
  calls?: number;
  success_rate?: number;
  latency?: number;
}

export interface AgentListItem {
  id: string;
  name: string;
  description: string | null;
  phone_number: string | null;
  status: "active" | "inactive" | "archived";
  created_at: string | null;
  updated_at: string | null;
  // Optional metrics fields
  calls?: number;
  success_rate?: number;
  latency?: number;
}

export interface AgentCreateRequest {
  name: string;
  description?: string | null;
  phone_number?: string | null;
  config?: Record<string, unknown>;
  status?: "active" | "inactive";
}

export interface AgentUpdateRequest {
  name?: string | null;
  description?: string | null;
  phone_number?: string | null;
  config?: Record<string, unknown> | null;
  status?: "active" | "inactive" | "archived" | null;
}

export interface AgentsListResponse {
  count: number;
  agents: AgentListItem[];
}
