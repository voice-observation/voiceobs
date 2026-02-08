"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/primitives/card";
import { Badge } from "@/components/primitives/badge";
import { Skeleton } from "@/components/primitives/skeleton";
import { Button } from "@/components/primitives/button";
import { Switch } from "@/components/primitives/switch";
import { Label } from "@/components/primitives/label";
import { Slider } from "@/components/primitives/slider";
import { api } from "@/lib/api";
import { logger } from "@/lib/logger";
import { AlertCircle, ArrowLeft, Pencil, Play, Trash2, Volume2 } from "lucide-react";
import { AudioPlayer } from "@/components/shared/audio/AudioPlayer";
import { DeletePersonaDialog } from "@/components/personas/DeletePersonaDialog";
import { toast } from "sonner";
import type { Persona } from "@/lib/types";

export default function PersonaDetailPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const [persona, setPersona] = useState<Persona | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        setError(null);
        const personaData = await api.personas.getPersona(params.id);
        setPersona(personaData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load persona");
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [params.id]);

  const handleToggleActive = async (checked: boolean) => {
    if (!persona) return;

    try {
      // Optimistically update UI
      setPersona((prev) => (prev ? { ...prev, is_active: checked } : null));

      // Call the API to update the persona's active status
      const updatedPersona = await api.personas.setPersonaActive(persona.id, checked);
      setPersona(updatedPersona);

      logger.info("Persona active status updated", {
        personaId: persona.id,
        isActive: checked,
      });
    } catch (err) {
      logger.error("Failed to update persona active status", err, {
        personaId: persona.id,
        isActive: checked,
      });
      // Revert on error
      try {
        const refreshedPersona = await api.personas.getPersona(persona.id);
        setPersona(refreshedPersona);
      } catch (refreshErr) {
        logger.error("Failed to refresh persona after toggle error", refreshErr);
      }
    }
  };

  const handlePlayPreview = async () => {
    if (!persona) return;

    try {
      setIsPlaying(true);
      let preview;
      try {
        // Try to get existing preview audio
        preview = await api.personas.getPersonaPreviewAudio(persona.id);
      } catch (err) {
        // If preview doesn't exist, generate it
        logger.debug("Preview audio not found, generating...", { personaId: persona.id });
        preview = await api.personas.generatePersonaPreviewAudio(persona.id);
      }

      if (preview.audio_url) {
        setAudioUrl(preview.audio_url);
        // Create audio element and play
        const audio = new Audio(preview.audio_url);
        audio.play().catch((err) => {
          logger.error("Failed to play audio", err, {
            personaId: persona.id,
            audioUrl: preview.audio_url,
          });
          setIsPlaying(false);
        });
        // Clean up when done
        audio.addEventListener("ended", () => {
          setIsPlaying(false);
          audio.remove();
        });
        audio.addEventListener("error", () => {
          logger.error("Audio playback error", undefined, {
            personaId: persona.id,
            audioUrl: preview.audio_url,
          });
          setIsPlaying(false);
          audio.remove();
        });
      } else {
        logger.warn("No preview audio URL available", { personaId: persona.id });
        setIsPlaying(false);
      }
    } catch (err) {
      logger.error("Failed to get or generate preview audio", err, { personaId: persona.id });
      setIsPlaying(false);
    }
  };

  const handleDeletePersona = async () => {
    if (!persona) return;

    setIsDeleting(true);
    try {
      await api.personas.deletePersona(persona.id);
      toast("Persona deleted", {
        description: `"${persona.name}" has been deleted successfully.`,
      });
      router.push("/personas");
    } catch (err) {
      logger.error("Failed to delete persona", err);
      const errorMessage = err instanceof Error ? err.message : "Failed to delete persona";
      toast.error("Delete failed", {
        description: errorMessage,
      });
      setIsDeleting(false);
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "N/A";
    return new Date(dateString).toLocaleDateString();
  };

  const toPascalCase = (str: string | null) => {
    if (!str) return "N/A";
    return str
      .split(/[\s_-]+/)
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join("");
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <Skeleton className="mb-4 h-8 w-32" />
          <Skeleton className="h-9 w-48" />
        </div>
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          {/* Left Column Skeleton */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <Skeleton className="h-6 w-24" />
              </CardHeader>
              <CardContent className="space-y-3">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <Skeleton className="h-6 w-32" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-24 w-full" />
              </CardContent>
            </Card>
          </div>
          {/* Right Column Skeleton */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <Skeleton className="h-6 w-20" />
              </CardHeader>
              <CardContent>
                <div className="flex gap-2">
                  <Skeleton className="h-6 w-16" />
                  <Skeleton className="h-6 w-20" />
                  <Skeleton className="h-6 w-14" />
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <Skeleton className="h-6 w-28" />
                <Skeleton className="h-4 w-48" />
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-2 gap-4">
                  <Skeleton className="h-10 w-full" />
                  <Skeleton className="h-10 w-full" />
                </div>
                <Skeleton className="h-12 w-full" />
                <Skeleton className="h-12 w-full" />
                <Skeleton className="h-12 w-full" />
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <Button variant="ghost" size="sm" asChild className="mb-4">
            <Link href="/personas">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Personas
            </Link>
          </Button>
          <h1 className="text-3xl font-bold tracking-tight">Persona Details</h1>
        </div>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-destructive">
              <AlertCircle className="h-5 w-5" />
              <p>Error loading persona: {error}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!persona) {
    return (
      <div className="space-y-6">
        <div>
          <Button variant="ghost" size="sm" asChild className="mb-4">
            <Link href="/personas">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Personas
            </Link>
          </Button>
          <h1 className="text-3xl font-bold tracking-tight">Persona Details</h1>
        </div>
        <Card>
          <CardContent className="pt-6">
            <p className="text-muted-foreground">Persona not found</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <Button variant="ghost" size="sm" asChild className="mb-4">
          <Link href="/personas">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Personas
          </Link>
        </Button>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">{persona.name}</h1>
          </div>
          <div className="flex items-center gap-3">
            <Button variant="outline" size="sm" asChild>
              <Link href={`/personas/${params.id}/edit`}>
                <Pencil className="mr-2 h-4 w-4" />
                Edit
              </Link>
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setDeleteDialogOpen(true)}
              className="text-destructive hover:text-destructive"
            >
              <Trash2 className="mr-2 h-4 w-4" />
              Delete
            </Button>
            <div className="flex items-center gap-2">
              <Label htmlFor="active-toggle" className="text-sm">
                {persona.is_active ? "Active" : "Inactive"}
              </Label>
              <Switch
                id="active-toggle"
                checked={persona.is_active}
                onCheckedChange={handleToggleActive}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Two-column layout */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        {/* Left Column */}
        <div className="space-y-6">
          {/* Details */}
          <Card>
            <CardHeader>
              <CardTitle>Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {persona.description && (
                <div className="flex items-center gap-2">
                  <Label className="w-28 flex-shrink-0 text-xs text-muted-foreground">
                    Description
                  </Label>
                  <p className="text-sm font-medium">{persona.description}</p>
                </div>
              )}
              <div className="flex items-center gap-2">
                <Label className="w-28 flex-shrink-0 text-xs text-muted-foreground">Created</Label>
                <p className="text-sm font-medium">{formatDate(persona.created_at)}</p>
              </div>
              {persona.created_by && (
                <div className="flex items-center gap-2">
                  <Label className="w-28 flex-shrink-0 text-xs text-muted-foreground">
                    Created By
                  </Label>
                  <p className="text-sm font-medium">{toPascalCase(persona.created_by)}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Preview Audio */}
          <Card>
            <CardHeader>
              <CardTitle>Preview Audio</CardTitle>
            </CardHeader>
            <CardContent>
              {persona.preview_audio_url ? (
                <div className="space-y-4">
                  {audioUrl && <AudioPlayer audioUrl={audioUrl} />}
                  <Button
                    onClick={handlePlayPreview}
                    disabled={isPlaying}
                    variant={audioUrl ? "outline" : "default"}
                  >
                    {isPlaying ? (
                      <>
                        <Volume2 className="mr-2 h-4 w-4 animate-pulse" />
                        Playing...
                      </>
                    ) : (
                      <>
                        <Play className="mr-2 h-4 w-4" />
                        {audioUrl ? "Play Again" : "Play Preview"}
                      </>
                    )}
                  </Button>
                  {persona.preview_audio_text && (
                    <p className="mt-2 text-sm text-muted-foreground">
                      Preview text: &quot;{persona.preview_audio_text}&quot;
                    </p>
                  )}
                </div>
              ) : (
                <div className="py-8 text-center">
                  <p className="mb-4 text-muted-foreground">No preview audio available</p>
                  <Button onClick={handlePlayPreview} disabled={isPlaying}>
                    {isPlaying ? (
                      <>
                        <Volume2 className="mr-2 h-4 w-4 animate-pulse" />
                        Generating...
                      </>
                    ) : (
                      <>
                        <Play className="mr-2 h-4 w-4" />
                        Generate Preview Audio
                      </>
                    )}
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right Column */}
        <div className="space-y-6">
          {/* Configuration */}
          <Card>
            <CardHeader>
              <CardTitle>Configuration</CardTitle>
              <CardDescription>
                Voice and behavioral characteristics of this persona
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* TTS Settings - Side by side */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <Label className="text-xs text-muted-foreground">TTS Provider</Label>
                  <p className="text-sm font-medium">
                    {persona.tts_provider
                      ? persona.tts_provider.charAt(0).toUpperCase() + persona.tts_provider.slice(1)
                      : "Not set"}
                  </p>
                </div>
                <div className="space-y-1">
                  <Label className="text-xs text-muted-foreground">TTS Model</Label>
                  <p className="text-sm font-medium">
                    {(() => {
                      if (!persona.tts_config) return "Not set";
                      const config = persona.tts_config;
                      if (persona.tts_provider === "elevenlabs" && config.voice_name) {
                        return config.voice_name as string;
                      }
                      if (persona.tts_provider === "openai" && config.voice) {
                        return `${config.voice} (${config.model || "tts-1"})`;
                      }
                      if (persona.tts_provider === "deepgram" && config.model) {
                        return config.model as string;
                      }
                      return "Not set";
                    })()}
                  </p>
                </div>
              </div>

              {/* Behavioral Sliders */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>Aggression</Label>
                  <span className="text-sm font-medium">{persona.aggression.toFixed(1)}</span>
                </div>
                <Slider
                  value={[persona.aggression]}
                  max={1}
                  min={0}
                  step={0.1}
                  disabled
                  className="w-full"
                />
                <div className="flex items-center justify-between px-1 text-xs text-muted-foreground">
                  <span>Passive</span>
                  <span>Assertive</span>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>Patience</Label>
                  <span className="text-sm font-medium">{persona.patience.toFixed(1)}</span>
                </div>
                <Slider
                  value={[persona.patience]}
                  max={1}
                  min={0}
                  step={0.1}
                  disabled
                  className="w-full"
                />
                <div className="flex items-center justify-between px-1 text-xs text-muted-foreground">
                  <span>Impatient</span>
                  <span>Patient</span>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label>Verbosity</Label>
                  <span className="text-sm font-medium">{persona.verbosity.toFixed(1)}</span>
                </div>
                <Slider
                  value={[persona.verbosity]}
                  max={1}
                  min={0}
                  step={0.1}
                  disabled
                  className="w-full"
                />
                <div className="flex items-center justify-between px-1 text-xs text-muted-foreground">
                  <span>Concise</span>
                  <span>Verbose</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Traits */}
          {persona.traits.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Traits</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {persona.traits.map((trait, idx) => (
                    <Badge key={idx} variant="secondary">
                      {trait}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Delete Dialog */}
      {persona && (
        <DeletePersonaDialog
          open={deleteDialogOpen}
          onOpenChange={setDeleteDialogOpen}
          persona={persona}
          onDelete={handleDeletePersona}
          isDeleting={isDeleting}
        />
      )}
    </div>
  );
}
