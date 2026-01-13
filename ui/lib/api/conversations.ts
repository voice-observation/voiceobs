/**
 * Conversations API client.
 */

import { BaseApiClient } from "./base";

// Re-export conversation-related types from main types file
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

export class ConversationsApi extends BaseApiClient {
  /**
   * List all conversations.
   */
  async listConversations(): Promise<ConversationsListResponse> {
    return this.get<ConversationsListResponse>("/conversations");
  }

  /**
   * Get a conversation by ID.
   */
  async getConversation(conversationId: string): Promise<ConversationDetail> {
    return this.get<ConversationDetail>(`/conversations/${conversationId}`);
  }

  /**
   * List failures with optional filtering.
   */
  async listFailures(severity?: string, type?: string): Promise<FailuresListResponse> {
    const params = new URLSearchParams();
    if (severity) params.append("severity", severity);
    if (type) params.append("type", type);
    const query = params.toString();
    return this.get<FailuresListResponse>(`/failures${query ? `?${query}` : ""}`);
  }

  /**
   * Analyze all conversations.
   */
  async analyzeAll(): Promise<AnalysisResponse> {
    return this.get<AnalysisResponse>("/analyze");
  }

  /**
   * Analyze a specific conversation.
   */
  async analyzeConversation(conversationId: string): Promise<AnalysisResponse> {
    return this.get<AnalysisResponse>(`/analyze/${conversationId}`);
  }
}
