"use client";

import { Badge } from "@/components/primitives/badge";
import { Loader2, CheckCircle, XCircle, Clock, Play, AlertCircle } from "lucide-react";
import type { TestSuiteStatus } from "@/lib/types";

interface TestSuiteStatusBadgeProps {
  status: TestSuiteStatus;
  error?: string | null;
}

/**
 * Unified badge component that displays the status of a test suite.
 * Handles both generation status and execution status in a single badge.
 *
 * Status flow:
 * - pending: Generation waiting to start
 * - generating: AI is creating test scenarios
 * - ready: Generation complete, tests never run
 * - generation_failed: Generation failed
 * - running: Tests are executing
 * - completed: Tests finished successfully
 * - failed: Tests finished with failures
 */
export function TestSuiteStatusBadge({ status, error }: TestSuiteStatusBadgeProps) {
  switch (status) {
    case "pending":
      return (
        <Badge variant="secondary" className="gap-1">
          <Clock className="h-3 w-3" />
          Pending
        </Badge>
      );
    case "generating":
      return (
        <Badge
          variant="secondary"
          className="gap-1 bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
        >
          <Loader2 className="h-3 w-3 animate-spin" />
          Generating...
        </Badge>
      );
    case "ready":
      return (
        <Badge variant="secondary" className="gap-1">
          <AlertCircle className="h-3 w-3" />
          Never Run
        </Badge>
      );
    case "generation_failed":
      return (
        <Badge variant="destructive" className="gap-1" title={error || undefined}>
          <XCircle className="h-3 w-3" />
          Generation Failed
        </Badge>
      );
    case "running":
      return (
        <Badge
          variant="secondary"
          className="gap-1 bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200"
        >
          <Play className="h-3 w-3" />
          Running
        </Badge>
      );
    case "completed":
      return (
        <Badge
          variant="secondary"
          className="gap-1 bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
        >
          <CheckCircle className="h-3 w-3" />
          Passed
        </Badge>
      );
    case "failed":
      return (
        <Badge variant="destructive" className="gap-1">
          <XCircle className="h-3 w-3" />
          Failed
        </Badge>
      );
    default:
      return <Badge variant="outline">{status}</Badge>;
  }
}
