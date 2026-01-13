/**
 * Test Suites API client (mock data implementation).
 */

import { BaseApiClient, simulateDelay } from "./base";
import type {
  TestSuite,
  TestSuiteCreateRequest,
  TestSuiteUpdateRequest,
  TestSuitesListResponse,
} from "../types";
import { mockTestSuites } from "../mockData";

// In-memory storage for test suites
const inMemoryStore = {
  testSuites: [...mockTestSuites],
};

export class TestSuitesApi extends BaseApiClient {
  /**
   * List all test suites.
   */
  async listTestSuites(): Promise<TestSuitesListResponse> {
    await simulateDelay();
    return {
      count: inMemoryStore.testSuites.length,
      suites: inMemoryStore.testSuites,
    };
  }

  /**
   * Get a test suite by ID.
   */
  async getTestSuite(id: string): Promise<TestSuite> {
    await simulateDelay();
    const suite = inMemoryStore.testSuites.find((s) => s.id === id);
    if (!suite) {
      throw new Error(`Test suite '${id}' not found`);
    }
    return suite;
  }

  /**
   * Create a new test suite.
   */
  async createTestSuite(data: TestSuiteCreateRequest): Promise<TestSuite> {
    await simulateDelay(500);
    const newSuite: TestSuite = {
      id: `suite-${Date.now()}`,
      name: data.name,
      description: data.description || null,
      status: "pending",
      created_at: new Date().toISOString(),
    };
    inMemoryStore.testSuites.push(newSuite);
    return newSuite;
  }

  /**
   * Update a test suite.
   */
  async updateTestSuite(id: string, data: TestSuiteUpdateRequest): Promise<TestSuite> {
    await simulateDelay(400);
    const index = inMemoryStore.testSuites.findIndex((s) => s.id === id);
    if (index === -1) {
      throw new Error(`Test suite '${id}' not found`);
    }
    const suite = inMemoryStore.testSuites[index];
    inMemoryStore.testSuites[index] = {
      ...suite,
      ...(data.name !== undefined && data.name !== null && { name: data.name }),
      ...(data.description !== undefined && { description: data.description }),
      ...(data.status !== undefined && data.status !== null && { status: data.status as TestSuite["status"] }),
    };
    return inMemoryStore.testSuites[index];
  }

  /**
   * Delete a test suite.
   */
  async deleteTestSuite(id: string): Promise<void> {
    await simulateDelay(300);
    const index = inMemoryStore.testSuites.findIndex((s) => s.id === id);
    if (index === -1) {
      throw new Error(`Test suite '${id}' not found`);
    }
    inMemoryStore.testSuites.splice(index, 1);
  }
}
