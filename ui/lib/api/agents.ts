/**
 * Agents API client.
 */

import { BaseApiClient } from "./base";
import type {
  Agent,
  AgentCreateRequest,
  AgentUpdateRequest,
  AgentsListResponse,
} from "../types";

export class AgentsApi extends BaseApiClient {
  /**
   * List all agents with optional filtering.
   */
  async listAgents(
    status?: "active" | "inactive" | "archived" | null,
    limit?: number | null,
    offset?: number | null
  ): Promise<AgentsListResponse> {
    const params = new URLSearchParams();
    if (status !== undefined && status !== null) {
      params.append("status", status);
    }
    if (limit !== undefined && limit !== null) {
      params.append("limit", String(limit));
    }
    if (offset !== undefined && offset !== null) {
      params.append("offset", String(offset));
    }
    const query = params.toString();
    return this.get<AgentsListResponse>(`/api/v1/agents${query ? `?${query}` : ""}`);
  }

  /**
   * Get an agent by ID.
   */
  async getAgent(id: string): Promise<Agent> {
    return this.get<Agent>(`/api/v1/agents/${id}`);
  }

  /**
   * Create a new agent.
   */
  async createAgent(data: AgentCreateRequest): Promise<Agent> {
    return this.post<Agent>("/api/v1/agents", data);
  }

  /**
   * Update an existing agent.
   */
  async updateAgent(id: string, data: AgentUpdateRequest): Promise<Agent> {
    return this.put<Agent>(`/api/v1/agents/${id}`, data);
  }

  /**
   * Delete an agent.
   * @param id - Agent ID
   * @param soft - If true, soft delete (set status=archived). If false, hard delete.
   */
  async deleteAgent(id: string, soft: boolean = true): Promise<void> {
    const params = new URLSearchParams();
    params.append("soft", String(soft));
    await this.delete(`/api/v1/agents/${id}?${params.toString()}`);
  }

  /**
   * Enable or disable an agent.
   * @param id - Agent ID
   * @param isActive - Whether the agent should be active
   */
  async setAgentActive(id: string, isActive: boolean): Promise<Agent> {
    const status = isActive ? "active" : "inactive";
    return this.patch<Agent>(`/api/v1/agents/${id}/status`, { status });
  }
}
