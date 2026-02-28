import { SuiteRunsApi } from "../suiteRuns";

// Mock the base fetch
jest.mock("../base", () => ({
  BaseApiClient: class {
    async get(url: string) {
      return { url };
    }
    async post(url: string, body?: unknown) {
      return { url, body };
    }
  },
}));

describe("SuiteRunsApi", () => {
  const api = new SuiteRunsApi();
  const orgId = "org-123";

  it("runSuite calls POST /api/v1/orgs/{orgId}/test-suites/{suiteId}/run", async () => {
    const result = (await api.runSuite(orgId, "suite-456")) as unknown as { url: string };
    expect(result.url).toBe("/api/v1/orgs/org-123/test-suites/suite-456/run");
  });

  it("runScenario calls POST /api/v1/orgs/{orgId}/test-scenarios/{scenarioId}/run", async () => {
    const result = (await api.runScenario(orgId, "scenario-789")) as unknown as { url: string };
    expect(result.url).toBe("/api/v1/orgs/org-123/test-scenarios/scenario-789/run");
  });

  it("getSuiteRun calls GET /api/v1/orgs/{orgId}/suite-runs/{runId}", async () => {
    const result = (await api.getSuiteRun(orgId, "run-123")) as unknown as { url: string };
    expect(result.url).toBe("/api/v1/orgs/org-123/suite-runs/run-123");
  });

  it("cancelSuiteRun calls POST /api/v1/orgs/{orgId}/suite-runs/{runId}/cancel", async () => {
    const result = (await api.cancelSuiteRun(orgId, "run-123")) as unknown as { url: string };
    expect(result.url).toBe("/api/v1/orgs/org-123/suite-runs/run-123/cancel");
  });

  it("getExecutionAudioUrl calls GET /api/v1/orgs/{orgId}/executions/{execId}/audio", async () => {
    const result = (await api.getExecutionAudioUrl(orgId, "exec-456")) as unknown as {
      url: string;
    };
    expect(result.url).toBe("/api/v1/orgs/org-123/executions/exec-456/audio");
  });
});
