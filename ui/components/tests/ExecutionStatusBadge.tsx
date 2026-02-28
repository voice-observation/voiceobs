"use client";

import { Badge } from "@/components/primitives/badge";
import { Clock, Phone, Brain, CheckCircle2, XCircle, AlertTriangle } from "lucide-react";
import type { ExecutionStatus } from "@/lib/types";

interface ExecutionStatusBadgeProps {
  status: ExecutionStatus;
  passed?: boolean;
}

const config: Record<
  string,
  {
    label: string;
    variant: "default" | "secondary" | "destructive" | "outline";
    icon: React.ElementType;
    className?: string;
  }
> = {
  pending: { label: "Queued", variant: "secondary", icon: Clock },
  queued: { label: "In Queue", variant: "secondary", icon: Clock },
  calling: {
    label: "Calling",
    variant: "default",
    icon: Phone,
    className: "animate-pulse",
  },
  evaluating: {
    label: "Evaluating",
    variant: "default",
    icon: Brain,
    className: "animate-pulse",
  },
  completed_pass: {
    label: "Passed",
    variant: "default",
    icon: CheckCircle2,
    className: "bg-green-100 text-green-800",
  },
  completed_fail: { label: "Failed", variant: "destructive", icon: XCircle },
  failed: { label: "Error", variant: "destructive", icon: AlertTriangle },
};

export function ExecutionStatusBadge({ status, passed }: ExecutionStatusBadgeProps) {
  let key = status as string;
  if (status === "completed") {
    key = passed ? "completed_pass" : "completed_fail";
  }

  const { label, variant, icon: Icon, className } = config[key] ?? config.pending;

  return (
    <Badge variant={variant} className={className}>
      <Icon className="mr-1 h-3 w-3" />
      {label}
    </Badge>
  );
}
