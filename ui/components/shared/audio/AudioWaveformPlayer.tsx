"use client";

import * as React from "react";
import type WaveSurfer from "wavesurfer.js";
import WaveSurferLib from "wavesurfer.js";
import { Play, Pause, Volume2, VolumeX, SkipBack, SkipForward } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import { formatTime, type PlaybackSpeed, PLAYBACK_SPEEDS } from "@/lib/audio";

export interface AudioWaveformPlayerProps {
  audioUrl: string;
  className?: string;
  height?: number;
  waveColor?: string;
  progressColor?: string;
  cursorColor?: string;
  onReady?: (wavesurfer: WaveSurfer) => void;
  onPlay?: () => void;
  onPause?: () => void;
  onTimeUpdate?: (currentTime: number) => void;
  onFinish?: () => void;
  onError?: (error: Error) => void;
  showControls?: boolean;
  showTimeDisplay?: boolean;
  showSpeedControl?: boolean;
  showVolumeControl?: boolean;
  showSkipControls?: boolean;
  skipSeconds?: number;
}

export function AudioWaveformPlayer({
  audioUrl,
  className,
  height = 100,
  waveColor = "hsl(var(--muted-foreground))",
  progressColor = "hsl(var(--primary))",
  cursorColor = "hsl(var(--primary))",
  onReady,
  onPlay,
  onPause,
  onTimeUpdate,
  onFinish,
  onError,
  showControls = true,
  showTimeDisplay = true,
  showSpeedControl = true,
  showVolumeControl = true,
  showSkipControls = true,
  skipSeconds = 5,
}: AudioWaveformPlayerProps) {
  const [isPlaying, setIsPlaying] = React.useState(false);
  const [currentTime, setCurrentTime] = React.useState(0);
  const [duration, setDuration] = React.useState(0);
  const [volume, setVolume] = React.useState(1);
  const [isMuted, setIsMuted] = React.useState(false);
  const [playbackSpeed, setPlaybackSpeed] = React.useState<PlaybackSpeed>(1);
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const containerRef = React.useRef<HTMLDivElement>(null);
  const wavesurferRef = React.useRef<WaveSurfer | null>(null);

  // Initialize WaveSurfer
  React.useEffect(() => {
    if (!containerRef.current) return;

    const wavesurfer = WaveSurferLib.create({
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
    });

    wavesurferRef.current = wavesurfer;

    // Set initial playback rate and volume
    // Note: These are also updated in separate effects when they change
    wavesurfer.setPlaybackRate(playbackSpeed);
    wavesurfer.setVolume(volume);

    // Load audio
    wavesurfer
      .load(audioUrl)
      .then(() => {
        setIsLoading(false);
        setError(null);
        onReady?.(wavesurfer);
      })
      .catch((err) => {
        setIsLoading(false);
        setError("Failed to load audio");
        onError?.(err instanceof Error ? err : new Error(String(err)));
      });

    // Event handlers
    wavesurfer.on("ready", () => {
      setDuration(wavesurfer.getDuration());
    });

    wavesurfer.on("play", () => {
      setIsPlaying(true);
      onPlay?.();
    });

    wavesurfer.on("pause", () => {
      setIsPlaying(false);
      onPause?.();
    });

    wavesurfer.on("timeupdate", (time) => {
      setCurrentTime(time);
      onTimeUpdate?.(time);
    });

    wavesurfer.on("finish", () => {
      setIsPlaying(false);
      setCurrentTime(0);
      onFinish?.();
    });

    wavesurfer.on("error", (err) => {
      setIsLoading(false);
      setError("Audio playback error");
      onError?.(err instanceof Error ? err : new Error(String(err)));
    });

    // Cleanup
    return () => {
      wavesurfer.destroy();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [audioUrl, height, waveColor, progressColor, cursorColor]);

  // Update playback rate when it changes
  React.useEffect(() => {
    if (wavesurferRef.current) {
      wavesurferRef.current.setPlaybackRate(playbackSpeed);
    }
  }, [playbackSpeed]);

  // Update volume when it changes
  React.useEffect(() => {
    if (wavesurferRef.current) {
      wavesurferRef.current.setVolume(isMuted ? 0 : volume);
    }
  }, [volume, isMuted]);

  const togglePlayPause = () => {
    if (!wavesurferRef.current) return;
    if (isPlaying) {
      wavesurferRef.current.pause();
    } else {
      wavesurferRef.current.play();
    }
  };

  const handleVolumeChange = (newVolume: number) => {
    setVolume(newVolume);
    setIsMuted(newVolume === 0);
    if (wavesurferRef.current) {
      wavesurferRef.current.setVolume(newVolume);
    }
  };

  const handleMuteToggle = () => {
    if (isMuted) {
      handleVolumeChange(0.5); // Restore to 50% when unmuting
    } else {
      handleVolumeChange(0);
    }
  };

  const handleSpeedChange = (speed: string) => {
    const newSpeed = parseFloat(speed) as PlaybackSpeed;
    setPlaybackSpeed(newSpeed);
    if (wavesurferRef.current) {
      wavesurferRef.current.setPlaybackRate(newSpeed);
    }
  };

  const handleSkipBackward = () => {
    if (!wavesurferRef.current) return;
    const newTime = Math.max(0, currentTime - skipSeconds);
    wavesurferRef.current.seekTo(newTime / duration);
  };

  const handleSkipForward = () => {
    if (!wavesurferRef.current) return;
    const newTime = Math.min(duration, currentTime + skipSeconds);
    wavesurferRef.current.seekTo(newTime / duration);
  };

  if (error) {
    return (
      <div className={cn("space-y-4", className)}>
        <div className="flex min-h-[100px] w-full items-center justify-center rounded-md border border-border bg-card p-6">
          <p className="text-muted-foreground">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className={cn("space-y-4", className)}>
      {/* Waveform */}
      <div className="relative min-h-[100px] w-full rounded-md border border-border bg-card p-3">
        <div ref={containerRef} className="w-full" />
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center rounded-md bg-card/80 text-sm text-muted-foreground">
            Loading audio...
          </div>
        )}
      </div>

      {/* Controls */}
      {showControls && (
        <div className="flex flex-wrap items-center gap-4">
          {/* Skip Backward */}
          {showSkipControls && (
            <Button
              onClick={handleSkipBackward}
              disabled={isLoading || currentTime === 0}
              variant="outline"
              size="icon"
              aria-label={`Skip backward ${skipSeconds}s`}
            >
              <SkipBack className="h-4 w-4" />
            </Button>
          )}

          {/* Play/Pause Button */}
          <Button
            onClick={togglePlayPause}
            disabled={isLoading}
            variant="outline"
            size="icon"
            aria-label={isPlaying ? "Pause" : "Play"}
          >
            {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
          </Button>

          {/* Skip Forward */}
          {showSkipControls && (
            <Button
              onClick={handleSkipForward}
              disabled={isLoading || currentTime >= duration}
              variant="outline"
              size="icon"
              aria-label={`Skip forward ${skipSeconds}s`}
            >
              <SkipForward className="h-4 w-4" />
            </Button>
          )}

          {/* Volume Control */}
          {showVolumeControl && (
            <div className="flex items-center gap-2">
              <Button
                onClick={handleMuteToggle}
                variant="ghost"
                size="icon"
                aria-label={isMuted ? "Unmute" : "Mute"}
                className="h-9 w-9"
              >
                {isMuted ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
              </Button>
              <input
                type="range"
                min="0"
                max="1"
                step="0.01"
                value={isMuted ? 0 : volume}
                onChange={(e) => handleVolumeChange(parseFloat(e.target.value))}
                className="h-2 w-24 cursor-pointer appearance-none rounded-lg bg-muted [&::-moz-range-thumb]:h-3 [&::-moz-range-thumb]:w-3 [&::-moz-range-thumb]:cursor-pointer [&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:border-0 [&::-moz-range-thumb]:bg-primary [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-primary"
                style={{
                  background: `linear-gradient(to right, hsl(var(--primary)) 0%, hsl(var(--primary)) ${(isMuted ? 0 : volume) * 100}%, hsl(var(--muted)) ${(isMuted ? 0 : volume) * 100}%, hsl(var(--muted)) 100%)`,
                }}
                aria-label="Volume"
              />
            </div>
          )}

          {/* Playback Speed */}
          {showSpeedControl && (
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">Speed:</span>
              <Select value={playbackSpeed.toString()} onValueChange={handleSpeedChange}>
                <SelectTrigger className="w-20">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {PLAYBACK_SPEEDS.map((speed) => (
                    <SelectItem key={speed} value={speed.toString()}>
                      {speed}x
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          {/* Time Display */}
          {showTimeDisplay && (
            <div className="ml-auto flex items-center gap-1 text-sm text-muted-foreground">
              <span>{formatTime(currentTime)}</span>
              <span>/</span>
              <span>{formatTime(duration)}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
