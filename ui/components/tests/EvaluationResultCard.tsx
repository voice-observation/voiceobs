"use client";

import { useState } from "react";
import { Badge } from "@/components/primitives/badge";
import { Card, CardContent, CardHeader } from "@/components/primitives/card";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/primitives/collapsible";
import { CheckCircle2, ChevronDown, ChevronUp, XCircle } from "lucide-react";
import { cn } from "@/lib/utils";
import type { EvaluationResult } from "@/lib/types";

interface EvaluationResultCardProps {
  result: EvaluationResult | null;
  className?: string;
}

function ScoreBar({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
      <div
        className={cn(
          "h-full rounded-full transition-all",
          score >= 0.7 ? "bg-green-500" : "bg-destructive"
        )}
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

export function EvaluationResultCard({ result, className }: EvaluationResultCardProps) {
  const [criteriaOpen, setCriteriaOpen] = useState(true);

  if (!result) {
    return (
      <div
        className={cn(
          "rounded-lg border border-dashed py-4 text-center text-sm text-muted-foreground",
          className
        )}
      >
        No evaluation available
      </div>
    );
  }

  const scorePct = Math.round(result.score * 100);

  return (
    <Card className={className}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between gap-4">
          <Badge
            variant={result.passed ? "default" : "destructive"}
            className={result.passed ? "bg-green-100 text-green-800" : ""}
          >
            {result.passed ? (
              <CheckCircle2 className="mr-1 h-3 w-3" />
            ) : (
              <XCircle className="mr-1 h-3 w-3" />
            )}
            {result.passed ? "Passed" : "Failed"}
          </Badge>
          <span className="text-sm font-medium">{scorePct}%</span>
        </div>
        <div className="mt-1 flex gap-4 text-xs text-muted-foreground">
          <span>Goal: {result.goal_achieved ? "✓" : "✗"}</span>
          <span>Intent: {result.intent_handled ? "✓" : "✗"}</span>
        </div>
      </CardHeader>
      <CardContent className="space-y-3 pt-0">
        {result.criteria && result.criteria.length > 0 && (
          <Collapsible open={criteriaOpen} onOpenChange={setCriteriaOpen}>
            <CollapsibleTrigger className="flex items-center gap-2 text-sm font-medium hover:underline">
              {criteriaOpen ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
              Criteria ({result.criteria.length})
            </CollapsibleTrigger>
            <CollapsibleContent>
              <div className="mt-2 space-y-3">
                {result.criteria.map((c, i) => (
                  <div key={i} className="space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="text-sm">{c.name}</span>
                      <span className="text-xs">
                        {c.passed ? (
                          <CheckCircle2 className="h-3 w-3 text-green-600" />
                        ) : (
                          <XCircle className="h-3 w-3 text-destructive" />
                        )}
                      </span>
                    </div>
                    <ScoreBar score={c.score} />
                    {c.evidence && (
                      <p className="text-xs italic text-muted-foreground">
                        &quot;{c.evidence}&quot;
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </CollapsibleContent>
          </Collapsible>
        )}
        {result.reasoning && (
          <div>
            <p className="mb-1 text-xs font-medium text-muted-foreground">Reasoning</p>
            <p className="text-sm">{result.reasoning}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
