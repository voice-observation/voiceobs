/**
 * Agents API client.
 */

import { BaseApiClient } from "./base";
import type {
  Agent,
  AgentListItem,
  AgentCreateRequest,
  AgentUpdateRequest,
  AgentsListResponse,
  ConnectionStatus,
  VerificationStatusResponse,
} from "../types";

// Backend response types (with 'goal' field)
interface BackendAgent {
  id: string;
  name: string;
  goal: string;
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
}

interface BackendAgentListItem {
  id: string;
  name: string;
  agent_type: string;
  phone_number: string | null;
  goal: string;
  connection_status: ConnectionStatus;
  is_active: boolean;
  created_at: string | null;
}

interface BackendAgentsListResponse {
  count: number;
  agents: BackendAgentListItem[];
}

export class AgentsApi extends BaseApiClient {
  /**
   * Transform backend agent to frontend agent (goal -> description).
   */
  private fromBackend(agent: BackendAgent): Agent {
    const { goal, ...rest } = agent;
    return { ...rest, description: goal };
  }

  /**
   * Transform backend list item to frontend list item (goal -> description).
   */
  private fromBackendListItem(agent: BackendAgentListItem): AgentListItem {
    const { goal, ...rest } = agent;
    return { ...rest, description: goal };
  }

  /**
   * Transform frontend create/update request to backend (description -> goal).
   */
  private toBackend(data: AgentCreateRequest | AgentUpdateRequest): Record<string, unknown> {
    const { description, ...rest } = data;
    const result: Record<string, unknown> = { ...rest };
    if (description !== undefined) {
      result.goal = description;
    }
    return result;
  }

  /**
   * List all agents with optional filtering.
   */
  async listAgents(
    connectionStatus?: ConnectionStatus | null,
    isActive?: boolean | null,
    limit?: number | null,
    offset?: number | null
  ): Promise<AgentsListResponse> {
    const params = new URLSearchParams();
    if (connectionStatus !== undefined && connectionStatus !== null) {
      params.append("connection_status", connectionStatus);
    }
    if (isActive !== undefined && isActive !== null) {
      params.append("is_active", String(isActive));
    }
    if (limit !== undefined && limit !== null) {
      params.append("limit", String(limit));
    }
    if (offset !== undefined && offset !== null) {
      params.append("offset", String(offset));
    }
    const query = params.toString();
    const response = await this.get<BackendAgentsListResponse>(
      `/api/v1/agents${query ? `?${query}` : ""}`
    );
    return {
      count: response.count,
      agents: response.agents.map((a) => this.fromBackendListItem(a)),
    };
  }

  /**
   * Get an agent by ID.
   */
  async getAgent(id: string): Promise<Agent> {
    const response = await this.get<BackendAgent>(`/api/v1/agents/${id}`);
    return this.fromBackend(response);
  }

  /**
   * Create a new agent.
   */
  async createAgent(data: AgentCreateRequest): Promise<Agent> {
    const backendData = {
      ...this.toBackend(data),
      agent_type: "phone", // Hardcode for now
    };
    const response = await this.post<BackendAgent>("/api/v1/agents", backendData);
    return this.fromBackend(response);
  }

  /**
   * Update an existing agent.
   */
  async updateAgent(id: string, data: AgentUpdateRequest): Promise<Agent> {
    const backendData = this.toBackend(data);
    const response = await this.put<BackendAgent>(`/api/v1/agents/${id}`, backendData);
    return this.fromBackend(response);
  }

  /**
   * Delete an agent.
   * @param id - Agent ID
   * @param soft - If true, soft delete. If false, hard delete.
   */
  async deleteAgent(id: string, soft: boolean = true): Promise<void> {
    const params = new URLSearchParams();
    params.append("soft", String(soft));
    await this.delete(`/api/v1/agents/${id}?${params.toString()}`);
  }

  /**
   * Trigger agent verification.
   * @param id - Agent ID
   * @param force - Force re-verification even if already verified
   */
  async verifyAgent(id: string, force: boolean = false): Promise<Agent> {
    const response = await this.post<BackendAgent>(`/api/v1/agents/${id}/verify`, { force });
    return this.fromBackend(response);
  }

  /**
   * Get verification status for an agent.
   */
  async getVerificationStatus(id: string): Promise<VerificationStatusResponse> {
    // Backend returns different field names, so we need to map them
    const response = await this.get<{
      agent_id: string;
      status: ConnectionStatus;
      attempts: number;
      reasoning: string | null;
      transcript: Array<{ role: string; content: string }> | null;
      last_verification_at: string | null;
      error: string | null;
    }>(`/api/v1/agents/${id}/verification-status`);

    return {
      connection_status: response.status,
      verification_attempts: response.attempts,
      last_verification_at: response.last_verification_at,
      verification_error: response.error,
      verification_reasoning: response.reasoning,
    };
  }
}
