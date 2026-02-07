"use client";

import { Badge } from "@/components/primitives/badge";
import { CheckCircle, Pencil } from "lucide-react";
import { cn } from "@/lib/utils";

interface TestScenarioStatusBadgeProps {
  status: "ready" | "draft";
  className?: string;
}

/**
 * Badge component that displays the status of a test scenario.
 *
 * Status meanings:
 * - ready: Scenario has all required fields (name, goal, persona_id)
 * - draft: Scenario is missing one or more required fields
 */
export function TestScenarioStatusBadge({ status, className }: TestScenarioStatusBadgeProps) {
  const isReady = status === "ready";

  return (
    <Badge
      variant="secondary"
      className={cn(
        "gap-1 text-xs",
        isReady
          ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
          : "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200",
        className
      )}
    >
      {isReady ? <CheckCircle className="h-3 w-3" /> : <Pencil className="h-3 w-3" />}
      {isReady ? "Ready" : "Draft"}
    </Badge>
  );
}
