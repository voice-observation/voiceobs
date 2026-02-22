import { renderHook, act, waitFor } from "@testing-library/react";
import { useVerificationPolling } from "../useVerificationPolling";
import { api } from "@/lib/api";

// Mock the API
jest.mock("@/lib/api", () => ({
  api: {
    agents: {
      getVerificationStatus: jest.fn(),
    },
  },
}));

// Mock the logger
jest.mock("@/lib/logger", () => ({
  logger: {
    error: jest.fn(),
    info: jest.fn(),
  },
}));

describe("useVerificationPolling", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  describe("initial state", () => {
    it("returns initial state correctly", () => {
      const { result } = renderHook(() => useVerificationPolling({ orgId: "org-123" }));

      expect(result.current.status).toBeNull();
      expect(result.current.isPolling).toBe(false);
      expect(result.current.error).toBeNull();
      expect(typeof result.current.startPolling).toBe("function");
      expect(typeof result.current.stopPolling).toBe("function");
    });
  });

  describe("startPolling", () => {
    it("sets isPolling to true when started", async () => {
      (api.agents.getVerificationStatus as jest.Mock).mockResolvedValue({
        connection_status: "connecting",
        verification_attempts: 1,
        last_verification_at: null,
        verification_error: null,
        verification_reasoning: null,
      });

      const { result } = renderHook(() => useVerificationPolling({ orgId: "org-123" }));

      await act(async () => {
        result.current.startPolling("agent-123");
      });

      expect(result.current.isPolling).toBe(true);
    });

    it("calls getVerificationStatus immediately", async () => {
      (api.agents.getVerificationStatus as jest.Mock).mockResolvedValue({
        connection_status: "connecting",
        verification_attempts: 1,
        last_verification_at: null,
        verification_error: null,
        verification_reasoning: null,
      });

      const { result } = renderHook(() => useVerificationPolling({ orgId: "org-123" }));

      await act(async () => {
        result.current.startPolling("agent-123");
      });

      expect(api.agents.getVerificationStatus).toHaveBeenCalledWith("org-123", "agent-123");
    });

    it("updates status after successful poll", async () => {
      const mockStatus = {
        connection_status: "connecting" as const,
        verification_attempts: 1,
        last_verification_at: null,
        verification_error: null,
        verification_reasoning: null,
      };
      (api.agents.getVerificationStatus as jest.Mock).mockResolvedValue(mockStatus);

      const { result } = renderHook(() => useVerificationPolling({ orgId: "org-123" }));

      await act(async () => {
        result.current.startPolling("agent-123");
      });

      await waitFor(() => {
        expect(result.current.status).toEqual(mockStatus);
      });
    });

    it("prevents duplicate starts for same agent", async () => {
      (api.agents.getVerificationStatus as jest.Mock).mockResolvedValue({
        connection_status: "connecting",
        verification_attempts: 1,
        last_verification_at: null,
        verification_error: null,
        verification_reasoning: null,
      });

      const { result } = renderHook(() => useVerificationPolling({ orgId: "org-123" }));

      await act(async () => {
        result.current.startPolling("agent-123");
      });

      await act(async () => {
        result.current.startPolling("agent-123");
      });

      // Should only be called once (initial poll)
      expect(api.agents.getVerificationStatus).toHaveBeenCalledTimes(1);
    });
  });

  describe("stopPolling", () => {
    it("sets isPolling to false when stopped", async () => {
      (api.agents.getVerificationStatus as jest.Mock).mockResolvedValue({
        connection_status: "connecting",
        verification_attempts: 1,
        last_verification_at: null,
        verification_error: null,
        verification_reasoning: null,
      });

      const { result } = renderHook(() => useVerificationPolling({ orgId: "org-123" }));

      await act(async () => {
        result.current.startPolling("agent-123");
      });

      expect(result.current.isPolling).toBe(true);

      act(() => {
        result.current.stopPolling();
      });

      expect(result.current.isPolling).toBe(false);
    });

    it("stops subsequent polls", async () => {
      (api.agents.getVerificationStatus as jest.Mock).mockResolvedValue({
        connection_status: "connecting",
        verification_attempts: 1,
        last_verification_at: null,
        verification_error: null,
        verification_reasoning: null,
      });

      const { result } = renderHook(() =>
        useVerificationPolling({ orgId: "org-123", interval: 1000 })
      );

      await act(async () => {
        result.current.startPolling("agent-123");
      });

      const callCountAfterStart = (api.agents.getVerificationStatus as jest.Mock).mock.calls.length;

      act(() => {
        result.current.stopPolling();
      });

      // Advance timers
      await act(async () => {
        jest.advanceTimersByTime(5000);
      });

      // No additional calls should be made after stopping
      expect(api.agents.getVerificationStatus).toHaveBeenCalledTimes(callCountAfterStart);
    });
  });

  describe("completion handling", () => {
    it("stops polling when status is verified", async () => {
      (api.agents.getVerificationStatus as jest.Mock).mockResolvedValue({
        connection_status: "verified",
        verification_attempts: 1,
        last_verification_at: "2024-01-01T00:00:00Z",
        verification_error: null,
        verification_reasoning: "Agent verified successfully",
      });

      const onComplete = jest.fn();
      const { result } = renderHook(() => useVerificationPolling({ orgId: "org-123", onComplete }));

      await act(async () => {
        result.current.startPolling("agent-123");
      });

      await waitFor(() => {
        expect(result.current.isPolling).toBe(false);
      });

      expect(onComplete).toHaveBeenCalledWith("verified", null);
    });

    it("stops polling when status is failed", async () => {
      (api.agents.getVerificationStatus as jest.Mock).mockResolvedValue({
        connection_status: "failed",
        verification_attempts: 3,
        last_verification_at: "2024-01-01T00:00:00Z",
        verification_error: "Connection timeout",
        verification_reasoning: null,
      });

      const onComplete = jest.fn();
      const { result } = renderHook(() => useVerificationPolling({ orgId: "org-123", onComplete }));

      await act(async () => {
        result.current.startPolling("agent-123");
      });

      await waitFor(() => {
        expect(result.current.isPolling).toBe(false);
      });

      expect(onComplete).toHaveBeenCalledWith("failed", "Connection timeout");
    });

    it("continues polling when status is connecting", async () => {
      (api.agents.getVerificationStatus as jest.Mock).mockResolvedValue({
        connection_status: "connecting",
        verification_attempts: 1,
        last_verification_at: null,
        verification_error: null,
        verification_reasoning: null,
      });

      const onComplete = jest.fn();
      const { result } = renderHook(() =>
        useVerificationPolling({ orgId: "org-123", onComplete, interval: 1000 })
      );

      await act(async () => {
        result.current.startPolling("agent-123");
      });

      expect(result.current.isPolling).toBe(true);
      expect(onComplete).not.toHaveBeenCalled();
    });
  });

  describe("retry logic", () => {
    it("retries on API error up to maxRetries times", async () => {
      (api.agents.getVerificationStatus as jest.Mock)
        .mockRejectedValueOnce(new Error("Network error"))
        .mockRejectedValueOnce(new Error("Network error"))
        .mockRejectedValueOnce(new Error("Network error"));

      const { result } = renderHook(() =>
        useVerificationPolling({ orgId: "org-123", maxRetries: 3, interval: 1000 })
      );

      await act(async () => {
        result.current.startPolling("agent-123");
      });

      // First call (immediate)
      expect(api.agents.getVerificationStatus).toHaveBeenCalledTimes(1);

      // Wait for retry with exponential backoff (2000ms)
      await act(async () => {
        jest.advanceTimersByTime(2000);
      });

      expect(api.agents.getVerificationStatus).toHaveBeenCalledTimes(2);

      // Wait for second retry with exponential backoff (4000ms)
      await act(async () => {
        jest.advanceTimersByTime(4000);
      });

      expect(api.agents.getVerificationStatus).toHaveBeenCalledTimes(3);

      // After maxRetries, polling should stop with error
      await waitFor(() => {
        expect(result.current.isPolling).toBe(false);
        expect(result.current.error).toBe("Network error");
      });
    });

    it("resets retry count on successful poll", async () => {
      (api.agents.getVerificationStatus as jest.Mock)
        .mockRejectedValueOnce(new Error("Network error"))
        .mockResolvedValueOnce({
          connection_status: "connecting",
          verification_attempts: 1,
          last_verification_at: null,
          verification_error: null,
          verification_reasoning: null,
        })
        .mockRejectedValueOnce(new Error("Network error"))
        .mockResolvedValue({
          connection_status: "verified",
          verification_attempts: 1,
          last_verification_at: "2024-01-01T00:00:00Z",
          verification_error: null,
          verification_reasoning: null,
        });

      const { result } = renderHook(() =>
        useVerificationPolling({ orgId: "org-123", maxRetries: 3, interval: 1000 })
      );

      await act(async () => {
        result.current.startPolling("agent-123");
      });

      // First call fails
      expect(api.agents.getVerificationStatus).toHaveBeenCalledTimes(1);

      // Wait for retry
      await act(async () => {
        jest.advanceTimersByTime(2000);
      });

      // Second call succeeds
      expect(api.agents.getVerificationStatus).toHaveBeenCalledTimes(2);

      // Wait for next poll (should be at normal interval since retry count reset)
      await act(async () => {
        jest.advanceTimersByTime(1000);
      });

      expect(api.agents.getVerificationStatus).toHaveBeenCalledTimes(3);
    });

    it("uses exponential backoff for retries", async () => {
      (api.agents.getVerificationStatus as jest.Mock).mockRejectedValue(new Error("Network error"));

      const { result } = renderHook(() =>
        useVerificationPolling({ orgId: "org-123", maxRetries: 3, interval: 1000 })
      );

      await act(async () => {
        result.current.startPolling("agent-123");
      });

      // First call (immediate)
      expect(api.agents.getVerificationStatus).toHaveBeenCalledTimes(1);

      // Retry 1: should happen after 2000ms (1000 * 2^1)
      await act(async () => {
        jest.advanceTimersByTime(1000);
      });
      expect(api.agents.getVerificationStatus).toHaveBeenCalledTimes(1);

      await act(async () => {
        jest.advanceTimersByTime(1000);
      });
      expect(api.agents.getVerificationStatus).toHaveBeenCalledTimes(2);

      // Retry 2: should happen after 4000ms (1000 * 2^2)
      await act(async () => {
        jest.advanceTimersByTime(3000);
      });
      expect(api.agents.getVerificationStatus).toHaveBeenCalledTimes(2);

      await act(async () => {
        jest.advanceTimersByTime(1000);
      });
      expect(api.agents.getVerificationStatus).toHaveBeenCalledTimes(3);
    });
  });

  describe("timeout handling", () => {
    it("stops polling after maxDuration", async () => {
      (api.agents.getVerificationStatus as jest.Mock).mockResolvedValue({
        connection_status: "connecting",
        verification_attempts: 1,
        last_verification_at: null,
        verification_error: null,
        verification_reasoning: null,
      });

      const { result } = renderHook(() =>
        useVerificationPolling({ orgId: "org-123", maxDuration: 5000, interval: 1000 })
      );

      await act(async () => {
        result.current.startPolling("agent-123");
      });

      expect(result.current.isPolling).toBe(true);

      // The timeout check happens inside poll(), which is scheduled via setTimeout
      // We need to advance timers and allow the poll to execute and check the timeout
      // Each poll schedules the next one, so we need to advance multiple times
      for (let i = 0; i < 10; i++) {
        await act(async () => {
          jest.advanceTimersByTime(1000);
        });
      }

      // After maxDuration has passed, the next poll should detect it and stop
      expect(result.current.isPolling).toBe(false);
      expect(result.current.error).toBe("Verification is taking longer than expected");
    });
  });

  describe("agent switching", () => {
    it("stops polling for previous agent when starting new one", async () => {
      (api.agents.getVerificationStatus as jest.Mock).mockResolvedValue({
        connection_status: "connecting",
        verification_attempts: 1,
        last_verification_at: null,
        verification_error: null,
        verification_reasoning: null,
      });

      const { result } = renderHook(() =>
        useVerificationPolling({ orgId: "org-123", interval: 1000 })
      );

      await act(async () => {
        result.current.startPolling("agent-123");
      });

      await act(async () => {
        result.current.startPolling("agent-456");
      });

      // Should have called with agent-456
      expect(api.agents.getVerificationStatus).toHaveBeenLastCalledWith("org-123", "agent-456");
    });
  });

  describe("cleanup", () => {
    it("cleans up on unmount", async () => {
      (api.agents.getVerificationStatus as jest.Mock).mockResolvedValue({
        connection_status: "connecting",
        verification_attempts: 1,
        last_verification_at: null,
        verification_error: null,
        verification_reasoning: null,
      });

      const { result, unmount } = renderHook(() =>
        useVerificationPolling({ orgId: "org-123", interval: 1000 })
      );

      await act(async () => {
        result.current.startPolling("agent-123");
      });

      const callCountBeforeUnmount = (api.agents.getVerificationStatus as jest.Mock).mock.calls
        .length;

      unmount();

      // Advance timers after unmount
      await act(async () => {
        jest.advanceTimersByTime(5000);
      });

      // No additional calls should be made
      expect(api.agents.getVerificationStatus).toHaveBeenCalledTimes(callCountBeforeUnmount);
    });
  });
});
