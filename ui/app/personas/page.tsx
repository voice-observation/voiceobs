"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertCircle, Plus, ToggleLeft, ToggleRight } from "lucide-react";
import { api, type Persona } from "@/lib/api";
import { PersonaCard } from "@/components/personas/PersonaCard";
import { CreatePersonaDialog } from "@/components/personas/CreatePersonaDialog";
import type { PersonaCreateRequest } from "@/lib/types";

export default function PersonasPage() {
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("predefined");

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        setError(null);
        const response = await api.listPersonas();
        setPersonas(response.personas);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load personas");
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const predefinedPersonas = personas.filter((p) => p.is_predefined);
  const customPersonas = personas.filter((p) => !p.is_predefined);

  const handleCreatePersona = async (data: PersonaCreateRequest) => {
    try {
      const newPersona = await api.createPersona(data);
      setPersonas((prev) => [...prev, newPersona]);
    } catch (err) {
      throw err; // Re-throw to let dialog handle it
    }
  };

  const handleToggleEnabled = async (id: string, enabled: boolean) => {
    try {
      const updatedPersona = await api.updatePersona(id, { enabled });
      setPersonas((prev) =>
        prev.map((p) => (p.id === id ? updatedPersona : p))
      );
    } catch (err) {
      console.error("Failed to update persona:", err);
    }
  };

  const handleListenVoice = (id: string) => {
    // TODO: Implement voice playback
    console.log("Listen voice for persona:", id);
  };

  const handleEnableAll = async () => {
    const currentPersonas = activeTab === "predefined" ? predefinedPersonas : customPersonas;
    const disabledPersonas = currentPersonas.filter((p) => !(p.enabled ?? true));

    for (const persona of disabledPersonas) {
      await handleToggleEnabled(persona.id, true);
    }
  };

  const handleDisableAll = async () => {
    const currentPersonas = activeTab === "predefined" ? predefinedPersonas : customPersonas;
    const enabledPersonas = currentPersonas.filter((p) => p.enabled ?? true);

    for (const persona of enabledPersonas) {
      await handleToggleEnabled(persona.id, false);
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
            <TabsTrigger value="predefined">Pre-defined Personas</TabsTrigger>
            <TabsTrigger value="custom">Custom Personas</TabsTrigger>
          </TabsList>

          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={handleDisableAll}>
              <ToggleLeft className="w-4 h-4 mr-2" />
              Disable All
            </Button>
            <Button variant="outline" size="sm" onClick={handleEnableAll}>
              <ToggleRight className="w-4 h-4 mr-2" />
              Enable All
            </Button>
            <Button size="sm" onClick={() => setCreateDialogOpen(true)}>
              <Plus className="w-4 h-4 mr-2" />
              Create Persona
            </Button>
          </div>
        </div>

        <TabsContent value="predefined" className="mt-6">
          {predefinedPersonas.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {predefinedPersonas.map((persona) => (
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
                  <p>No pre-defined personas found</p>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="custom" className="mt-6">
          {customPersonas.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {customPersonas.map((persona) => (
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
                  <p>No custom personas found</p>
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
