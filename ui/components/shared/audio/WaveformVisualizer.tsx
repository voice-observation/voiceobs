"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

export interface Segment {
  id: string;
  start: number;
  end: number;
  color?: string;
  label?: string;
}

export interface WaveformVisualizerProps {
  waveformData?: number[];
  duration: number;
  currentTime: number;
  segments?: Segment[];
  height?: number;
  waveColor?: string;
  progressColor?: string;
  cursorColor?: string;
  segmentColors?: Record<string, string>;
  className?: string;
  onSeek?: (time: number) => void;
}

export function WaveformVisualizer({
  waveformData,
  duration,
  currentTime,
  segments = [],
  height = 100,
  waveColor = "hsl(var(--muted-foreground))",
  progressColor = "hsl(var(--primary))",
  cursorColor = "hsl(var(--primary))",
  segmentColors = {},
  className,
  onSeek,
}: WaveformVisualizerProps) {
  const containerRef = React.useRef<HTMLDivElement>(null);
  const canvasRef = React.useRef<HTMLCanvasElement>(null);
  const [isDragging, setIsDragging] = React.useState(false);

  // Normalize waveform data if provided
  const normalizedData = React.useMemo(() => {
    if (!waveformData || waveformData.length === 0) {
      // Generate placeholder data
      return Array.from({ length: 200 }, () => Math.random() * 0.5 + 0.3);
    }
    const max = Math.max(...waveformData);
    return max > 0 ? waveformData.map((val) => val / max) : waveformData;
  }, [waveformData]);

  const drawWaveform = React.useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const width = canvas.width;
    const barWidth = 2;
    const barGap = 1;
    const totalBarWidth = barWidth + barGap;
    const barsCount = Math.floor(width / totalBarWidth);
    const progress = duration > 0 ? currentTime / duration : 0;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    // Draw segments background
    segments.forEach((segment) => {
      const startX = (segment.start / duration) * width;
      const endX = (segment.end / duration) * width;
      const color = segment.color || segmentColors[segment.id] || "hsl(var(--accent))";
      ctx.fillStyle = color + "20"; // 20% opacity
      ctx.fillRect(startX, 0, endX - startX, height);
    });

    // Draw waveform bars
    const dataPoints = normalizedData.slice(0, barsCount);
    dataPoints.forEach((amplitude, index) => {
      const x = index * totalBarWidth;
      const barHeight = amplitude * (height - 4); // Leave 2px padding top and bottom
      const y = (height - barHeight) / 2;

      // Determine color based on progress
      const barProgress = x / width;
      if (barProgress <= progress) {
        ctx.fillStyle = progressColor;
      } else {
        ctx.fillStyle = waveColor;
      }

      ctx.fillRect(x, y, barWidth, barHeight);
    });

    // Draw playhead indicator
    if (duration > 0) {
      const playheadX = progress * width;
      ctx.strokeStyle = cursorColor;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(playheadX, 0);
      ctx.lineTo(playheadX, height);
      ctx.stroke();
    }

    // Draw segment boundaries
    segments.forEach((segment) => {
      const startX = (segment.start / duration) * width;
      const endX = (segment.end / duration) * width;
      const color = segment.color || segmentColors[segment.id] || "hsl(var(--accent))";

      // Start boundary
      ctx.strokeStyle = color;
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(startX, 0);
      ctx.lineTo(startX, height);
      ctx.stroke();

      // End boundary
      ctx.beginPath();
      ctx.moveTo(endX, 0);
      ctx.lineTo(endX, height);
      ctx.stroke();
    });
  }, [
    normalizedData,
    duration,
    currentTime,
    segments,
    height,
    waveColor,
    progressColor,
    cursorColor,
    segmentColors,
  ]);

  // Handle resize
  React.useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width } = entry.contentRect;
        canvas.width = width * window.devicePixelRatio;
        canvas.height = height * window.devicePixelRatio;
        canvas.style.width = `${width}px`;
        canvas.style.height = `${height}px`;
        const ctx = canvas.getContext("2d");
        if (ctx) {
          ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
        }
        drawWaveform();
      }
    });

    resizeObserver.observe(container);

    // Initial size
    const width = container.clientWidth;
    canvas.width = width * window.devicePixelRatio;
    canvas.height = height * window.devicePixelRatio;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    const ctx = canvas.getContext("2d");
    if (ctx) {
      ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
    }
    drawWaveform();

    return () => {
      resizeObserver.disconnect();
    };
  }, [height, drawWaveform]);

  // Redraw when data changes
  React.useEffect(() => {
    drawWaveform();
  }, [drawWaveform]);

  const handleClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!onSeek || duration === 0) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const progress = x / rect.width;
    const time = Math.max(0, Math.min(duration, progress * duration));
    onSeek(time);
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    setIsDragging(true);
    handleClick(e);
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (isDragging) {
      handleClick(e);
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  React.useEffect(() => {
    if (isDragging) {
      const handleGlobalMouseMove = (e: MouseEvent) => {
        if (!onSeek || duration === 0) return;
        const canvas = canvasRef.current;
        if (!canvas) return;
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const progress = Math.max(0, Math.min(1, x / rect.width));
        const time = progress * duration;
        onSeek(time);
      };

      const handleGlobalMouseUp = () => {
        setIsDragging(false);
      };

      window.addEventListener("mousemove", handleGlobalMouseMove);
      window.addEventListener("mouseup", handleGlobalMouseUp);

      return () => {
        window.removeEventListener("mousemove", handleGlobalMouseMove);
        window.removeEventListener("mouseup", handleGlobalMouseUp);
      };
    }
  }, [isDragging, onSeek, duration]);

  return (
    <div
      ref={containerRef}
      className={cn("relative w-full", className)}
      style={{ height: `${height}px` }}
    >
      <canvas
        ref={canvasRef}
        onClick={handleClick}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        className="h-full w-full cursor-pointer"
      />
    </div>
  );
}
