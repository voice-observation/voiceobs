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
  PreviewAudioStatusResponse,
} from "../types";

export class PersonasApi extends BaseApiClient {
  private basePath(orgId: string): string {
    return `/api/v1/orgs/${orgId}/personas`;
  }

  /**
   * List all personas with optional filtering.
   */
  async listPersonas(
    orgId: string,
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
    return this.get<PersonasListResponse>(`${this.basePath(orgId)}${query ? `?${query}` : ""}`);
  }

  /**
   * Get a persona by ID.
   */
  async getPersona(orgId: string, id: string): Promise<Persona> {
    return this.get<Persona>(`${this.basePath(orgId)}/${id}`);
  }

  /**
   * Create a new persona.
   */
  async createPersona(orgId: string, data: PersonaCreateRequest): Promise<Persona> {
    return this.post<Persona>(this.basePath(orgId), data);
  }

  /**
   * Update an existing persona.
   */
  async updatePersona(orgId: string, id: string, data: PersonaUpdateRequest): Promise<Persona> {
    return this.put<Persona>(`${this.basePath(orgId)}/${id}`, data);
  }

  /**
   * Delete a persona.
   * @param orgId - Organization ID
   * @param id - Persona ID
   * @param soft - If true, soft delete (set is_active=false). If false, hard delete.
   */
  async deletePersona(orgId: string, id: string, soft: boolean = true): Promise<void> {
    const params = new URLSearchParams();
    params.append("soft", String(soft));
    await this.delete(`${this.basePath(orgId)}/${id}?${params.toString()}`);
  }

  /**
   * Get pregenerated preview audio for a persona.
   */
  async getPersonaPreviewAudio(orgId: string, id: string): Promise<PersonaAudioPreviewResponse> {
    return this.get<PersonaAudioPreviewResponse>(`${this.basePath(orgId)}/${id}/preview-audio`);
  }

  /**
   * Start async preview audio generation for a persona.
   * Returns immediately with status "generating".
   */
  async generatePersonaPreviewAudio(
    orgId: string,
    id: string
  ): Promise<PreviewAudioStatusResponse> {
    return this.post<PreviewAudioStatusResponse>(`${this.basePath(orgId)}/${id}/preview-audio`, {});
  }

  /**
   * Get preview audio generation status for a persona.
   */
  async getPreviewAudioStatus(orgId: string, id: string): Promise<PreviewAudioStatusResponse> {
    return this.get<PreviewAudioStatusResponse>(
      `${this.basePath(orgId)}/${id}/preview-audio/status`
    );
  }

  /**
   * Enable or disable a persona.
   * @param orgId - Organization ID
   * @param id - Persona ID
   * @param isActive - Whether the persona should be active
   */
  async setPersonaActive(orgId: string, id: string, isActive: boolean): Promise<Persona> {
    return this.patch<Persona>(`${this.basePath(orgId)}/${id}/active`, { is_active: isActive });
  }

  /**
   * Get available TTS provider models.
   * This is global data not scoped to organizations.
   */
  async getTTSModels(): Promise<Record<string, Record<string, Record<string, unknown>>>> {
    return this.get<Record<string, Record<string, Record<string, unknown>>>>(`/api/v1/tts/models`);
  }

  /**
   * Set a persona as the default fallback.
   * POST /api/v1/orgs/{orgId}/personas/{id}/set-default
   */
  async setDefault(orgId: string, id: string): Promise<Persona> {
    return this.post<Persona>(`${this.basePath(orgId)}/${id}/set-default`, {});
  }
}
