/**
 * Type-safe API client for voiceobs server.
 *
 * In development, requests are proxied through Next.js to avoid CORS issues.
 * The proxy is configured in next.config.js to forward /api/* to the voiceobs server.
 */

// Get API URL - use proxy on client-side, direct URL on server-side
const getApiBaseUrl = () => {
  // Client-side: use Next.js proxy
  if (typeof window !== "undefined") {
    return "/api";
  }
  // Server-side: use direct URL
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8765";
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
}

export const api = new ApiClient();
