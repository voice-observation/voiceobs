"use client";

import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

interface CheckboxCardProps {
  label: string;
  checked: boolean;
  onCheckedChange: () => void;
  className?: string;
}

export function CheckboxCard({ label, checked, onCheckedChange, className }: CheckboxCardProps) {
  return (
    <div
      className={cn(
        "flex cursor-pointer items-center gap-2 rounded-md border px-3 py-2 transition-colors",
        checked ? "border-primary bg-primary/5" : "border-border hover:bg-muted/50",
        className
      )}
      onClick={onCheckedChange}
    >
      <div
        className={cn(
          "flex h-4 w-4 shrink-0 items-center justify-center rounded border border-primary transition-colors",
          checked && "bg-primary text-primary-foreground"
        )}
      >
        {checked && <Check className="h-3.5 w-3.5 stroke-[3]" />}
      </div>
      <span className="text-sm font-medium">{label}</span>
    </div>
  );
}
