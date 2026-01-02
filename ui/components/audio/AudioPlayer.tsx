"use client";

import { useState, useRef } from "react";
import type WaveSurfer from "wavesurfer.js";
import { Play, Pause, Volume2, VolumeX } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Waveform } from "./Waveform";
import { formatTime, type PlaybackSpeed, PLAYBACK_SPEEDS } from "@/lib/audio";
import { cn } from "@/lib/utils";

export interface AudioPlayerProps {
  audioUrl: string;
  conversationId: string;
  className?: string;
}

export function AudioPlayer({ audioUrl, conversationId, className }: AudioPlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState<PlaybackSpeed>(1);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const wavesurferRef = useRef<WaveSurfer | null>(null);

  const handleReady = (wavesurfer: WaveSurfer) => {
    wavesurferRef.current = wavesurfer;
    setDuration(wavesurfer.getDuration());
    setIsLoading(false);
    setError(null);
  };

  const handleError = (err: Error) => {
    setIsLoading(false);
    setError("Audio not found");
  };

  const handlePlay = () => {
    setIsPlaying(true);
  };

  const handlePause = () => {
    setIsPlaying(false);
  };

  const handleTimeUpdate = (time: number) => {
    setCurrentTime(time);
  };

  const handleFinish = () => {
    setIsPlaying(false);
    setCurrentTime(0);
  };

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

  if (error) {
    return (
      <div className={cn("space-y-4", className)}>
        <div className="w-full rounded-md border border-border bg-card p-6 min-h-[100px] flex items-center justify-center">
          <p className="text-muted-foreground">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className={cn("space-y-4", className)}>
      {/* Waveform */}
      <div className="w-full rounded-md border border-border bg-card p-3 min-h-[100px] relative">
        <Waveform
          audioUrl={audioUrl}
          onReady={handleReady}
          onPlay={handlePlay}
          onPause={handlePause}
          onTimeUpdate={handleTimeUpdate}
          onFinish={handleFinish}
          onError={handleError}
          playbackRate={playbackSpeed}
          volume={isMuted ? 0 : volume}
          height={100}
        />
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-card/80 text-muted-foreground text-sm rounded-md">
            Loading audio...
          </div>
        )}
      </div>

      {/* Controls */}
      <div className="flex items-center gap-4 flex-wrap">
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

        {/* Volume Control */}
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
            className="w-24 h-2 bg-muted rounded-lg appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-primary [&::-webkit-slider-thumb]:cursor-pointer [&::-moz-range-thumb]:h-3 [&::-moz-range-thumb]:w-3 [&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:bg-primary [&::-moz-range-thumb]:border-0 [&::-moz-range-thumb]:cursor-pointer"
            style={{
              background: `linear-gradient(to right, hsl(var(--primary)) 0%, hsl(var(--primary)) ${(isMuted ? 0 : volume) * 100}%, hsl(var(--muted)) ${(isMuted ? 0 : volume) * 100}%, hsl(var(--muted)) 100%)`,
            }}
            aria-label="Volume"
          />
        </div>

        {/* Playback Speed */}
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

        {/* Time Display */}
        <div className="flex items-center gap-1 text-sm text-muted-foreground ml-auto">
          <span>{formatTime(currentTime)}</span>
          <span>/</span>
          <span>{formatTime(duration)}</span>
        </div>
      </div>
    </div>
  );
}
