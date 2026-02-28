import { renderHook, act } from "@testing-library/react";
import { useSuiteRunPolling } from "../useSuiteRunPolling";
import { api } from "@/lib/api";

jest.mock("@/lib/api");

describe("useSuiteRunPolling", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("does not poll when suiteRunId is null", () => {
    renderHook(() => useSuiteRunPolling({ orgId: "org-1", suiteRunId: null, enabled: true }));
    expect(api.suiteRuns.getSuiteRun).not.toHaveBeenCalled();
  });

  it("does not poll when disabled", () => {
    renderHook(() => useSuiteRunPolling({ orgId: "org-1", suiteRunId: "run-1", enabled: false }));
    expect(api.suiteRuns.getSuiteRun).not.toHaveBeenCalled();
  });

  it("polls immediately when enabled with suiteRunId", async () => {
    (api.suiteRuns.getSuiteRun as jest.Mock).mockResolvedValue({
      id: "run-1",
      status: "running",
      total_scenarios: 5,
      completed_scenarios: 2,
      failed_scenarios: 0,
      executions: [],
    });

    renderHook(() => useSuiteRunPolling({ orgId: "org-1", suiteRunId: "run-1", enabled: true }));

    await act(async () => {
      await Promise.resolve();
    });

    expect(api.suiteRuns.getSuiteRun).toHaveBeenCalledWith("org-1", "run-1");
  });

  it("stops polling when status is completed", async () => {
    const onComplete = jest.fn();
    (api.suiteRuns.getSuiteRun as jest.Mock).mockResolvedValue({
      id: "run-1",
      status: "completed",
      total_scenarios: 5,
      completed_scenarios: 5,
      failed_scenarios: 0,
      executions: [],
    });

    renderHook(() =>
      useSuiteRunPolling({
        orgId: "org-1",
        suiteRunId: "run-1",
        enabled: true,
        onComplete,
      })
    );

    await act(async () => {
      await Promise.resolve();
    });

    expect(onComplete).toHaveBeenCalled();
  });
});
