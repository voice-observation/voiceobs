"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { api } from "@/lib/api";
import { logger } from "@/lib/logger";
import { useToast } from "@/hooks/use-toast";
import { useVerificationPolling } from "@/hooks/useVerificationPolling";
import type { Agent, AgentUpdateRequest } from "@/lib/types";

interface UseAgentActionsOptions {
  /** Called when verification completes successfully */
  onVerified?: (agentId: string) => void;
  /** Called when an agent is deleted */
  onDeleted?: (agentId: string) => void;
  /** Called when an agent is updated */
  onUpdated?: (agent: Agent) => void;
  /** Called when an agent's active status is toggled */
  onActiveToggled?: (agentId: string, isActive: boolean) => void;
}

interface UseAgentActionsResult {
  /** Trigger verification for an agent */
  verifyAgent: (agentId: string) => Promise<void>;
  /** Delete an agent */
  deleteAgent: (agentId: string) => Promise<void>;
  /** Update an agent */
  updateAgent: (
    agentId: string,
    data: AgentUpdateRequest,
    currentPhoneNumber?: string | null
  ) => Promise<Agent | null>;
  /** Toggle an agent's active status */
  toggleActive: (agentId: string, currentIsActive: boolean) => Promise<void>;
  /** Set of agent IDs currently being verified */
  verifyingIds: Set<string>;
  /** Set of agent IDs currently being deleted */
  deletingIds: Set<string>;
  /** Set of agent IDs currently being updated */
  updatingIds: Set<string>;
}

/**
 * Hook for managing agent actions with consistent error handling and toast notifications.
 * Tracks loading states per agent ID to support concurrent operations.
 */
export function useAgentActions(options: UseAgentActionsOptions = {}): UseAgentActionsResult {
  const { onVerified, onDeleted, onUpdated, onActiveToggled } = options;
  const { toast } = useToast();

  const [verifyingIds, setVerifyingIds] = useState<Set<string>>(new Set());
  const [deletingIds, setDeletingIds] = useState<Set<string>>(new Set());
  const [updatingIds, setUpdatingIds] = useState<Set<string>>(new Set());

  // Use ref for startPolling to avoid circular dependencies
  const startPollingRef = useRef<((agentId: string) => void) | null>(null);
  const onVerifiedRef = useRef(onVerified);

  // Keep refs up to date
  useEffect(() => {
    onVerifiedRef.current = onVerified;
  }, [onVerified]);

  const handleVerificationComplete = useCallback(
    (agentId: string) => (status: string, verificationError?: string | null) => {
      // Remove from verifying set
      setVerifyingIds((prev) => {
        const next = new Set(prev);
        next.delete(agentId);
        return next;
      });

      if (status === "verified") {
        toast({
          title: "Agent verified",
          description: "The agent has been successfully verified.",
        });
        onVerifiedRef.current?.(agentId);
      } else if (status === "failed") {
        toast({
          title: "Verification failed",
          description: verificationError || "Agent verification failed.",
          variant: "destructive",
        });
      }
    },
    [toast]
  );

  // We need a separate polling instance per agent being verified
  // For simplicity, we'll use a single polling instance and track the current agent
  const currentVerifyingAgentRef = useRef<string | null>(null);

  const { startPolling } = useVerificationPolling({
    onComplete: (status, verificationError) => {
      const agentId = currentVerifyingAgentRef.current;
      if (agentId) {
        handleVerificationComplete(agentId)(status, verificationError);
        currentVerifyingAgentRef.current = null;
      }
    },
  });

  // Keep ref up to date
  useEffect(() => {
    startPollingRef.current = startPolling;
  }, [startPolling]);

  const verifyAgent = useCallback(
    async (agentId: string) => {
      try {
        setVerifyingIds((prev) => new Set(prev).add(agentId));
        currentVerifyingAgentRef.current = agentId;

        await api.agents.verifyAgent(agentId, true);
        toast({
          title: "Verification started",
          description: "Verifying agent...",
        });
        startPollingRef.current?.(agentId);
      } catch (err) {
        logger.error("Failed to start verification", err);
        setVerifyingIds((prev) => {
          const next = new Set(prev);
          next.delete(agentId);
          return next;
        });
        currentVerifyingAgentRef.current = null;
        toast({
          title: "Failed to start verification",
          description: err instanceof Error ? err.message : "Unknown error",
          variant: "destructive",
        });
      }
    },
    [toast]
  );

  const deleteAgent = useCallback(
    async (agentId: string) => {
      try {
        setDeletingIds((prev) => new Set(prev).add(agentId));
        await api.agents.deleteAgent(agentId);
        toast({
          title: "Agent deleted",
        });
        onDeleted?.(agentId);
      } catch (err) {
        logger.error("Failed to delete agent", err);
        toast({
          title: "Failed to delete agent",
          description: err instanceof Error ? err.message : "Unknown error",
          variant: "destructive",
        });
      } finally {
        setDeletingIds((prev) => {
          const next = new Set(prev);
          next.delete(agentId);
          return next;
        });
      }
    },
    [toast, onDeleted]
  );

  const updateAgent = useCallback(
    async (
      agentId: string,
      data: AgentUpdateRequest,
      currentPhoneNumber?: string | null
    ): Promise<Agent | null> => {
      try {
        setUpdatingIds((prev) => new Set(prev).add(agentId));

        // Check if phone number changed (will trigger re-verification)
        const phoneChanged =
          data.phone_number !== undefined && data.phone_number !== currentPhoneNumber;

        const updatedAgent = await api.agents.updateAgent(agentId, data);

        if (phoneChanged) {
          toast({
            title: "Agent updated",
            description: "Re-verification in progress...",
          });
          // Start polling for verification
          setVerifyingIds((prev) => new Set(prev).add(agentId));
          currentVerifyingAgentRef.current = agentId;
          startPollingRef.current?.(agentId);
        } else {
          toast({
            title: "Agent updated",
          });
        }

        onUpdated?.(updatedAgent);
        return updatedAgent;
      } catch (err) {
        logger.error("Failed to update agent", err);
        toast({
          title: "Failed to update agent",
          description: err instanceof Error ? err.message : "Unknown error",
          variant: "destructive",
        });
        return null;
      } finally {
        setUpdatingIds((prev) => {
          const next = new Set(prev);
          next.delete(agentId);
          return next;
        });
      }
    },
    [toast, onUpdated]
  );

  const toggleActive = useCallback(
    async (agentId: string, currentIsActive: boolean) => {
      const newIsActive = !currentIsActive;
      try {
        setUpdatingIds((prev) => new Set(prev).add(agentId));
        await api.agents.updateAgent(agentId, { is_active: newIsActive });
        toast({
          title: newIsActive ? "Agent activated" : "Agent deactivated",
          description: newIsActive
            ? "The agent is now active and can receive calls."
            : "The agent is now inactive.",
        });
        onActiveToggled?.(agentId, newIsActive);
      } catch (err) {
        logger.error("Failed to toggle agent status", err);
        toast({
          title: "Failed to update agent",
          description: err instanceof Error ? err.message : "Unknown error",
          variant: "destructive",
        });
        throw err; // Re-throw so caller can handle optimistic update revert
      } finally {
        setUpdatingIds((prev) => {
          const next = new Set(prev);
          next.delete(agentId);
          return next;
        });
      }
    },
    [toast, onActiveToggled]
  );

  return {
    verifyAgent,
    deleteAgent,
    updateAgent,
    toggleActive,
    verifyingIds,
    deletingIds,
    updatingIds,
  };
}
