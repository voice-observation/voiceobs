"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { Card, CardContent } from "@/components/primitives/card";
import { Button } from "@/components/primitives/button";
import { Switch } from "@/components/primitives/switch";
import { Badge } from "@/components/primitives/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/primitives/dropdown-menu";
import {
  MoreHorizontal,
  Play,
  Star,
  Volume2,
  Loader2,
  RefreshCw,
  Pencil,
  Trash2,
} from "lucide-react";
import type { PersonaListItem } from "@/lib/types";
import { api } from "@/lib/api";

interface PersonaCardProps {
  orgId: string;
  persona: PersonaListItem;
  onToggleEnabled: (id: string, enabled: boolean) => void;
  onListenVoice: (id: string) => void;
  onSetDefault: (id: string) => void;
  onDelete: (persona: PersonaListItem) => void;
  playingPersonaId: string | null;
  onPlayingChange: (personaId: string | null) => void;
}

const POLL_INTERVAL_MS = 2000;
const POLL_TIMEOUT_MS = 60000;

export function PersonaCard({
  orgId,
  persona,
  onToggleEnabled,
  onListenVoice,
  onSetDefault,
  onDelete,
  playingPersonaId,
  onPlayingChange,
}: PersonaCardProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [previewStatus, setPreviewStatus] = useState<"generating" | "ready" | "failed" | null>(
    persona.preview_audio_status
  );
  const [audioUrl, setAudioUrl] = useState<string | null>(persona.preview_audio_url);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
      if (audioRef.current) {
        audioRef.current.pause();
      }
    };
  }, []);

  // Stop audio when another persona starts playing
  useEffect(() => {
    if (playingPersonaId !== null && playingPersonaId !== persona.id) {
      if (audioRef.current) {
        audioRef.current.pause();
      }
      setIsPlaying(false);
    }
  }, [playingPersonaId, persona.id]);

  const playAudio = (url: string) => {
    if (audioRef.current) {
      audioRef.current.pause();
    }
    const audio = new Audio(url);
    audioRef.current = audio;
    audio.onended = () => {
      setIsPlaying(false);
      onPlayingChange(null);
    };
    audio.onerror = () => {
      setIsPlaying(false);
      onPlayingChange(null);
    };
    audio.play().catch(() => {
      setIsPlaying(false);
      onPlayingChange(null);
    });
    setIsPlaying(true);
    onPlayingChange(persona.id);
  };

  const handleTryVoice = async () => {
    // If playing, stop
    if (isPlaying && audioRef.current) {
      audioRef.current.pause();
      setIsPlaying(false);
      onPlayingChange(null);
      return;
    }

    // If ready, play immediately
    if (previewStatus === "ready" && audioUrl) {
      playAudio(audioUrl);
      return;
    }

    // Start generation
    try {
      await api.personas.generatePersonaPreviewAudio(orgId, persona.id);
      setPreviewStatus("generating");

      // Start polling
      const startTime = Date.now();
      pollIntervalRef.current = setInterval(async () => {
        // Check timeout
        if (Date.now() - startTime > POLL_TIMEOUT_MS) {
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
          }
          setPreviewStatus("failed");
          return;
        }

        try {
          const result = await api.personas.getPreviewAudioStatus(orgId, persona.id);
          setPreviewStatus(result.status);

          if (result.status === "ready" && result.audio_url) {
            if (pollIntervalRef.current) {
              clearInterval(pollIntervalRef.current);
              pollIntervalRef.current = null;
            }
            setAudioUrl(result.audio_url);
            playAudio(result.audio_url);
          } else if (result.status === "failed") {
            if (pollIntervalRef.current) {
              clearInterval(pollIntervalRef.current);
              pollIntervalRef.current = null;
            }
          }
        } catch {
          // Continue polling on error
        }
      }, POLL_INTERVAL_MS);
    } catch {
      setPreviewStatus("failed");
    }
  };

  const getButtonContent = () => {
    if (isPlaying) {
      return (
        <>
          <Volume2 className="mr-1.5 h-4 w-4 animate-pulse" />
          Playing...
        </>
      );
    }

    switch (previewStatus) {
      case "generating":
        return (
          <>
            <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
            Generating...
          </>
        );
      case "failed":
        return (
          <>
            <RefreshCw className="mr-1.5 h-4 w-4" />
            Retry
          </>
        );
      default:
        return (
          <>
            <Play className="mr-1.5 h-4 w-4" />
            Try Voice
          </>
        );
    }
  };

  const isButtonDisabled = previewStatus === "generating";

  return (
    <Link href={`/personas/${persona.id}`} className="block" data-testid="persona-card">
      <Card className="relative cursor-pointer transition-colors hover:border-primary">
        <CardContent className="p-5">
          <div className="mb-3 flex items-start justify-between">
            <div className="flex-1 pr-4">
              <div className="mb-1 flex items-center gap-2">
                <h3
                  className="text-base font-semibold transition-colors hover:text-primary"
                  data-testid="persona-name"
                >
                  {persona.name}
                </h3>
                {persona.is_default && (
                  <Badge
                    variant="secondary"
                    className="flex items-center gap-1"
                    data-testid="default-badge"
                  >
                    <Star className="h-3 w-3" />
                    Default
                  </Badge>
                )}
                {persona.persona_type && (
                  <Badge variant="outline" data-testid="persona-type">
                    {persona.persona_type === "system" ? "System" : "Custom"}
                  </Badge>
                )}
              </div>
              <p className="line-clamp-2 text-sm text-muted-foreground">
                {persona.description || ""}
              </p>
            </div>
            <div className="flex items-center gap-2" onClick={(e) => e.preventDefault()}>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-8 w-8 p-0"
                    data-testid="persona-card-menu"
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                    }}
                  >
                    <MoreHorizontal className="h-4 w-4" />
                    <span className="sr-only">Open menu</span>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem asChild>
                    <Link
                      href={`/personas/${persona.id}/edit`}
                      onClick={(e) => e.stopPropagation()}
                    >
                      <Pencil className="mr-2 h-4 w-4" />
                      Edit
                    </Link>
                  </DropdownMenuItem>
                  {!persona.is_default && (
                    <DropdownMenuItem
                      data-testid="set-default-menu-item"
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        onSetDefault(persona.id);
                      }}
                    >
                      <Star className="mr-2 h-4 w-4" />
                      Set as Default
                    </DropdownMenuItem>
                  )}
                  <DropdownMenuItem
                    data-testid="delete-menu-item"
                    disabled={persona.persona_type === "system"}
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      if (persona.persona_type !== "system") {
                        onDelete(persona);
                      }
                    }}
                    className="text-destructive focus:text-destructive disabled:opacity-50"
                  >
                    <Trash2 className="mr-2 h-4 w-4" />
                    Delete
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
              <Switch
                data-testid="toggle-active-button"
                checked={persona.is_active}
                onCheckedChange={(checked) => onToggleEnabled(persona.id, checked)}
              />
            </div>
          </div>

          <div className="mt-4 space-y-2">
            {persona.traits.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {persona.traits.slice(0, 3).map((trait, idx) => (
                  <span
                    key={idx}
                    className="rounded-md bg-muted px-2 py-0.5 text-xs text-muted-foreground"
                  >
                    {trait}
                  </span>
                ))}
                {persona.traits.length > 3 && (
                  <span className="px-2 py-0.5 text-xs text-muted-foreground">
                    +{persona.traits.length - 3}
                  </span>
                )}
              </div>
            )}

            <div className="flex items-center justify-between pt-2">
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <div className="flex items-center gap-1">
                  <span>Aggression:</span>
                  <span className="font-medium">{persona.aggression.toFixed(1)}</span>
                </div>
                <div className="flex items-center gap-1">
                  <span>Patience:</span>
                  <span className="font-medium">{persona.patience.toFixed(1)}</span>
                </div>
                <div className="flex items-center gap-1">
                  <span>Verbosity:</span>
                  <span className="font-medium">{persona.verbosity.toFixed(1)}</span>
                </div>
              </div>

              <Button
                size="sm"
                variant="secondary"
                data-testid="preview-audio-button"
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  handleTryVoice();
                }}
                disabled={isButtonDisabled}
              >
                {getButtonContent()}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
