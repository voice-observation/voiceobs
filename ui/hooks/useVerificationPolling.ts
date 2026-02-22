"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { api } from "@/lib/api";
import type { ConnectionStatus, VerificationStatusResponse } from "@/lib/types";
import { logger } from "@/lib/logger";

export interface UseVerificationPollingOptions {
  /** Organization ID for org-scoped agent API calls (required) */
  orgId?: string;
  /** Polling interval in milliseconds (default: 3000) */
  interval?: number;
  /** Maximum polling duration in milliseconds (default: 120000 = 2 minutes) */
  maxDuration?: number;
  /** Maximum number of consecutive API failures before stopping (default: 3) */
  maxRetries?: number;
  /** Callback when verification completes */
  onComplete?: (status: ConnectionStatus, error?: string | null) => void;
}

export interface UseVerificationPollingResult {
  /** Current verification status */
  status: VerificationStatusResponse | null;
  /** Whether polling is active */
  isPolling: boolean;
  /** Error message if polling failed */
  error: string | null;
  /** Start polling for an agent */
  startPolling: (agentId: string) => void;
  /** Stop polling */
  stopPolling: () => void;
}

/**
 * Hook for polling agent verification status.
 * Polls every 3 seconds until status is "verified" or "failed".
 * Retries up to maxRetries times on API errors with exponential backoff.
 */
export function useVerificationPolling(
  options: UseVerificationPollingOptions = {}
): UseVerificationPollingResult {
  const { orgId = "", interval = 3000, maxDuration = 120000, maxRetries = 3, onComplete } = options;

  const [status, setStatus] = useState<VerificationStatusResponse | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const agentIdRef = useRef<string | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const startTimeRef = useRef<number | null>(null);
  const isPollingRef = useRef(false);
  const hasCompletedRef = useRef(false);
  const retryCountRef = useRef(0);
  const onCompleteRef = useRef(onComplete);
  const pollRef = useRef<() => Promise<void>>();

  // Keep onComplete ref up to date
  useEffect(() => {
    onCompleteRef.current = onComplete;
  }, [onComplete]);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    isPollingRef.current = false;
    setIsPolling(false);
    agentIdRef.current = null;
    startTimeRef.current = null;
    retryCountRef.current = 0;
  }, []);

  const scheduleNextPoll = useCallback((delay: number) => {
    // Clear any existing scheduled poll
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    timeoutRef.current = setTimeout(() => {
      pollRef.current?.();
    }, delay);
  }, []);

  const poll = useCallback(async () => {
    // Early exit if polling was stopped or already completed
    if (!agentIdRef.current || !isPollingRef.current || hasCompletedRef.current) {
      return;
    }

    // Check timeout
    if (startTimeRef.current && Date.now() - startTimeRef.current > maxDuration) {
      setError("Verification is taking longer than expected");
      stopPolling();
      return;
    }

    // Capture the current agentId to check after async call
    const currentAgentId = agentIdRef.current;

    try {
      if (!orgId) return;
      const verificationStatus = await api.agents.getVerificationStatus(orgId, currentAgentId);

      // Check if polling was stopped while the request was in flight
      if (
        !isPollingRef.current ||
        agentIdRef.current !== currentAgentId ||
        hasCompletedRef.current
      ) {
        return;
      }

      // Reset retry count on success
      retryCountRef.current = 0;
      setStatus(verificationStatus);

      // Stop polling if verification is complete
      if (
        verificationStatus.connection_status === "verified" ||
        verificationStatus.connection_status === "failed"
      ) {
        // Mark as completed to prevent duplicate onComplete calls
        hasCompletedRef.current = true;
        stopPolling();
        onCompleteRef.current?.(
          verificationStatus.connection_status,
          verificationStatus.verification_error
        );
      } else {
        // Schedule next poll at normal interval
        scheduleNextPoll(interval);
      }
    } catch (err) {
      // Check if polling was stopped while the request was in flight
      if (!isPollingRef.current || agentIdRef.current !== currentAgentId) {
        return;
      }

      retryCountRef.current += 1;
      logger.error(
        `Failed to poll verification status (attempt ${retryCountRef.current}/${maxRetries})`,
        err
      );

      if (retryCountRef.current >= maxRetries) {
        // Max retries reached, stop polling
        setError(err instanceof Error ? err.message : "Failed to get verification status");
        stopPolling();
      } else {
        // Retry with exponential backoff: interval * 2^retryCount
        const backoffDelay = interval * Math.pow(2, retryCountRef.current);
        logger.info(`Retrying in ${backoffDelay}ms...`);
        scheduleNextPoll(backoffDelay);
      }
    }
  }, [orgId, maxDuration, maxRetries, interval, stopPolling, scheduleNextPoll]);

  // Keep pollRef up to date
  useEffect(() => {
    pollRef.current = poll;
  }, [poll]);

  const startPolling = useCallback(
    (agentId: string) => {
      // Prevent duplicate starts while already polling the same agent
      if (isPollingRef.current && agentIdRef.current === agentId) {
        return;
      }

      // Stop any existing polling
      stopPolling();

      // Reset state
      setStatus(null);
      setError(null);
      hasCompletedRef.current = false;
      retryCountRef.current = 0;
      isPollingRef.current = true;
      setIsPolling(true);
      agentIdRef.current = agentId;
      startTimeRef.current = Date.now();

      // Start polling (initial poll, subsequent polls scheduled via setTimeout)
      poll();
    },
    [poll, stopPolling]
  );

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return {
    status,
    isPolling,
    error,
    startPolling,
    stopPolling,
  };
}
