"use client";

import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";
import { CheckCircle2, XCircle, AlertTriangle, Clock } from "lucide-react";

const statusBadgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      status: {
        passed: "border-success/20 bg-success/10 text-success",
        failed: "border-destructive/20 bg-destructive/10 text-destructive",
        warning: "border-warning/20 bg-warning/10 text-warning",
        pending: "border-muted-foreground/20 bg-muted text-muted-foreground",
      },
      size: {
        sm: "px-2 py-0.5 text-xs",
        md: "px-2.5 py-0.5 text-xs",
        lg: "px-3 py-1 text-sm",
      },
    },
    defaultVariants: {
      status: "pending",
      size: "md",
    },
  }
);

export interface StatusBadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof statusBadgeVariants> {
  showIcon?: boolean;
}

const statusIcons = {
  passed: CheckCircle2,
  failed: XCircle,
  warning: AlertTriangle,
  pending: Clock,
};

export function StatusBadge({
  className,
  status = "pending",
  size = "md",
  showIcon = true,
  children,
  ...props
}: StatusBadgeProps) {
  const Icon = status ? statusIcons[status] : null;

  return (
    <div className={cn(statusBadgeVariants({ status, size }), className)} {...props}>
      {showIcon && Icon && <Icon className="h-3 w-3" />}
      {children}
    </div>
  );
}
