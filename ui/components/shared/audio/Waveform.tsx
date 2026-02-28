"use client";

import { useEffect, useRef } from "react";
import WaveSurfer from "wavesurfer.js";
import { cn } from "@/lib/utils";

export interface WaveformProps {
  audioUrl: string;
  /** Optional fetch params (e.g. auth headers) for same-origin protected URLs */
  fetchParams?: RequestInit;
  onReady?: (wavesurfer: WaveSurfer) => void;
  onPlay?: () => void;
  onPause?: () => void;
  onTimeUpdate?: (currentTime: number) => void;
  onFinish?: () => void;
  onError?: (error: Error) => void;
  className?: string;
  height?: number;
  waveColor?: string;
  progressColor?: string;
  cursorColor?: string;
  playbackRate?: number;
  volume?: number;
}

export function Waveform({
  audioUrl,
  fetchParams,
  onReady,
  onPlay,
  onPause,
  onTimeUpdate,
  onFinish,
  onError,
  className,
  height = 100,
  waveColor = "hsl(var(--muted-foreground))",
  progressColor = "hsl(var(--primary))",
  cursorColor = "hsl(var(--primary))",
  playbackRate = 1,
  volume = 1,
}: WaveformProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const wavesurferRef = useRef<WaveSurfer | null>(null);
  const fetchParamsRef = useRef(fetchParams);
  fetchParamsRef.current = fetchParams;

  useEffect(() => {
    if (!containerRef.current) return;

    // Initialize WaveSurfer
    const wavesurfer = WaveSurfer.create({
      container: containerRef.current,
      waveColor,
      progressColor,
      cursorColor,
      height,
      normalize: true,
      barWidth: 2,
      barRadius: 2,
      barGap: 1,
      interact: true,
      ...(fetchParamsRef.current && { fetchParams: fetchParamsRef.current }),
    });

    wavesurferRef.current = wavesurfer;

    // Set playback rate and volume
    wavesurfer.setPlaybackRate(playbackRate);
    wavesurfer.setVolume(volume);

    // Load audio
    wavesurfer.load(audioUrl).catch((error) => {
      // AbortError = component unmounted/remounted (e.g. React Strict Mode) - not a real load failure
      if (error?.name !== "AbortError") onError?.(error);
    });

    // Event handlers
    wavesurfer.on("ready", () => {
      onReady?.(wavesurfer);
    });

    wavesurfer.on("play", () => {
      onPlay?.();
    });

    wavesurfer.on("pause", () => {
      onPause?.();
    });

    wavesurfer.on("timeupdate", (currentTime) => {
      onTimeUpdate?.(currentTime);
    });

    wavesurfer.on("finish", () => {
      onFinish?.();
    });

    wavesurfer.on("error", (error) => {
      // AbortError = component unmounted/remounted (e.g. React Strict Mode) - not a real load failure
      if (error?.name !== "AbortError") onError?.(error);
    });

    // Cleanup
    return () => {
      wavesurfer.destroy();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [audioUrl]); // Only recreate on URL change; fetchParams via ref to avoid Strict Mode re-runs

  // Update playback rate when it changes
  useEffect(() => {
    if (wavesurferRef.current) {
      wavesurferRef.current.setPlaybackRate(playbackRate);
    }
  }, [playbackRate]);

  // Update volume when it changes
  useEffect(() => {
    if (wavesurferRef.current) {
      wavesurferRef.current.setVolume(volume);
    }
  }, [volume]);

  return <div ref={containerRef} className={cn("w-full", className)} />;
}
