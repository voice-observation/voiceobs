"use client";

import { cn } from "@/lib/utils";
import type { TranscriptEntry } from "@/lib/types";

interface TranscriptViewerProps {
  transcript: TranscriptEntry[] | null;
  className?: string;
}

function formatTimestamp(ms: number): string {
  const totalSeconds = Math.floor(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

export function TranscriptViewer({ transcript, className }: TranscriptViewerProps) {
  if (!transcript || transcript.length === 0) {
    return (
      <div className={cn("py-4 text-center text-sm text-muted-foreground", className)}>
        No transcript available
      </div>
    );
  }

  return (
    <div className={cn("space-y-3", className)}>
      {transcript.map((entry, i) => {
        const isAgent = entry.role === "agent";
        return (
          <div
            key={i}
            className={cn("flex gap-3 text-sm", isAgent ? "flex-row" : "flex-row-reverse")}
          >
            <div
              className={cn(
                "max-w-[75%] rounded-lg px-3 py-2",
                isAgent ? "bg-muted text-foreground" : "bg-primary text-primary-foreground"
              )}
            >
              <div className="mb-1 flex items-center gap-2">
                <span className="text-xs font-semibold">{isAgent ? "Agent" : "Caller"}</span>
                <span className="text-xs opacity-70">{formatTimestamp(entry.timestamp_ms)}</span>
              </div>
              <p>{entry.text}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
