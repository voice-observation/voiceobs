"use client";

import { useState, useEffect, useRef } from "react";
import { Card, CardContent, CardHeader } from "@/components/primitives/card";
import { AudioPlayer } from "@/components/shared/audio/AudioPlayer";
import { TranscriptViewer } from "./TranscriptViewer";
import { EvaluationResultCard } from "./EvaluationResultCard";
import { AlertCircle } from "lucide-react";
import { api, getAuthHeaders } from "@/lib/api";
import type { ExecutionSummary } from "@/lib/types";

interface ExecutionDetailPanelProps {
  orgId: string;
  execution: ExecutionSummary;
  className?: string;
}

export function ExecutionDetailPanel({ orgId, execution, className }: ExecutionDetailPanelProps) {
  const [audioUrl, setAudioUrl] = useState<string | null>(() => {
    const url = execution.audio_url;
    if (!url) return null;
    if (url.startsWith("http://") || url.startsWith("https://")) return url;
    return null;
  });
  const [audioError, setAudioError] = useState<string | null>(null);
  const blobUrlRef = useRef<string | null>(null);

  // If audio_url is not a full URL, fetch stream URL and load audio (with auth for same-origin)
  useEffect(() => {
    if (!execution.audio_url) return;
    if (execution.audio_url.startsWith("http://") || execution.audio_url.startsWith("https://")) {
      setAudioUrl(execution.audio_url);
      return;
    }
    let cancelled = false;

    Promise.all([api.suiteRuns.getExecutionAudioUrl(orgId, execution.id), getAuthHeaders()])
      .then(async ([res, authHeaders]) => {
        if (cancelled || !res?.url) return;

        const streamUrl = res.url;
        const isSameOrigin =
          streamUrl.startsWith("/api") ||
          streamUrl.startsWith("/") ||
          (typeof window !== "undefined" &&
            new URL(streamUrl, window.location.origin).origin === window.location.origin);

        if (isSameOrigin && Object.keys(authHeaders).length > 0) {
          // Fetch with auth and create blob URL - WaveSurfer loads blob URLs without auth
          const fullUrl =
            typeof window !== "undefined"
              ? new URL(streamUrl, window.location.origin).href
              : streamUrl;
          const response = await fetch(fullUrl, { headers: authHeaders });
          if (cancelled) return;
          if (!response.ok) {
            setAudioError("Failed to load audio");
            return;
          }
          const blob = await response.blob();
          if (cancelled) return;
          const blobUrl = URL.createObjectURL(blob);
          blobUrlRef.current = blobUrl;
          setAudioUrl(blobUrl);
        } else {
          setAudioUrl(streamUrl);
        }
      })
      .catch(() => {
        if (!cancelled) setAudioError("Failed to load audio");
      });

    return () => {
      cancelled = true;
      if (blobUrlRef.current) {
        URL.revokeObjectURL(blobUrlRef.current);
        blobUrlRef.current = null;
      }
    };
  }, [orgId, execution.id, execution.audio_url]);

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <h3 className="font-semibold">
            {execution.scenario_name ?? `Execution ${execution.id.slice(0, 8)}`}
          </h3>
          <span className="text-xs text-muted-foreground">
            Attempt {execution.attempt} of {execution.max_attempts}
          </span>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {execution.error_message && (
          <div className="flex items-start gap-2 rounded-lg border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <p>{execution.error_message}</p>
          </div>
        )}

        {audioUrl && !audioError && (
          <div>
            <h4 className="mb-2 text-sm font-medium">Recording</h4>
            <AudioPlayer audioUrl={audioUrl} />
          </div>
        )}
        {audioError && <p className="text-sm text-muted-foreground">{audioError}</p>}

        <div>
          <h4 className="mb-2 text-sm font-medium">Transcript</h4>
          <TranscriptViewer transcript={execution.transcript} />
        </div>

        <div>
          <h4 className="mb-2 text-sm font-medium">Evaluation</h4>
          <EvaluationResultCard result={execution.evaluation_result} />
        </div>
      </CardContent>
    </Card>
  );
}
