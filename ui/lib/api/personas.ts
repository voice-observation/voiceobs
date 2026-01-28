/**
 * Personas API client.
 */

import { BaseApiClient } from "./base";
import type {
  Persona,
  PersonaCreateRequest,
  PersonaUpdateRequest,
  PersonasListResponse,
  PersonaAudioPreviewResponse,
} from "../types";

export class PersonasApi extends BaseApiClient {
  /**
   * List all personas with optional filtering.
   */
  async listPersonas(
    is_active?: boolean | null,
    limit?: number | null,
    offset?: number | null
  ): Promise<PersonasListResponse> {
    const params = new URLSearchParams();
    if (is_active !== undefined && is_active !== null) {
      params.append("is_active", String(is_active));
    }
    if (limit !== undefined && limit !== null) {
      params.append("limit", String(limit));
    }
    if (offset !== undefined && offset !== null) {
      params.append("offset", String(offset));
    }
    const query = params.toString();
    return this.get<PersonasListResponse>(`/api/v1/personas${query ? `?${query}` : ""}`);
  }

  /**
   * Get a persona by ID.
   */
  async getPersona(id: string): Promise<Persona> {
    return this.get<Persona>(`/api/v1/personas/${id}`);
  }

  /**
   * Create a new persona.
   */
  async createPersona(data: PersonaCreateRequest): Promise<Persona> {
    return this.post<Persona>("/api/v1/personas", data);
  }

  /**
   * Update an existing persona.
   */
  async updatePersona(id: string, data: PersonaUpdateRequest): Promise<Persona> {
    return this.put<Persona>(`/api/v1/personas/${id}`, data);
  }

  /**
   * Delete a persona.
   * @param id - Persona ID
   * @param soft - If true, soft delete (set is_active=false). If false, hard delete.
   */
  async deletePersona(id: string, soft: boolean = true): Promise<void> {
    const params = new URLSearchParams();
    params.append("soft", String(soft));
    await this.delete(`/api/v1/personas/${id}?${params.toString()}`);
  }

  /**
   * Get pregenerated preview audio for a persona.
   */
  async getPersonaPreviewAudio(id: string): Promise<PersonaAudioPreviewResponse> {
    return this.get<PersonaAudioPreviewResponse>(`/api/v1/personas/${id}/preview-audio`);
  }

  /**
   * Generate and store preview audio for a persona.
   */
  async generatePersonaPreviewAudio(id: string): Promise<PersonaAudioPreviewResponse> {
    return this.post<PersonaAudioPreviewResponse>(`/api/v1/personas/${id}/preview-audio`, {});
  }

  /**
   * Enable or disable a persona.
   * @param id - Persona ID
   * @param isActive - Whether the persona should be active
   */
  async setPersonaActive(id: string, isActive: boolean): Promise<Persona> {
    return this.patch<Persona>(`/api/v1/personas/${id}/active`, { is_active: isActive });
  }

  /**
   * Get available TTS provider models.
   */
  async getTTSModels(): Promise<Record<string, Record<string, Record<string, unknown>>>> {
    return this.get<Record<string, Record<string, Record<string, unknown>>>>(
      "/api/v1/personas/tts-models"
    );
  }
}
