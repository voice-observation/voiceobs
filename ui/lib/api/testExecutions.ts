/**
 * Test Executions API client (mock data implementation).
 */

import { BaseApiClient, simulateDelay } from "./base";
import type {
  TestExecution,
  TestExecutionsListResponse,
  TestExecutionFilters,
  TestRunResponse,
} from "../types";
import { mockTestExecutions, mockTestScenarios } from "../mockData";

// In-memory storage for test executions
const inMemoryStore = {
  testExecutions: [...mockTestExecutions],
  testScenarios: [...mockTestScenarios],
};

export class TestExecutionsApi extends BaseApiClient {
  /**
   * List all test executions with optional filtering.
   */
  async listTestExecutions(filters?: TestExecutionFilters): Promise<TestExecutionsListResponse> {
    await simulateDelay();
    let executions = inMemoryStore.testExecutions;
    if (filters?.scenario_id) {
      executions = executions.filter((e) => e.scenario_id === filters.scenario_id);
    }
    if (filters?.status) {
      executions = executions.filter((e) => e.status === filters.status);
    }
    if (filters?.suite_id) {
      // Filter by suite_id through scenarios
      const suiteScenarioIds = inMemoryStore.testScenarios
        .filter((s) => s.suite_id === filters.suite_id)
        .map((s) => s.id);
      executions = executions.filter((e) => suiteScenarioIds.includes(e.scenario_id));
    }
    return {
      count: executions.length,
      executions,
    };
  }

  /**
   * Get a test execution by ID.
   */
  async getTestExecution(id: string): Promise<TestExecution> {
    await simulateDelay();
    const execution = inMemoryStore.testExecutions.find((e) => e.id === id);
    if (!execution) {
      throw new Error(`Test execution '${id}' not found`);
    }
    return execution;
  }

  /**
   * Run a test execution for a scenario.
   */
  async runTestExecution(scenarioId: string): Promise<TestRunResponse> {
    await simulateDelay(800);
    // Verify scenario exists
    const scenario = inMemoryStore.testScenarios.find((s) => s.id === scenarioId);
    if (!scenario) {
      throw new Error(`Test scenario '${scenarioId}' not found`);
    }
    // Create a new execution
    const newExecution: TestExecution = {
      id: `execution-${Date.now()}`,
      scenario_id: scenarioId,
      conversation_id: null,
      status: "queued",
      started_at: null,
      completed_at: null,
      result_json: {},
    };
    inMemoryStore.testExecutions.push(newExecution);
    // Simulate execution starting
    setTimeout(() => {
      const exec = inMemoryStore.testExecutions.find((e) => e.id === newExecution.id);
      if (exec) {
        exec.status = "running";
        exec.started_at = new Date().toISOString();
      }
    }, 1000);
    // Simulate completion after estimated duration
    const estimatedDuration = (scenario.timeout || 300) * 1000;
    setTimeout(() => {
      const exec = inMemoryStore.testExecutions.find((e) => e.id === newExecution.id);
      if (exec) {
        exec.status = "completed";
        exec.completed_at = new Date().toISOString();
        exec.conversation_id = `conv-${Date.now()}`;
        exec.result_json = {
          passed: Math.random() > 0.2, // 80% pass rate
          score: 0.7 + Math.random() * 0.3,
          duration_ms: estimatedDuration,
          turns_completed: Math.floor((scenario.max_turns || 10) * 0.8),
        };
      }
    }, estimatedDuration);
    return {
      execution_id: newExecution.id,
      status: "queued",
      scenarios_count: 1,
      estimated_duration: scenario.timeout || 300,
    };
  }
}
