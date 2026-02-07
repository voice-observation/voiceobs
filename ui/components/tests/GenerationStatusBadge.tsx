"use client";

import { Badge } from "@/components/primitives/badge";
import { Loader2, CheckCircle, XCircle, Clock } from "lucide-react";

interface GenerationStatusBadgeProps {
  status: "pending" | "generating" | "ready" | "generation_failed";
  error?: string;
}

/**
 * Badge component that displays the generation status of a test suite.
 * Shows different visual states for pending, generating, ready, and failed statuses.
 */
export function GenerationStatusBadge({ status, error }: GenerationStatusBadgeProps) {
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
        <Badge variant="secondary" className="gap-1 bg-blue-100 text-blue-800">
          <Loader2 className="h-3 w-3 animate-spin" />
          Generating...
        </Badge>
      );
    case "ready":
      return (
        <Badge variant="secondary" className="gap-1 bg-green-100 text-green-800">
          <CheckCircle className="h-3 w-3" />
          Ready
        </Badge>
      );
    case "generation_failed":
      return (
        <Badge variant="destructive" className="gap-1" title={error}>
          <XCircle className="h-3 w-3" />
          Failed
        </Badge>
      );
    default:
      return <Badge variant="outline">{status}</Badge>;
  }
}
