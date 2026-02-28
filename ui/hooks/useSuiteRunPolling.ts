"use client";

import { useEffect, useRef, useCallback } from "react";
import { api } from "@/lib/api";
import type { SuiteRun, SuiteRunStatus } from "@/lib/types";

export interface UseSuiteRunPollingOptions {
  orgId: string;
  suiteRunId: string | null;
  enabled: boolean;
  /** Polling interval in ms. Default: 5000 */
  interval?: number;
  onStatusChange?: (suiteRun: SuiteRun) => void;
  onComplete?: (suiteRun: SuiteRun) => void;
  onError?: (error: Error) => void;
}

export interface UseSuiteRunPollingResult {
  stopPolling: () => void;
}

const TERMINAL_STATUSES: SuiteRunStatus[] = ["completed", "failed", "cancelled"];

export function useSuiteRunPolling({
  orgId,
  suiteRunId,
  enabled,
  interval = 5000,
  onStatusChange,
  onComplete,
  onError,
}: UseSuiteRunPollingOptions): UseSuiteRunPollingResult {
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const onStatusChangeRef = useRef(onStatusChange);
  const onCompleteRef = useRef(onComplete);
  const onErrorRef = useRef(onError);
  onStatusChangeRef.current = onStatusChange;
  onCompleteRef.current = onComplete;
  onErrorRef.current = onError;

  const poll = useCallback(async () => {
    if (!orgId || !suiteRunId) return;
    try {
      const suiteRun = await api.suiteRuns.getSuiteRun(orgId, suiteRunId);
      onStatusChangeRef.current?.(suiteRun);

      if (TERMINAL_STATUSES.includes(suiteRun.status)) {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
        onCompleteRef.current?.(suiteRun);
      }
    } catch (error) {
      console.error("Suite run polling error", error);
      onErrorRef.current?.(error instanceof Error ? error : new Error("Polling failed"));
    }
  }, [orgId, suiteRunId]);

  useEffect(() => {
    if (!enabled || !suiteRunId) return;

    poll();
    intervalRef.current = setInterval(poll, interval);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [enabled, suiteRunId, poll, interval]);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  return { stopPolling };
}
