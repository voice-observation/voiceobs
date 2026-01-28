/**
 * Pipelines API client (mock data implementation).
 */

import { BaseApiClient, simulateDelay } from "./base";
import type {
  Pipeline,
  PipelineCreateRequest,
  PipelineUpdateRequest,
  PipelinesListResponse,
} from "../types";
import { mockPipelines } from "../mockData";

// In-memory storage for pipelines
const inMemoryStore = {
  pipelines: [...mockPipelines],
};

export class PipelinesApi extends BaseApiClient {
  /**
   * List all pipelines.
   */
  async listPipelines(): Promise<PipelinesListResponse> {
    await simulateDelay();
    return {
      count: inMemoryStore.pipelines.length,
      pipelines: inMemoryStore.pipelines,
    };
  }

  /**
   * Get a pipeline by ID.
   */
  async getPipeline(id: string): Promise<Pipeline> {
    await simulateDelay();
    const pipeline = inMemoryStore.pipelines.find((p) => p.id === id);
    if (!pipeline) {
      throw new Error(`Pipeline '${id}' not found`);
    }
    return pipeline;
  }

  /**
   * Create a new pipeline.
   */
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

  /**
   * Update a pipeline.
   */
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
      ...(data.status !== undefined &&
        data.status !== null && { status: data.status as Pipeline["status"] }),
      updated_at: new Date().toISOString(),
    };
    return inMemoryStore.pipelines[index];
  }

  /**
   * Delete a pipeline.
   */
  async deletePipeline(id: string): Promise<void> {
    await simulateDelay(300);
    const index = inMemoryStore.pipelines.findIndex((p) => p.id === id);
    if (index === -1) {
      throw new Error(`Pipeline '${id}' not found`);
    }
    inMemoryStore.pipelines.splice(index, 1);
  }
}
