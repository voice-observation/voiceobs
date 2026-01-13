/**
 * Utility functions for test suite operations.
 */

import type { TestSuite } from "../types";

/**
 * Calculate pass rate from test suite status (mock implementation).
 * In a real app, this would calculate from actual test executions.
 */
export function getPassRateFromStatus(status: TestSuite["status"]): number {
  switch (status) {
    case "completed":
      return 95; // Mock value - in real app, calculate from executions
    case "running":
      return 0; // Still running
    case "failed":
      return 45; // Mock value
    case "pending":
      return 0; // Not started
    default:
      return 0;
  }
}

/**
 * Get status badge type from test suite status.
 */
export function getStatusBadgeType(
  status: TestSuite["status"]
): "passed" | "failed" | "warning" | "pending" {
  switch (status) {
    case "completed":
      return "passed";
    case "running":
      return "warning";
    case "failed":
      return "failed";
    case "pending":
      return "pending";
    default:
      return "pending";
  }
}

/**
 * Get status label text from test suite status.
 */
export function getStatusLabel(status: TestSuite["status"]): string {
  switch (status) {
    case "completed":
      return "Passed";
    case "running":
      return "Running";
    case "failed":
      return "Failed";
    case "pending":
      return "Pending";
    default:
      return "Pending";
  }
}

/**
 * Format a date string to relative time (e.g., "2 days ago", "3 hours ago").
 */
export function formatRelativeTime(dateString: string | null): string {
  if (!dateString) return "Never";

  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);
  const diffWeeks = Math.floor(diffDays / 7);
  const diffMonths = Math.floor(diffDays / 30);
  const diffYears = Math.floor(diffDays / 365);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins} minute${diffMins !== 1 ? "s" : ""} ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours !== 1 ? "s" : ""} ago`;
  if (diffDays < 7) return `${diffDays} day${diffDays !== 1 ? "s" : ""} ago`;
  if (diffWeeks < 4) return `${diffWeeks} week${diffWeeks !== 1 ? "s" : ""} ago`;
  if (diffMonths < 12) return `${diffMonths} month${diffMonths !== 1 ? "s" : ""} ago`;
  if (diffYears > 0) return `${diffYears} year${diffYears !== 1 ? "s" : ""} ago`;
  return `${diffDays} day${diffDays !== 1 ? "s" : ""} ago`;
}

/**
 * Get CSS class name for pass rate color based on rate value.
 */
export function getPassRateColor(rate: number): string {
  if (rate >= 90) return "bg-success";
  if (rate >= 70) return "bg-warning";
  return "bg-destructive";
}
