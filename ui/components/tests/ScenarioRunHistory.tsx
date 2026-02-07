"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/primitives/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/primitives/table";
import { Badge } from "@/components/primitives/badge";
import { CheckCircle2, XCircle, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

interface RunData {
  id: string;
  created_at: string;
  passed: boolean;
  duration_seconds?: number;
  turns_count?: number;
}

interface ScenarioRunHistoryProps {
  runs: RunData[];
  onRowClick?: (runId: string) => void;
}

export function ScenarioRunHistory({ runs, onRowClick }: ScenarioRunHistoryProps) {
  // Calculate summary stats
  const totalRuns = runs.length;
  const passedRuns = runs.filter((r) => r.passed).length;
  const passRate = totalRuns > 0 ? Math.round((passedRuns / totalRuns) * 100) : 0;

  // Sort runs by date (newest first)
  const sortedRuns = [...runs].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  };

  const formatDuration = (seconds?: number) => {
    if (seconds == null) return "-";
    if (seconds < 60) return `${Math.round(seconds)}s`;
    const minutes = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    return `${minutes}m ${secs}s`;
  };

  if (runs.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Run History</CardTitle>
        </CardHeader>
        <CardContent className="py-8 text-center text-muted-foreground">No runs yet</CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
        <CardTitle className="text-lg">Run History</CardTitle>
        <div className="flex items-center gap-3 text-sm text-muted-foreground">
          <span>{totalRuns} runs</span>
          <Badge
            variant="outline"
            className={cn(
              passRate >= 80
                ? "border-green-200 bg-green-500/10 text-green-600"
                : passRate >= 50
                  ? "border-yellow-200 bg-yellow-500/10 text-yellow-600"
                  : "border-red-200 bg-red-500/10 text-red-600"
            )}
          >
            {passRate}% pass rate
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Date</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Duration</TableHead>
              <TableHead>Turns</TableHead>
              <TableHead className="w-[40px]"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sortedRuns.map((run) => (
              <TableRow
                key={run.id}
                className={cn(onRowClick && "cursor-pointer hover:bg-muted/50")}
                onClick={() => onRowClick?.(run.id)}
              >
                <TableCell className="font-medium">{formatDate(run.created_at)}</TableCell>
                <TableCell>
                  <div className="flex items-center gap-1.5">
                    {run.passed ? (
                      <>
                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                        <span className="text-green-600">Passed</span>
                      </>
                    ) : (
                      <>
                        <XCircle className="h-4 w-4 text-red-500" />
                        <span className="text-red-600">Failed</span>
                      </>
                    )}
                  </div>
                </TableCell>
                <TableCell>{formatDuration(run.duration_seconds)}</TableCell>
                <TableCell>{run.turns_count ?? "-"}</TableCell>
                <TableCell>
                  {onRowClick && <ChevronRight className="h-4 w-4 text-muted-foreground" />}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
