"use client";

import { useEffect, useRef, useCallback } from "react";
import { api } from "@/lib/api";
import type { GenerationStatusResponse } from "@/lib/types";

/**
 * Options for the useGenerationPolling hook.
 */
export interface UseGenerationPollingOptions {
  /** Organization ID for org-scoped test suite API calls (required) */
  orgId?: string;
  /** The ID of the test suite to poll generation status for */
  suiteId: string | null;
  /** Whether polling is enabled */
  enabled: boolean;
  /** Polling interval in milliseconds (default: 2000) */
  interval?: number;
  /** Callback when status changes */
  onStatusChange?: (status: GenerationStatusResponse) => void;
  /** Callback when generation completes (status is 'ready' or 'generation_failed') */
  onComplete?: (status: GenerationStatusResponse) => void;
  /** Callback when an error occurs during polling */
  onError?: (error: Error) => void;
}

/**
 * Result of the useGenerationPolling hook.
 */
export interface UseGenerationPollingResult {
  /** Manually stop polling */
  stopPolling: () => void;
}

/**
 * Hook for polling test suite generation status.
 * Polls at the specified interval until status is "ready" or "generation_failed".
 * Automatically stops polling when the status indicates completion or failure.
 */
export function useGenerationPolling({
  orgId = "",
  suiteId,
  enabled,
  interval = 2000,
  onStatusChange,
  onComplete,
  onError,
}: UseGenerationPollingOptions): UseGenerationPollingResult {
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const poll = useCallback(async () => {
    // suiteId is guaranteed to be non-null when poll is called
    // because the effect only starts polling when suiteId is truthy
    try {
      if (!orgId) return;
      const status = await api.testSuites.getGenerationStatus(orgId, suiteId!);
      onStatusChange?.(status);

      // Stop polling when generation is complete or failed
      if (status.status === "ready" || status.status === "generation_failed") {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
        onComplete?.(status);
      }
    } catch (error) {
      console.error("Generation polling error", error);
      onError?.(error instanceof Error ? error : new Error("Polling failed"));
    }
  }, [orgId, suiteId, onStatusChange, onComplete, onError]);

  useEffect(() => {
    // Don't start polling if disabled or no suiteId
    if (!enabled || !suiteId) {
      return;
    }

    // Initial poll
    poll();

    // Start interval
    intervalRef.current = setInterval(poll, interval);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [enabled, suiteId, poll, interval]);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  return { stopPolling };
}
