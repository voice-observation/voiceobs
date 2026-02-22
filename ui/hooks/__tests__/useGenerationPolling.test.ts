import { renderHook, act, waitFor } from "@testing-library/react";
import { useGenerationPolling } from "../useGenerationPolling";
import { api } from "@/lib/api";

// Mock the API
jest.mock("@/lib/api", () => ({
  api: {
    testSuites: {
      getGenerationStatus: jest.fn(),
    },
  },
}));

describe("useGenerationPolling", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  describe("initial state", () => {
    it("does not poll when enabled is false", async () => {
      const { result } = renderHook(() =>
        useGenerationPolling({
          orgId: "org-123",
          suiteId: "suite-123",
          enabled: false,
        })
      );

      expect(api.testSuites.getGenerationStatus).not.toHaveBeenCalled();
      expect(typeof result.current.stopPolling).toBe("function");
    });

    it("does not poll when suiteId is null", async () => {
      const { result } = renderHook(() =>
        useGenerationPolling({
          orgId: "org-123",
          suiteId: null,
          enabled: true,
        })
      );

      expect(api.testSuites.getGenerationStatus).not.toHaveBeenCalled();
      expect(typeof result.current.stopPolling).toBe("function");
    });

    it("handles suiteId becoming null during active polling", async () => {
      (api.testSuites.getGenerationStatus as jest.Mock).mockResolvedValue({
        suite_id: "suite-123",
        status: "generating",
        scenario_count: 0,
      });

      const { rerender } = renderHook(
        ({ suiteId }) =>
          useGenerationPolling({
            orgId: "org-123",
            suiteId,
            enabled: true,
            interval: 1000,
          }),
        { initialProps: { suiteId: "suite-123" as string | null } }
      );

      await act(async () => {
        await Promise.resolve();
      });

      expect(api.testSuites.getGenerationStatus).toHaveBeenCalledTimes(1);

      // Change suiteId to null - poll function will early return if called
      rerender({ suiteId: null });

      // Since enabled is still true but suiteId is null, the effect cleanup runs
      // and no new interval is started
      await act(async () => {
        jest.advanceTimersByTime(3000);
      });

      // No additional calls should be made
      expect(api.testSuites.getGenerationStatus).toHaveBeenCalledTimes(1);
    });
  });

  describe("polling behavior", () => {
    it("polls immediately when enabled with valid suiteId", async () => {
      (api.testSuites.getGenerationStatus as jest.Mock).mockResolvedValue({
        suite_id: "suite-123",
        status: "generating",
        scenario_count: 0,
      });

      renderHook(() =>
        useGenerationPolling({
          orgId: "org-123",
          suiteId: "suite-123",
          enabled: true,
        })
      );

      await act(async () => {
        await Promise.resolve();
      });

      expect(api.testSuites.getGenerationStatus).toHaveBeenCalledWith("org-123", "suite-123");
    });

    it("continues polling at specified interval when status is generating", async () => {
      (api.testSuites.getGenerationStatus as jest.Mock).mockResolvedValue({
        suite_id: "suite-123",
        status: "generating",
        scenario_count: 0,
      });

      renderHook(() =>
        useGenerationPolling({
          orgId: "org-123",
          suiteId: "suite-123",
          enabled: true,
          interval: 1000,
        })
      );

      await act(async () => {
        await Promise.resolve();
      });

      expect(api.testSuites.getGenerationStatus).toHaveBeenCalledTimes(1);

      // Advance timer
      await act(async () => {
        jest.advanceTimersByTime(1000);
        await Promise.resolve();
      });

      expect(api.testSuites.getGenerationStatus).toHaveBeenCalledTimes(2);
    });

    it("calls onStatusChange with each poll result", async () => {
      const mockStatus = {
        suite_id: "suite-123",
        status: "generating" as const,
        scenario_count: 2,
      };
      (api.testSuites.getGenerationStatus as jest.Mock).mockResolvedValue(mockStatus);

      const onStatusChange = jest.fn();

      renderHook(() =>
        useGenerationPolling({
          orgId: "org-123",
          suiteId: "suite-123",
          enabled: true,
          onStatusChange,
        })
      );

      await act(async () => {
        await Promise.resolve();
      });

      expect(onStatusChange).toHaveBeenCalledWith(mockStatus);
    });
  });

  describe("completion handling", () => {
    it("stops polling and calls onComplete when status is ready", async () => {
      const mockStatus = {
        suite_id: "suite-123",
        status: "ready" as const,
        scenario_count: 5,
      };
      (api.testSuites.getGenerationStatus as jest.Mock).mockResolvedValue(mockStatus);

      const onComplete = jest.fn();
      const onStatusChange = jest.fn();

      renderHook(() =>
        useGenerationPolling({
          orgId: "org-123",
          suiteId: "suite-123",
          enabled: true,
          interval: 1000,
          onComplete,
          onStatusChange,
        })
      );

      await act(async () => {
        await Promise.resolve();
      });

      expect(onComplete).toHaveBeenCalledWith(mockStatus);
      expect(onStatusChange).toHaveBeenCalledWith(mockStatus);

      // Verify polling stopped - advance time and check no more calls
      const callCount = (api.testSuites.getGenerationStatus as jest.Mock).mock.calls.length;

      await act(async () => {
        jest.advanceTimersByTime(3000);
      });

      expect(api.testSuites.getGenerationStatus).toHaveBeenCalledTimes(callCount);
    });

    it("stops polling and calls onComplete when status is generation_failed", async () => {
      const mockStatus = {
        suite_id: "suite-123",
        status: "generation_failed" as const,
        scenario_count: 0,
        error: "Generation failed due to API error",
      };
      (api.testSuites.getGenerationStatus as jest.Mock).mockResolvedValue(mockStatus);

      const onComplete = jest.fn();

      renderHook(() =>
        useGenerationPolling({
          orgId: "org-123",
          suiteId: "suite-123",
          enabled: true,
          interval: 1000,
          onComplete,
        })
      );

      await act(async () => {
        await Promise.resolve();
      });

      expect(onComplete).toHaveBeenCalledWith(mockStatus);

      // Verify polling stopped
      const callCount = (api.testSuites.getGenerationStatus as jest.Mock).mock.calls.length;

      await act(async () => {
        jest.advanceTimersByTime(3000);
      });

      expect(api.testSuites.getGenerationStatus).toHaveBeenCalledTimes(callCount);
    });

    it("continues polling when status is pending", async () => {
      (api.testSuites.getGenerationStatus as jest.Mock).mockResolvedValue({
        suite_id: "suite-123",
        status: "pending",
        scenario_count: 0,
      });

      const onComplete = jest.fn();

      renderHook(() =>
        useGenerationPolling({
          orgId: "org-123",
          suiteId: "suite-123",
          enabled: true,
          interval: 1000,
          onComplete,
        })
      );

      await act(async () => {
        await Promise.resolve();
      });

      expect(onComplete).not.toHaveBeenCalled();

      // Polling should continue
      await act(async () => {
        jest.advanceTimersByTime(1000);
        await Promise.resolve();
      });

      expect(api.testSuites.getGenerationStatus).toHaveBeenCalledTimes(2);
    });
  });

  describe("error handling", () => {
    it("calls onError when API call fails", async () => {
      const error = new Error("Network error");
      (api.testSuites.getGenerationStatus as jest.Mock).mockRejectedValue(error);

      const onError = jest.fn();

      renderHook(() =>
        useGenerationPolling({
          orgId: "org-123",
          suiteId: "suite-123",
          enabled: true,
          onError,
        })
      );

      await act(async () => {
        await Promise.resolve();
      });

      expect(onError).toHaveBeenCalledWith(error);
    });

    it("wraps non-Error objects in Error when calling onError", async () => {
      (api.testSuites.getGenerationStatus as jest.Mock).mockRejectedValue("string error");

      const onError = jest.fn();

      renderHook(() =>
        useGenerationPolling({
          orgId: "org-123",
          suiteId: "suite-123",
          enabled: true,
          onError,
        })
      );

      await act(async () => {
        await Promise.resolve();
      });

      expect(onError).toHaveBeenCalledWith(expect.any(Error));
      expect(onError.mock.calls[0][0].message).toBe("Polling failed");
    });
  });

  describe("stopPolling", () => {
    it("stops polling when stopPolling is called", async () => {
      (api.testSuites.getGenerationStatus as jest.Mock).mockResolvedValue({
        suite_id: "suite-123",
        status: "generating",
        scenario_count: 0,
      });

      const { result } = renderHook(() =>
        useGenerationPolling({
          orgId: "org-123",
          suiteId: "suite-123",
          enabled: true,
          interval: 1000,
        })
      );

      await act(async () => {
        await Promise.resolve();
      });

      const callCount = (api.testSuites.getGenerationStatus as jest.Mock).mock.calls.length;

      act(() => {
        result.current.stopPolling();
      });

      // Advance timer
      await act(async () => {
        jest.advanceTimersByTime(3000);
      });

      // No additional calls should be made
      expect(api.testSuites.getGenerationStatus).toHaveBeenCalledTimes(callCount);
    });
  });

  describe("enabled toggle", () => {
    it("stops polling when enabled changes to false", async () => {
      (api.testSuites.getGenerationStatus as jest.Mock).mockResolvedValue({
        suite_id: "suite-123",
        status: "generating",
        scenario_count: 0,
      });

      const { rerender } = renderHook(
        ({ enabled }) =>
          useGenerationPolling({
            orgId: "org-123",
            suiteId: "suite-123",
            enabled,
            interval: 1000,
          }),
        { initialProps: { enabled: true } }
      );

      await act(async () => {
        await Promise.resolve();
      });

      const callCount = (api.testSuites.getGenerationStatus as jest.Mock).mock.calls.length;

      // Disable polling - this triggers the cleanup path in the effect
      rerender({ enabled: false });

      // Advance timer
      await act(async () => {
        jest.advanceTimersByTime(3000);
      });

      // No additional calls should be made
      expect(api.testSuites.getGenerationStatus).toHaveBeenCalledTimes(callCount);
    });

    it("clears interval when suiteId changes to null while polling", async () => {
      (api.testSuites.getGenerationStatus as jest.Mock).mockResolvedValue({
        suite_id: "suite-123",
        status: "generating",
        scenario_count: 0,
      });

      const { rerender } = renderHook(
        ({ suiteId }) =>
          useGenerationPolling({
            orgId: "org-123",
            suiteId,
            enabled: true,
            interval: 1000,
          }),
        { initialProps: { suiteId: "suite-123" as string | null } }
      );

      await act(async () => {
        await Promise.resolve();
      });

      // Advance timer to ensure interval is set and at least one poll happened
      await act(async () => {
        jest.advanceTimersByTime(1000);
        await Promise.resolve();
      });

      const callCount = (api.testSuites.getGenerationStatus as jest.Mock).mock.calls.length;

      // Change suiteId to null - this triggers the cleanup path in the effect
      rerender({ suiteId: null });

      // Advance timer more
      await act(async () => {
        jest.advanceTimersByTime(3000);
      });

      // No additional calls should be made after suiteId becomes null
      expect(api.testSuites.getGenerationStatus).toHaveBeenCalledTimes(callCount);
    });

    it("starts polling when enabled changes to true", async () => {
      (api.testSuites.getGenerationStatus as jest.Mock).mockResolvedValue({
        suite_id: "suite-123",
        status: "generating",
        scenario_count: 0,
      });

      const { rerender } = renderHook(
        ({ enabled }) =>
          useGenerationPolling({
            orgId: "org-123",
            suiteId: "suite-123",
            enabled,
            interval: 1000,
          }),
        { initialProps: { enabled: false } }
      );

      expect(api.testSuites.getGenerationStatus).not.toHaveBeenCalled();

      // Enable polling
      rerender({ enabled: true });

      await act(async () => {
        await Promise.resolve();
      });

      expect(api.testSuites.getGenerationStatus).toHaveBeenCalledWith("org-123", "suite-123");
    });
  });

  describe("cleanup", () => {
    it("cleans up on unmount", async () => {
      (api.testSuites.getGenerationStatus as jest.Mock).mockResolvedValue({
        suite_id: "suite-123",
        status: "generating",
        scenario_count: 0,
      });

      const { unmount } = renderHook(() =>
        useGenerationPolling({
          orgId: "org-123",
          suiteId: "suite-123",
          enabled: true,
          interval: 1000,
        })
      );

      await act(async () => {
        await Promise.resolve();
      });

      const callCount = (api.testSuites.getGenerationStatus as jest.Mock).mock.calls.length;

      unmount();

      // Advance timers after unmount
      await act(async () => {
        jest.advanceTimersByTime(5000);
      });

      // No additional calls should be made
      expect(api.testSuites.getGenerationStatus).toHaveBeenCalledTimes(callCount);
    });
  });
});
