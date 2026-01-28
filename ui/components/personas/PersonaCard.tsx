"use client";

import { useState } from "react";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Play, Volume2 } from "lucide-react";
import type { PersonaListItem } from "@/lib/types";

interface PersonaCardProps {
  persona: PersonaListItem;
  onToggleEnabled: (id: string, enabled: boolean) => void;
  onListenVoice: (id: string) => void;
}

export function PersonaCard({ persona, onToggleEnabled, onListenVoice }: PersonaCardProps) {
  const [isPlaying, setIsPlaying] = useState(false);

  const handleListen = async () => {
    if (isPlaying) {
      // If already playing, stop it
      setIsPlaying(false);
      return;
    }

    setIsPlaying(true);
    try {
      await onListenVoice(persona.id);
      // Reset playing state after a reasonable delay
      // In a production app, you'd listen to audio events
      setTimeout(() => setIsPlaying(false), 10000);
    } catch (err) {
      console.error("Failed to play audio:", err);
      setIsPlaying(false);
    }
  };

  const hasPreviewAudio = !!persona.preview_audio_url;

  return (
    <Link href={`/personas/${persona.id}`} className="block">
      <Card className="relative cursor-pointer transition-colors hover:border-primary">
        <CardContent className="p-5">
          <div className="mb-3 flex items-start justify-between">
            <div className="flex-1 pr-4">
              <h3 className="mb-1 text-base font-semibold transition-colors hover:text-primary">
                {persona.name}
              </h3>
              <p className="line-clamp-2 text-sm text-muted-foreground">
                {persona.description || ""}
              </p>
            </div>
            <div onClick={(e) => e.preventDefault()}>
              <Switch
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
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  handleListen();
                }}
                disabled={!hasPreviewAudio}
                title={hasPreviewAudio ? "Play preview audio" : "No preview audio available"}
              >
                {isPlaying ? (
                  <>
                    <Volume2 className="mr-1.5 h-4 w-4 animate-pulse" />
                    Playing...
                  </>
                ) : (
                  <>
                    <Play className="mr-1.5 h-4 w-4" />
                    Try Voice
                  </>
                )}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
