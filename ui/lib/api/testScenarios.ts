/**
 * Test Scenarios API client (mock data implementation).
 */

import { BaseApiClient, simulateDelay } from "./base";
import type {
  TestScenario,
  TestScenarioCreateRequest,
  TestScenarioUpdateRequest,
  TestScenariosListResponse,
  TestScenarioFilters,
} from "../types";
import { mockTestScenarios, mockTestSuites } from "../mockData";

// In-memory storage for test scenarios
const inMemoryStore = {
  testScenarios: [...mockTestScenarios],
  testSuites: [...mockTestSuites],
};

export class TestScenariosApi extends BaseApiClient {
  /**
   * List all test scenarios with optional filtering.
   */
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

  /**
   * Get a test scenario by ID.
   */
  async getTestScenario(id: string): Promise<TestScenario> {
    await simulateDelay();
    const scenario = inMemoryStore.testScenarios.find((s) => s.id === id);
    if (!scenario) {
      throw new Error(`Test scenario '${id}' not found`);
    }
    return scenario;
  }

  /**
   * Create a new test scenario.
   */
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

  /**
   * Update a test scenario.
   */
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

  /**
   * Delete a test scenario.
   */
  async deleteTestScenario(id: string): Promise<void> {
    await simulateDelay(300);
    const index = inMemoryStore.testScenarios.findIndex((s) => s.id === id);
    if (index === -1) {
      throw new Error(`Test scenario '${id}' not found`);
    }
    inMemoryStore.testScenarios.splice(index, 1);
  }
}
