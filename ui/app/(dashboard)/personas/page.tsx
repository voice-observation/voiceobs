"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent } from "@/components/primitives/card";
import { Button } from "@/components/primitives/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/primitives/tabs";
import { Skeleton } from "@/components/primitives/skeleton";
import { AlertCircle, Plus } from "lucide-react";
import { api } from "@/lib/api";
import { logger } from "@/lib/logger";
import { useAuth } from "@/contexts/auth-context";
import { PersonaCard } from "@/components/personas/PersonaCard";
import { DeletePersonaDialog } from "@/components/personas/DeletePersonaDialog";
import { toast } from "sonner";
import type { PersonaListItem } from "@/lib/types";

export default function PersonasPage() {
  const { activeOrg } = useAuth();
  const orgId = activeOrg?.id ?? "";
  const [personas, setPersonas] = useState<PersonaListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("active");
  const [deletePersona, setDeletePersona] = useState<PersonaListItem | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [playingPersonaId, setPlayingPersonaId] = useState<string | null>(null);
  useEffect(() => {
    if (!orgId) return;
    async function fetchData() {
      try {
        setLoading(true);
        setError(null);
        // Fetch all personas (both active and inactive)
        const response = await api.personas.listPersonas(orgId, null);
        setPersonas(response.personas);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load personas");
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [orgId]);

  const activePersonas = personas.filter((p) => p.is_active);
  const inactivePersonas = personas.filter((p) => !p.is_active);

  const handleToggleEnabled = async (id: string, enabled: boolean) => {
    try {
      // Optimistically update UI
      setPersonas((prev) => prev.map((p) => (p.id === id ? { ...p, is_active: enabled } : p)));

      // Call the API to update the persona's active status
      const updatedPersona = await api.personas.setPersonaActive(orgId, id, enabled);

      // Update the persona in the list with the response from the API
      setPersonas((prev) =>
        prev.map((p) => (p.id === id ? { ...p, is_active: updatedPersona.is_active } : p))
      );

      logger.info("Persona active status updated", { personaId: id, isActive: enabled });
    } catch (err) {
      logger.error("Failed to update persona active status", err, {
        personaId: id,
        isActive: enabled,
      });
      // Revert on error by refreshing
      try {
        const response = await api.personas.listPersonas(orgId, null);
        setPersonas(response.personas);
      } catch (refreshErr) {
        logger.error("Failed to refresh personas after toggle error", refreshErr);
      }
    }
  };

  const handleListenVoice = async (id: string) => {
    try {
      let preview;
      try {
        // Try to get existing preview audio
        preview = await api.personas.getPersonaPreviewAudio(orgId, id);
      } catch (err) {
        // If preview doesn't exist, generate it
        logger.debug("Preview audio not found, generating...", { personaId: id });
        preview = await api.personas.generatePersonaPreviewAudio(orgId, id);
      }

      if (preview.audio_url) {
        // Create audio element and play
        const audio = new Audio(preview.audio_url);
        audio.play().catch((err) => {
          logger.error("Failed to play audio", err, { personaId: id, audioUrl: preview.audio_url });
        });
        // Clean up when done
        audio.addEventListener("ended", () => {
          audio.remove();
        });
        audio.addEventListener("error", () => {
          logger.error("Audio playback error", undefined, {
            personaId: id,
            audioUrl: preview.audio_url,
          });
          audio.remove();
        });
      } else {
        logger.warn("No preview audio URL available", { personaId: id });
      }
    } catch (err) {
      logger.error("Failed to get or generate preview audio", err, { personaId: id });
    }
  };

  const handleSetDefault = async (id: string) => {
    try {
      await api.personas.setDefault(orgId, id);
      logger.info("Persona set as default", { personaId: id });
      // Refresh the personas list to get updated is_default flags
      const response = await api.personas.listPersonas(orgId, null);
      setPersonas(response.personas);
    } catch (err) {
      logger.error("Failed to set persona as default", err, { personaId: id });
    }
  };

  const handleDeleteClick = (persona: PersonaListItem) => {
    setDeletePersona(persona);
  };

  const handleDeletePersona = async () => {
    if (!deletePersona) return;

    setIsDeleting(true);
    try {
      await api.personas.deletePersona(orgId, deletePersona.id);
      setPersonas((prev) => prev.filter((p) => p.id !== deletePersona.id));
      toast("Persona deleted", {
        description: `"${deletePersona.name}" has been deleted successfully.`,
      });
      setDeletePersona(null);
    } catch (err) {
      logger.error("Failed to delete persona", err);
      const errorMessage = err instanceof Error ? err.message : "Failed to delete persona";
      toast.error("Delete failed", {
        description: errorMessage,
      });
    } finally {
      setIsDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <Skeleton className="mb-2 h-9 w-48" />
          <Skeleton className="h-5 w-96" />
        </div>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Skeleton key={i} className="h-64 w-full" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Personas</h1>
        </div>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-destructive">
              <AlertCircle className="h-5 w-5" />
              <p>Error loading personas: {error}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Personas</h1>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <div className="flex items-center justify-between">
          <TabsList>
            <TabsTrigger value="active">Active Personas</TabsTrigger>
            <TabsTrigger value="inactive">Inactive Personas</TabsTrigger>
          </TabsList>

          <div className="flex items-center gap-2">
            <Button size="sm" asChild>
              <Link href="/personas/new">
                <Plus className="mr-2 h-4 w-4" />
                Create Persona
              </Link>
            </Button>
          </div>
        </div>

        <TabsContent value="active" className="mt-6">
          {activePersonas.length > 0 ? (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
              {activePersonas.map((persona) => (
                <PersonaCard
                  key={persona.id}
                  orgId={orgId}
                  persona={persona}
                  onToggleEnabled={handleToggleEnabled}
                  onListenVoice={handleListenVoice}
                  onSetDefault={handleSetDefault}
                  onDelete={handleDeleteClick}
                  playingPersonaId={playingPersonaId}
                  onPlayingChange={setPlayingPersonaId}
                />
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="pt-6">
                <div className="py-12 text-center text-muted-foreground">
                  <p>No active personas found</p>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="inactive" className="mt-6">
          {inactivePersonas.length > 0 ? (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
              {inactivePersonas.map((persona) => (
                <PersonaCard
                  key={persona.id}
                  orgId={orgId}
                  persona={persona}
                  onToggleEnabled={handleToggleEnabled}
                  onListenVoice={handleListenVoice}
                  onSetDefault={handleSetDefault}
                  onDelete={handleDeleteClick}
                  playingPersonaId={playingPersonaId}
                  onPlayingChange={setPlayingPersonaId}
                />
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="pt-6">
                <div className="py-12 text-center text-muted-foreground">
                  <p>No inactive personas found</p>
                  <Button variant="outline" className="mt-4" asChild>
                    <Link href="/personas/new">
                      <Plus className="mr-2 h-4 w-4" />
                      Create Your First Persona
                    </Link>
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>

      <DeletePersonaDialog
        open={!!deletePersona}
        onOpenChange={(open) => !open && setDeletePersona(null)}
        persona={deletePersona}
        onDelete={handleDeletePersona}
        isDeleting={isDeleting}
      />
    </div>
  );
}
