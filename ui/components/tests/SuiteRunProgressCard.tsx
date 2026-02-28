"use client";

import { Card, CardContent, CardHeader } from "@/components/primitives/card";
import { Button } from "@/components/primitives/button";
import { Progress } from "@/components/primitives/progress";
import { ExecutionStatusBadge } from "./ExecutionStatusBadge";
import { CheckCircle2, XCircle, Clock, Phone, Loader2 } from "lucide-react";
import type { SuiteRun, ExecutionSummary } from "@/lib/types";

interface SuiteRunProgressCardProps {
  suiteRun: SuiteRun;
  onCancel?: () => void;
  isCancelling?: boolean;
  className?: string;
}

function getExecutionIcon(exec: ExecutionSummary) {
  if (exec.status === "completed") {
    return exec.evaluation_result?.passed ? (
      <CheckCircle2 className="h-4 w-4 text-green-600" />
    ) : (
      <XCircle className="h-4 w-4 text-destructive" />
    );
  }
  if (exec.status === "calling" || exec.status === "evaluating") {
    return <Loader2 className="h-4 w-4 animate-spin" />;
  }
  return <Clock className="h-4 w-4 text-muted-foreground" />;
}

export function SuiteRunProgressCard({
  suiteRun,
  onCancel,
  isCancelling = false,
  className,
}: SuiteRunProgressCardProps) {
  const completed = suiteRun.completed_scenarios + suiteRun.failed_scenarios;
  const progress = suiteRun.total_scenarios > 0 ? (completed / suiteRun.total_scenarios) * 100 : 0;
  const isTerminal = ["completed", "failed", "cancelled"].includes(suiteRun.status);

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold">
            {suiteRun.status === "running" || suiteRun.status === "pending"
              ? "Running Tests"
              : "Test Run Complete"}
          </h3>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span>
              [{completed}/{suiteRun.total_scenarios}]
            </span>
            <Progress value={progress} className="h-2 w-24" />
            <span>{Math.round(progress)}%</span>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        {suiteRun.executions.map((exec) => (
          <div
            key={exec.id}
            className="flex items-center justify-between gap-4 rounded-lg border px-3 py-2 text-sm"
          >
            <div className="flex min-w-0 items-center gap-2">
              {getExecutionIcon(exec)}
              <span className="truncate">
                {exec.scenario_name ?? `Scenario ${exec.scenario_id.slice(0, 8)}`}
              </span>
            </div>
            <ExecutionStatusBadge status={exec.status} passed={exec.evaluation_result?.passed} />
          </div>
        ))}
        {!isTerminal && onCancel && (
          <Button
            variant="outline"
            size="sm"
            className="mt-2"
            onClick={onCancel}
            disabled={isCancelling}
          >
            Cancel
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
