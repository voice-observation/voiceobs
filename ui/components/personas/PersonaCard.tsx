"use client";

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Play, Thermometer, MapPin, User } from "lucide-react";
import type { Persona } from "@/lib/types";

interface PersonaCardProps {
  persona: Persona;
  onToggleEnabled: (id: string, enabled: boolean) => void;
  onListenVoice: (id: string) => void;
}

export function PersonaCard({ persona, onToggleEnabled, onListenVoice }: PersonaCardProps) {
  const [isPlaying, setIsPlaying] = useState(false);

  const handleListen = () => {
    setIsPlaying(true);
    onListenVoice(persona.id);
    // Simulate voice playback
    setTimeout(() => setIsPlaying(false), 2000);
  };

  const formatAccent = (accent: string) => {
    return accent
      .split(/[\s-]+/)
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join("");
  };

  return (
    <Card className="relative">
      <CardContent className="p-5">
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1 pr-4">
            <h3 className="font-semibold text-base mb-1">{persona.name}</h3>
            <p className="text-sm text-muted-foreground line-clamp-2">
              {persona.description || ""}
            </p>
          </div>
          <Switch
            checked={persona.enabled ?? true}
            onCheckedChange={(checked) => onToggleEnabled(persona.id, checked)}
          />
        </div>

        <div className="space-y-2 mt-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              {persona.gender && (
                <div className="flex items-center gap-1.5">
                  <User className="w-3.5 h-3.5" />
                  <span className="capitalize">{persona.gender}</span>
                </div>
              )}
              {persona.temperature !== undefined && (
                <div className="flex items-center gap-1.5">
                  <Thermometer className="w-3.5 h-3.5" />
                  <span>{persona.temperature}</span>
                </div>
              )}
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              {persona.accent && (
                <div className="flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5" />
                  <span>{formatAccent(persona.accent)}</span>
                </div>
              )}
            </div>

            <Button
              size="sm"
              variant="secondary"
              onClick={handleListen}
              disabled={isPlaying}
            >
              <Play className={`w-4 h-4 mr-1.5 ${isPlaying ? "animate-pulse" : ""}`} />
              {isPlaying ? "Playing..." : "Try Voice"}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
