"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { api } from "@/lib/api";
import type { ConnectionStatus, VerificationStatusResponse } from "@/lib/types";
import { logger } from "@/lib/logger";

export interface UseVerificationPollingOptions {
  /** Polling interval in milliseconds (default: 3000) */
  interval?: number;
  /** Maximum polling duration in milliseconds (default: 120000 = 2 minutes) */
  maxDuration?: number;
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
 */
export function useVerificationPolling(
  options: UseVerificationPollingOptions = {}
): UseVerificationPollingResult {
  const { interval = 3000, maxDuration = 120000, onComplete } = options;

  const [status, setStatus] = useState<VerificationStatusResponse | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const agentIdRef = useRef<string | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const startTimeRef = useRef<number | null>(null);
  const isPollingRef = useRef(false);
  const hasCompletedRef = useRef(false);
  const onCompleteRef = useRef(onComplete);

  // Keep onComplete ref up to date
  useEffect(() => {
    onCompleteRef.current = onComplete;
  }, [onComplete]);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    isPollingRef.current = false;
    setIsPolling(false);
    agentIdRef.current = null;
    startTimeRef.current = null;
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
      const verificationStatus = await api.agents.getVerificationStatus(currentAgentId);

      // Check if polling was stopped while the request was in flight
      if (
        !isPollingRef.current ||
        agentIdRef.current !== currentAgentId ||
        hasCompletedRef.current
      ) {
        return;
      }

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
      }
    } catch (err) {
      // Check if polling was stopped while the request was in flight
      if (!isPollingRef.current || agentIdRef.current !== currentAgentId) {
        return;
      }
      logger.error("Failed to poll verification status", err);
      setError(err instanceof Error ? err.message : "Failed to get verification status");
      stopPolling();
    }
  }, [maxDuration, stopPolling]);

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
      isPollingRef.current = true;
      setIsPolling(true);
      agentIdRef.current = agentId;
      startTimeRef.current = Date.now();

      // Start polling
      poll(); // Initial poll
      intervalRef.current = setInterval(poll, interval);
    },
    [interval, poll, stopPolling]
  );

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
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
