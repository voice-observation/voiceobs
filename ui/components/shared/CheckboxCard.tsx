"use client";

import { Checkbox } from "@/components/ui/checkbox";
import { cn } from "@/lib/utils";

interface CheckboxCardProps {
  label: string;
  checked: boolean;
  onCheckedChange: () => void;
  className?: string;
}

export function CheckboxCard({
  label,
  checked,
  onCheckedChange,
  className,
}: CheckboxCardProps) {
  return (
    <div
      className={cn(
        "flex items-center gap-2 px-3 py-2 rounded-md border cursor-pointer transition-colors",
        checked
          ? "border-primary bg-primary/5"
          : "border-border hover:bg-muted/50",
        className
      )}
      onClick={onCheckedChange}
    >
      <Checkbox checked={checked} onCheckedChange={onCheckedChange} />
      <span className="text-sm font-medium">{label}</span>
    </div>
  );
}
