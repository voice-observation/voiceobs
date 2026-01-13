"use client";

import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertCircle, Plus } from "lucide-react";
import { api } from "@/lib/api";
import { logger } from "@/lib/logger";
import { PersonaCard } from "@/components/personas/PersonaCard";
import { CreatePersonaDialog } from "@/components/personas/CreatePersonaDialog";
import type { PersonaCreateRequest, PersonaListItem } from "@/lib/types";

export default function PersonasPage() {
  const [personas, setPersonas] = useState<PersonaListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("active");

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        setError(null);
        // Fetch all personas (both active and inactive)
        const response = await api.personas.listPersonas(null);
        setPersonas(response.personas);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load personas");
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const activePersonas = personas.filter((p) => p.is_active);
  const inactivePersonas = personas.filter((p) => !p.is_active);

  const handleCreatePersona = async (data: PersonaCreateRequest) => {
    try {
      const newPersona = await api.personas.createPersona(data);
      // Convert PersonaResponse to PersonaListItem for display
      const personaListItem: PersonaListItem = {
        id: newPersona.id,
        name: newPersona.name,
        description: newPersona.description,
        aggression: newPersona.aggression,
        patience: newPersona.patience,
        verbosity: newPersona.verbosity,
        traits: newPersona.traits,
        preview_audio_url: newPersona.preview_audio_url,
        preview_audio_text: newPersona.preview_audio_text,
        is_active: newPersona.is_active,
      };
      setPersonas((prev) => [...prev, personaListItem]);
    } catch (err) {
      throw err; // Re-throw to let dialog handle it
    }
  };

  const handleToggleEnabled = async (id: string, enabled: boolean) => {
    try {
      // Optimistically update UI
      setPersonas((prev) =>
        prev.map((p) => (p.id === id ? { ...p, is_active: enabled } : p))
      );

      // Call the API to update the persona's active status
      const updatedPersona = await api.personas.setPersonaActive(id, enabled);

      // Update the persona in the list with the response from the API
      setPersonas((prev) =>
        prev.map((p) => (p.id === id ? { ...p, is_active: updatedPersona.is_active } : p))
      );

      logger.info("Persona active status updated", { personaId: id, isActive: enabled });
    } catch (err) {
      logger.error("Failed to update persona active status", err, { personaId: id, isActive: enabled });
      // Revert on error by refreshing
      try {
        const response = await api.personas.listPersonas(null);
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
        preview = await api.personas.getPersonaPreviewAudio(id);
      } catch (err) {
        // If preview doesn't exist, generate it
        logger.debug("Preview audio not found, generating...", { personaId: id });
        preview = await api.personas.generatePersonaPreviewAudio(id);
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
          logger.error("Audio playback error", undefined, { personaId: id, audioUrl: preview.audio_url });
          audio.remove();
        });
      } else {
        logger.warn("No preview audio URL available", { personaId: id });
      }
    } catch (err) {
      logger.error("Failed to get or generate preview audio", err, { personaId: id });
    }
  };


  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <Skeleton className="h-9 w-48 mb-2" />
          <Skeleton className="h-5 w-96" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
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
            <Button size="sm" onClick={() => setCreateDialogOpen(true)}>
              <Plus className="w-4 h-4 mr-2" />
              Create Persona
            </Button>
          </div>
        </div>

        <TabsContent value="active" className="mt-6">
          {activePersonas.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {activePersonas.map((persona) => (
                <PersonaCard
                  key={persona.id}
                  persona={persona}
                  onToggleEnabled={handleToggleEnabled}
                  onListenVoice={handleListenVoice}
                />
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-12 text-muted-foreground">
                  <p>No active personas found</p>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="inactive" className="mt-6">
          {inactivePersonas.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {inactivePersonas.map((persona) => (
                <PersonaCard
                  key={persona.id}
                  persona={persona}
                  onToggleEnabled={handleToggleEnabled}
                  onListenVoice={handleListenVoice}
                />
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-12 text-muted-foreground">
                  <p>No inactive personas found</p>
                  <Button
                    variant="outline"
                    className="mt-4"
                    onClick={() => setCreateDialogOpen(true)}
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Create Your First Persona
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>

      <CreatePersonaDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
        onCreate={handleCreatePersona}
      />
    </div>
  );
}
