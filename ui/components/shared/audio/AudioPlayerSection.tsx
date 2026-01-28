"use client";

import * as React from "react";
import type WaveSurfer from "wavesurfer.js";
import WaveSurferLib from "wavesurfer.js";
import {
  Play,
  Pause,
  Volume2,
  VolumeX,
  SkipBack,
  SkipForward,
  RotateCcw,
  RotateCw,
} from "lucide-react";
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

export interface TurnMarker {
  id: string;
  start: number;
  end: number;
  label?: string;
  color?: string;
  actor?: "user" | "agent";
}

export interface AudioPlayerSectionProps {
  audioUrl: string;
  conversationId?: string;
  turnMarkers?: TurnMarker[];
  className?: string;
  height?: number;
  waveColor?: string;
  progressColor?: string;
  cursorColor?: string;
  showControls?: boolean;
  showTimeDisplay?: boolean;
  showSpeedControl?: boolean;
  showVolumeControl?: boolean;
  showSkipControls?: boolean;
  showLoopControls?: boolean;
  skipSeconds?: number;
  onReady?: (wavesurfer: WaveSurfer) => void;
  onPlay?: () => void;
  onPause?: () => void;
  onTimeUpdate?: (currentTime: number) => void;
  onFinish?: () => void;
  onError?: (error: Error) => void;
  onTurnClick?: (turn: TurnMarker) => void;
}

export function AudioPlayerSection({
  audioUrl,
  conversationId,
  turnMarkers = [],
  className,
  height = 120,
  waveColor = "hsl(var(--muted-foreground))",
  progressColor = "hsl(var(--primary))",
  cursorColor = "hsl(var(--primary))",
  showControls = true,
  showTimeDisplay = true,
  showSpeedControl = true,
  showVolumeControl = true,
  showSkipControls = true,
  showLoopControls = true,
  skipSeconds = 5,
  onReady,
  onPlay,
  onPause,
  onTimeUpdate,
  onFinish,
  onError,
  onTurnClick,
}: AudioPlayerSectionProps) {
  const [isPlaying, setIsPlaying] = React.useState(false);
  const [currentTime, setCurrentTime] = React.useState(0);
  const [duration, setDuration] = React.useState(0);
  const [volume, setVolume] = React.useState(1);
  const [isMuted, setIsMuted] = React.useState(false);
  const [playbackSpeed, setPlaybackSpeed] = React.useState<PlaybackSpeed>(1);
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [waveformData, setWaveformData] = React.useState<number[]>([]);
  const [loopStart, setLoopStart] = React.useState<number | null>(null);
  const [loopEnd, setLoopEnd] = React.useState<number | null>(null);
  const [isLooping, setIsLooping] = React.useState(false);
  const containerRef = React.useRef<HTMLDivElement>(null);
  const wavesurferRef = React.useRef<WaveSurfer | null>(null);

  // Convert turn markers to segments for visualization
  const segments = React.useMemo(() => {
    return turnMarkers.map((turn) => ({
      id: turn.id,
      start: turn.start,
      end: turn.end,
      color:
        turn.color || (turn.actor === "user" ? "hsl(var(--blue-500))" : "hsl(var(--green-500))"),
      label: turn.label,
    }));
  }, [turnMarkers]);

  // Initialize WaveSurfer
  React.useEffect(() => {
    if (!containerRef.current) return;

    const wavesurfer = WaveSurferLib.create({
      container: containerRef.current,
      waveColor,
      progressColor,
      cursorColor,
      height: height - 40, // Reserve space for turn markers
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

    // Get waveform data for visualization
    wavesurfer.on("ready", () => {
      const duration = wavesurfer.getDuration();
      setDuration(duration);
      // Extract waveform data if available
      const peaks = wavesurfer.getDecodedData();
      if (peaks) {
        // Downsample peaks for visualization
        const samples = peaks.getChannelData(0);
        const sampleRate = peaks.sampleRate;
        const samplesPerPixel = Math.floor((samples.length / duration) * 2);
        const downsampled: number[] = [];
        for (let i = 0; i < samples.length; i += samplesPerPixel) {
          const chunk = samples.slice(i, i + samplesPerPixel);
          const max = Math.max(...chunk.map(Math.abs));
          downsampled.push(max);
        }
        setWaveformData(downsampled);
      }
    });

    // Event handlers
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

      // Handle looping
      if (isLooping && loopStart !== null && loopEnd !== null) {
        if (time >= loopEnd) {
          wavesurfer.seekTo(loopStart / duration);
        }
      }
    });

    wavesurfer.on("finish", () => {
      if (isLooping && loopStart !== null && loopEnd !== null) {
        wavesurfer.seekTo(loopStart / duration);
        wavesurfer.play();
      } else {
        setIsPlaying(false);
        setCurrentTime(0);
        onFinish?.();
      }
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
  }, [audioUrl, height, waveColor, progressColor, cursorColor, isLooping, loopStart, loopEnd]);

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

  const handleSeek = (time: number) => {
    if (!wavesurferRef.current || duration === 0) return;
    wavesurferRef.current.seekTo(time / duration);
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

  const handleSetLoopStart = () => {
    setLoopStart(currentTime);
    if (loopEnd === null || currentTime < loopEnd) {
      setIsLooping(true);
    }
  };

  const handleSetLoopEnd = () => {
    setLoopEnd(currentTime);
    if (loopStart === null || currentTime > loopStart) {
      setIsLooping(true);
    }
  };

  const handleClearLoop = () => {
    setLoopStart(null);
    setLoopEnd(null);
    setIsLooping(false);
  };

  const handleToggleLoop = () => {
    if (loopStart !== null && loopEnd !== null) {
      setIsLooping(!isLooping);
    }
  };

  // Find current turn based on current time
  const currentTurn = React.useMemo(() => {
    return turnMarkers.find((turn) => currentTime >= turn.start && currentTime <= turn.end);
  }, [turnMarkers, currentTime]);

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
      {/* Waveform with turn markers */}
      <div className="relative min-h-[100px] w-full rounded-md border border-border bg-card p-3">
        {/* Turn markers overlay */}
        {turnMarkers.length > 0 && (
          <div className="absolute left-0 right-0 top-0 z-10 flex h-6 items-center gap-1 px-3">
            {turnMarkers.map((turn) => {
              const width = duration > 0 ? ((turn.end - turn.start) / duration) * 100 : 0;
              const left = duration > 0 ? (turn.start / duration) * 100 : 0;
              const isActive = currentTime >= turn.start && currentTime <= turn.end;
              return (
                <button
                  key={turn.id}
                  onClick={() => {
                    handleSeek(turn.start);
                    onTurnClick?.(turn);
                  }}
                  className={cn(
                    "h-4 rounded text-[10px] font-medium transition-all hover:opacity-80",
                    isActive
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-muted-foreground opacity-60",
                    turn.actor === "user" && "border-l-2 border-blue-500",
                    turn.actor === "agent" && "border-l-2 border-green-500"
                  )}
                  style={{
                    width: `${width}%`,
                    marginLeft: turnMarkers.indexOf(turn) === 0 ? `${left}%` : "0",
                  }}
                  title={turn.label || `Turn ${turn.id}`}
                >
                  {turn.label || turn.id}
                </button>
              );
            })}
          </div>
        )}

        {/* Waveform container */}
        <div ref={containerRef} className="mt-6 w-full" />

        {/* Segment highlights overlay */}
        {segments.length > 0 && duration > 0 && (
          <div
            className="pointer-events-none absolute bottom-3 left-3 right-3"
            style={{ height: `${height - 60}px` }}
          >
            {segments.map((segment) => {
              const startPercent = (segment.start / duration) * 100;
              const widthPercent = ((segment.end - segment.start) / duration) * 100;
              const isActive = currentTime >= segment.start && currentTime <= segment.end;
              return (
                <div
                  key={segment.id}
                  className="absolute bottom-0 top-0 border-l border-r opacity-20 transition-opacity"
                  style={{
                    left: `${startPercent}%`,
                    width: `${widthPercent}%`,
                    backgroundColor: segment.color || "hsl(var(--accent))",
                    opacity: isActive ? 0.3 : 0.1,
                  }}
                />
              );
            })}
          </div>
        )}

        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center rounded-md bg-card/80 text-sm text-muted-foreground">
            Loading audio...
          </div>
        )}

        {/* Loop region indicator */}
        {loopStart !== null && loopEnd !== null && (
          <div
            className="absolute bottom-0 left-0 right-0 h-1 border-t-2 border-primary bg-primary/30"
            style={{
              left: `${(loopStart / duration) * 100}%`,
              width: `${((loopEnd - loopStart) / duration) * 100}%`,
            }}
          />
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

          {/* Loop Controls */}
          {showLoopControls && (
            <div className="flex items-center gap-1 rounded-md border p-1">
              <Button
                onClick={handleSetLoopStart}
                variant="ghost"
                size="sm"
                className="h-7 px-2 text-xs"
                title="Set loop start"
              >
                <RotateCcw className="mr-1 h-3 w-3" />
                Start
              </Button>
              <Button
                onClick={handleSetLoopEnd}
                variant="ghost"
                size="sm"
                className="h-7 px-2 text-xs"
                title="Set loop end"
              >
                <RotateCw className="mr-1 h-3 w-3" />
                End
              </Button>
              <Button
                onClick={handleToggleLoop}
                variant={isLooping ? "default" : "ghost"}
                size="sm"
                className="h-7 px-2 text-xs"
                disabled={loopStart === null || loopEnd === null}
                title="Toggle loop"
              >
                Loop
              </Button>
              {(loopStart !== null || loopEnd !== null) && (
                <Button
                  onClick={handleClearLoop}
                  variant="ghost"
                  size="sm"
                  className="h-7 px-2 text-xs"
                  title="Clear loop"
                >
                  Clear
                </Button>
              )}
            </div>
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
              {currentTurn && (
                <span className="ml-2 text-xs">
                  ({currentTurn.label || `Turn ${currentTurn.id}`})
                </span>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
