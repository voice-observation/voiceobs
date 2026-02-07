"use client";

import { useState, useCallback } from "react";
import { api } from "@/lib/api";
import { logger } from "@/lib/logger";
import { useToast } from "@/hooks/use-toast";
import type { TestSuite, TestSuiteCreateRequest, TestSuiteUpdateRequest } from "@/lib/types";

interface UseTestSuiteActionsOptions {
  /** Called when a test suite is created */
  onCreated?: (suite: TestSuite) => void;
  /** Called when a test suite is updated */
  onUpdated?: (suite: TestSuite) => void;
  /** Called when a test suite is deleted */
  onDeleted?: (suiteId: string) => void;
  /** Called when a test suite run completes */
  onRunComplete?: (suiteId: string, status: string) => void;
}

interface UseTestSuiteActionsResult {
  /** Create a new test suite */
  createSuite: (data: TestSuiteCreateRequest) => Promise<TestSuite | null>;
  /** Update a test suite */
  updateSuite: (suiteId: string, data: TestSuiteUpdateRequest) => Promise<TestSuite | null>;
  /** Delete a test suite */
  deleteSuite: (suiteId: string) => Promise<boolean>;
  /** Run a test suite (placeholder for future implementation) */
  runSuite: (suiteId: string) => Promise<void>;
  /** Set of suite IDs currently being created */
  creatingIds: Set<string>;
  /** Set of suite IDs currently being updated */
  updatingIds: Set<string>;
  /** Set of suite IDs currently being deleted */
  deletingIds: Set<string>;
  /** Set of suite IDs currently running */
  runningIds: Set<string>;
}

/**
 * Hook for managing test suite actions with consistent error handling and toast notifications.
 * Tracks loading states per suite ID to support concurrent operations.
 */
export function useTestSuiteActions(
  options: UseTestSuiteActionsOptions = {}
): UseTestSuiteActionsResult {
  const { onCreated, onUpdated, onDeleted, onRunComplete } = options;
  const { toast } = useToast();

  const [creatingIds, setCreatingIds] = useState<Set<string>>(new Set());
  const [updatingIds, setUpdatingIds] = useState<Set<string>>(new Set());
  const [deletingIds, setDeletingIds] = useState<Set<string>>(new Set());
  const [runningIds, setRunningIds] = useState<Set<string>>(new Set());

  const createSuite = useCallback(
    async (data: TestSuiteCreateRequest): Promise<TestSuite | null> => {
      const tempId = `creating-${Date.now()}`;
      try {
        setCreatingIds((prev) => new Set(prev).add(tempId));
        const suite = await api.testSuites.createTestSuite(data);
        toast({
          title: "Test suite created",
          description: `"${suite.name}" has been created successfully.`,
        });
        onCreated?.(suite);
        return suite;
      } catch (err) {
        logger.error("Failed to create test suite", err);
        toast({
          title: "Failed to create test suite",
          description: err instanceof Error ? err.message : "Unknown error",
          variant: "destructive",
        });
        return null;
      } finally {
        setCreatingIds((prev) => {
          const next = new Set(prev);
          next.delete(tempId);
          return next;
        });
      }
    },
    [toast, onCreated]
  );

  const updateSuite = useCallback(
    async (suiteId: string, data: TestSuiteUpdateRequest): Promise<TestSuite | null> => {
      try {
        setUpdatingIds((prev) => new Set(prev).add(suiteId));
        const suite = await api.testSuites.updateTestSuite(suiteId, data);
        toast({
          title: "Test suite updated",
        });
        onUpdated?.(suite);
        return suite;
      } catch (err) {
        logger.error("Failed to update test suite", err);
        toast({
          title: "Failed to update test suite",
          description: err instanceof Error ? err.message : "Unknown error",
          variant: "destructive",
        });
        return null;
      } finally {
        setUpdatingIds((prev) => {
          const next = new Set(prev);
          next.delete(suiteId);
          return next;
        });
      }
    },
    [toast, onUpdated]
  );

  const deleteSuite = useCallback(
    async (suiteId: string): Promise<boolean> => {
      try {
        setDeletingIds((prev) => new Set(prev).add(suiteId));
        await api.testSuites.deleteTestSuite(suiteId);
        toast({
          title: "Test suite deleted",
        });
        onDeleted?.(suiteId);
        return true;
      } catch (err) {
        logger.error("Failed to delete test suite", err);
        toast({
          title: "Failed to delete test suite",
          description: err instanceof Error ? err.message : "Unknown error",
          variant: "destructive",
        });
        return false;
      } finally {
        setDeletingIds((prev) => {
          const next = new Set(prev);
          next.delete(suiteId);
          return next;
        });
      }
    },
    [toast, onDeleted]
  );

  const runSuite = useCallback(
    async (suiteId: string): Promise<void> => {
      try {
        setRunningIds((prev) => new Set(prev).add(suiteId));
        toast({
          title: "Running test suite",
          description: "Test execution started...",
        });

        // TODO: Implement actual run API call
        // await api.testSuites.runTestSuite(suiteId);
        // TODO: Implement polling for run status
        // For now, just simulate a placeholder
        logger.info(`Run suite ${suiteId} - not yet implemented`);

        // Placeholder: remove from running after a delay
        // In real implementation, this would be handled by polling
        setTimeout(() => {
          setRunningIds((prev) => {
            const next = new Set(prev);
            next.delete(suiteId);
            return next;
          });
          onRunComplete?.(suiteId, "completed");
        }, 2000);
      } catch (err) {
        logger.error("Failed to run test suite", err);
        toast({
          title: "Failed to run test suite",
          description: err instanceof Error ? err.message : "Unknown error",
          variant: "destructive",
        });
        setRunningIds((prev) => {
          const next = new Set(prev);
          next.delete(suiteId);
          return next;
        });
      }
    },
    [toast, onRunComplete]
  );

  return {
    createSuite,
    updateSuite,
    deleteSuite,
    runSuite,
    creatingIds,
    updatingIds,
    deletingIds,
    runningIds,
  };
}
