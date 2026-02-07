/**
 * TypeScript types for voiceobs API responses.
 * These types match the backend Pydantic models.
 */

// Test Suite Types
export type TestSuiteStatus =
  | "pending"
  | "generating"
  | "ready"
  | "generation_failed"
  | "running"
  | "completed"
  | "failed";

export interface TestSuite {
  id: string;
  name: string;
  description: string | null;
  status: TestSuiteStatus;
  test_scopes: string[];
  thoroughness: number; // 0: Light, 1: Standard, 2: Exhaustive
  edge_cases: string[];
  evaluation_strictness: string; // "strict" | "balanced" | "flexible"
  created_at: string | null;
  agent_id?: string;
  generation_error?: string;
  scenario_count?: number;
}

export interface TestSuiteCreateRequest {
  name: string;
  description?: string | null;
  agent_id: string;
  test_scopes?: string[];
  thoroughness?: number;
  edge_cases?: string[];
  evaluation_strictness?: string;
}

export interface TestSuiteUpdateRequest {
  name?: string | null;
  description?: string | null;
  status?: string | null;
  test_scopes?: string[] | null;
  thoroughness?: number | null;
  edge_cases?: string[] | null;
  evaluation_strictness?: string | null;
}

export interface TestSuitesListResponse {
  count: number;
  suites: TestSuite[];
}

export interface GenerationStatusResponse {
  suite_id: string;
  status: "pending" | "generating" | "ready" | "generation_failed";
  scenario_count: number;
  error?: string;
}

export interface GenerateScenariosRequest {
  prompt?: string;
}

// Test Scenario Types
export type TestScenarioStatus = "ready" | "draft";

export interface TestScenario {
  id: string;
  suite_id: string;
  name: string;
  goal: string;
  persona_id: string;
  max_turns: number | null;
  timeout: number | null;
  intent?: string;
  persona_traits?: string[];
  persona_match_score?: number; // 0.0-1.0
  // New CRUD fields
  caller_behaviors?: string[];
  tags?: string[];
  status: TestScenarioStatus;
  is_manual: boolean; // True for manually created scenarios, False for AI-generated
}

export interface TestScenarioCreateRequest {
  suite_id: string;
  name: string;
  goal: string;
  persona_id: string;
  max_turns?: number | null;
  timeout?: number | null;
  caller_behaviors?: string[];
  tags?: string[];
}

export interface TestScenarioUpdateRequest {
  suite_id?: string | null;
  name?: string | null;
  goal?: string | null;
  persona_id?: string | null;
  max_turns?: number | null;
  timeout?: number | null;
  caller_behaviors?: string[];
  tags?: string[];
}

export interface TestScenariosListResponse {
  count: number;
  scenarios: TestScenario[];
  limit: number;
  offset: number;
}

export interface TestScenarioFilters {
  suite_id?: string;
  persona_id?: string;
  status?: TestScenarioStatus;
  intent?: string;
  tag?: string;
  search?: string;
  limit?: number;
  offset?: number;
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
  preview_audio_status: "generating" | "ready" | "failed" | null;
  is_active: boolean;
  is_default?: boolean;
}

// PersonaResponse - full persona model with all fields
export interface Persona {
  id: string;
  name: string;
  description: string | null;
  aggression: number; // 0-1
  patience: number; // 0-1
  verbosity: number; // 0-1
  traits: string[];
  tts_provider: string;
  tts_config: Record<string, unknown>;
  preview_audio_url: string | null;
  preview_audio_text: string | null;
  preview_audio_status: "generating" | "ready" | "failed" | null;
  preview_audio_error: string | null;
  metadata: Record<string, unknown>;
  created_at: string | null;
  updated_at: string | null;
  created_by: string | null;
  is_active: boolean;
  is_default?: boolean;
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
  tts_provider?: string | null;
  tts_config?: Record<string, unknown> | null;
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

export interface PreviewAudioStatusResponse {
  status: "generating" | "ready" | "failed" | null;
  audio_url: string | null;
  error_message: string | null;
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
export type ConnectionStatus = "pending" | "saved" | "connecting" | "verified" | "failed";

export interface Agent {
  id: string;
  name: string;
  description: string; // Maps to backend 'goal'
  agent_type: string;
  phone_number: string | null;
  connection_status: ConnectionStatus;
  is_active: boolean;
  supported_intents: string[];
  verification_attempts: number;
  last_verification_at: string | null;
  verification_error: string | null;
  verification_reasoning: string | null;
  verification_transcript: Array<{ role: string; content: string }> | null;
  metadata: Record<string, unknown>;
  created_at: string | null;
  updated_at: string | null;
  created_by: string | null;
  context?: string;
}

export interface AgentListItem {
  id: string;
  name: string;
  agent_type: string;
  phone_number: string | null;
  description: string; // Maps to backend 'goal'
  connection_status: ConnectionStatus;
  is_active: boolean;
  created_at: string | null;
}

export interface AgentCreateRequest {
  name: string;
  description: string; // Sent as 'goal' to backend
  phone_number: string;
  supported_intents: string[];
  context?: string;
}

export interface AgentUpdateRequest {
  name?: string;
  description?: string; // Sent as 'goal' to backend
  phone_number?: string;
  supported_intents?: string[];
  is_active?: boolean;
  context?: string;
}

export interface AgentsListResponse {
  count: number;
  agents: AgentListItem[];
}

export interface VerificationStatusResponse {
  connection_status: ConnectionStatus;
  verification_attempts: number;
  last_verification_at: string | null;
  verification_error: string | null;
  verification_reasoning: string | null;
}

// Trait vocabulary types
export interface TraitVocabularyResponse {
  vocabulary: Record<string, string[]>;
}
