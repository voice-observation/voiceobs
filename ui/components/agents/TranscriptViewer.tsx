"use client";

import { useState } from "react";
import { MessageSquare, ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

interface TranscriptMessage {
  role: string;
  content: string;
}

interface TranscriptViewerProps {
  messages: TranscriptMessage[];
  title?: string;
  maxHeight?: string;
  defaultExpanded?: boolean;
}

function MessageBubble({ message }: { message: TranscriptMessage }) {
  const isAgent = message.role === "assistant";
  const displayRole = isAgent ? "Agent" : "System";

  return (
    <div className={cn("flex flex-col", isAgent ? "items-end" : "items-start")}>
      <span className="mb-1 px-1 text-xs text-muted-foreground">{displayRole}</span>
      <div
        className={cn(
          "max-w-[65%] px-3 py-2 text-sm",
          isAgent ? "rounded-lg rounded-tr-sm bg-primary/10" : "rounded-lg rounded-tl-sm bg-muted"
        )}
      >
        {message.content}
      </div>
    </div>
  );
}

export function TranscriptViewer({
  messages,
  title = "Transcript",
  maxHeight = "24rem",
  defaultExpanded = false,
}: TranscriptViewerProps) {
  const [expanded, setExpanded] = useState(defaultExpanded);

  if (!messages || messages.length === 0) {
    return null;
  }

  return (
    <div className="overflow-hidden">
      {/* Clickable Header */}
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between p-4 transition-colors hover:bg-muted/50"
      >
        <div className="flex items-center gap-2">
          <MessageSquare className="h-4 w-4" />
          <span className="font-medium">{title}</span>
          <span className="text-sm text-muted-foreground">{messages.length} messages</span>
        </div>
        <div className="flex items-center gap-1 text-sm text-muted-foreground">
          {expanded ? "Collapse" : "Expand"}
          <ChevronDown className={cn("h-4 w-4 transition-transform", expanded && "rotate-180")} />
        </div>
      </button>

      {/* Collapsible Content */}
      {expanded && (
        <div className="space-y-4 overflow-y-auto border-t px-6 py-4" style={{ maxHeight }}>
          {messages.map((message, index) => (
            <MessageBubble key={index} message={message} />
          ))}
        </div>
      )}
    </div>
  );
}
