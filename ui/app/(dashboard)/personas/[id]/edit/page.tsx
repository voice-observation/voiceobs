"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/primitives/card";
import { Button } from "@/components/primitives/button";
import { Label } from "@/components/primitives/label";
import { Input } from "@/components/primitives/input";
import { Textarea } from "@/components/primitives/textarea";
import { Slider } from "@/components/primitives/slider";
import { Skeleton } from "@/components/primitives/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/primitives/select";
import { AlertCircle } from "lucide-react";
import { api } from "@/lib/api";
import { logger } from "@/lib/logger";
import { toast } from "sonner";
import { TraitSelect } from "@/components/personas/TraitSelect";
import type { Persona, PersonaUpdateRequest } from "@/lib/types";

type TTSModels = Record<string, Record<string, Record<string, unknown>>>;

export default function EditPersonaPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const [persona, setPersona] = useState<Persona | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [aggression, setAggression] = useState([0.5]);
  const [patience, setPatience] = useState([0.6]);
  const [verbosity, setVerbosity] = useState([0.4]);
  const [traits, setTraits] = useState<string[]>([]);
  const [ttsProvider, setTtsProvider] = useState<string>("");
  const [ttsModel, setTtsModel] = useState<string>("");
  const [ttsModels, setTtsModels] = useState<TTSModels>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [loadingModels, setLoadingModels] = useState(false);

  // Fetch persona data on mount
  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        setError(null);
        const personaData = await api.personas.getPersona(params.id);
        setPersona(personaData);

        // Initialize form with persona data
        setName(personaData.name);
        setDescription(personaData.description || "");
        setAggression([personaData.aggression]);
        setPatience([personaData.patience]);
        setVerbosity([personaData.verbosity]);
        setTraits(personaData.traits || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load persona");
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [params.id]);

  // Load TTS models on mount
  useEffect(() => {
    const loadTTSModels = async () => {
      try {
        setLoadingModels(true);
        const models = await api.personas.getTTSModels();
        setTtsModels(models);
        // Set default provider and model if available
        const providers = Object.keys(models);
        if (providers.length > 0) {
          setTtsProvider(providers[0]);
          const providerModels = Object.keys(models[providers[0]]);
          if (providerModels.length > 0) {
            setTtsModel(providerModels[0]);
          }
        }
      } catch (err) {
        logger.error("Failed to load TTS models", err);
      } finally {
        setLoadingModels(false);
      }
    };

    loadTTSModels();
  }, []);

  // Get available models for selected provider
  const availableModels = ttsProvider ? Object.keys(ttsModels[ttsProvider] || {}) : [];

  // Get model display name helper
  const getModelDisplayName = (provider: string, modelKey: string): string => {
    const model = ttsModels[provider]?.[modelKey];
    if (!model) return modelKey;

    if (provider === "elevenlabs" && "voice_name" in model) {
      return `${model.voice_name as string} (${modelKey})`;
    }
    if (provider === "openai" && "voice" in model) {
      return `${model.voice as string} (${model.model as string})`;
    }
    if (provider === "deepgram" && "model" in model) {
      return `${model.model as string}`;
    }
    return modelKey;
  };

  const handleSubmit = async () => {
    if (!name.trim() || !description.trim()) {
      return;
    }

    setIsSubmitting(true);
    try {
      const updateData: PersonaUpdateRequest = {
        name,
        description: description || null,
        aggression: aggression[0],
        patience: patience[0],
        verbosity: verbosity[0],
        traits: traits,
      };

      // Include TTS config if provider and model are selected
      if (ttsProvider && ttsModel) {
        const modelConfig = ttsModels[ttsProvider]?.[ttsModel];
        if (modelConfig) {
          updateData.tts_provider = ttsProvider;
          updateData.tts_config = modelConfig as Record<string, unknown>;
        }
      }

      const updatedPersona = await api.personas.updatePersona(params.id, updateData);
      toast("Persona updated", {
        description: `"${updatedPersona.name}" has been updated successfully.`,
      });
      router.push(`/personas/${params.id}`);
    } catch (error) {
      logger.error("Failed to update persona", error);
      toast.error("Update failed", {
        description: error instanceof Error ? error.message : "Failed to update persona",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Validation
  const isValid = name.trim() && description.trim();

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <Skeleton className="mb-2 h-9 w-48" />
          <Skeleton className="h-5 w-96" />
        </div>
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-64" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-64 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error || !persona) {
    return (
      <div className="space-y-6">
        <div>
          <Button variant="ghost" size="sm" asChild className="mb-4">
            <Link href="/personas">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Personas
            </Link>
          </Button>
          <h1 className="text-3xl font-bold tracking-tight">Edit Persona</h1>
        </div>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-destructive">
              <AlertCircle className="h-5 w-5" />
              <p>{error || "Persona not found"}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <Button variant="ghost" size="sm" asChild className="mb-4">
          <Link href={`/personas/${params.id}`}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Persona
          </Link>
        </Button>
        <h1 className="text-3xl font-bold tracking-tight">Edit Persona</h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Basic Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="name">Name *</Label>
            <Input
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Friendly Assistant"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description *</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe the persona's speaking style and behavior..."
              rows={3}
            />
          </div>

          <div className="space-y-2">
            <Label>Traits</Label>
            <TraitSelect value={traits} onChange={setTraits} />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Advanced Options</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="tts-provider">TTS Provider</Label>
            <Select
              value={ttsProvider}
              onValueChange={(value) => {
                setTtsProvider(value);
                const providerModels = Object.keys(ttsModels[value] || {});
                setTtsModel(providerModels.length > 0 ? providerModels[0] : "");
              }}
              disabled={loadingModels}
            >
              <SelectTrigger id="tts-provider">
                <SelectValue placeholder="Select TTS provider" />
              </SelectTrigger>
              <SelectContent>
                {Object.keys(ttsModels).map((provider) => (
                  <SelectItem key={provider} value={provider}>
                    {provider.charAt(0).toUpperCase() + provider.slice(1)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {ttsProvider && (
            <div className="space-y-2">
              <Label htmlFor="tts-model">TTS Model</Label>
              <Select
                value={ttsModel}
                onValueChange={setTtsModel}
                disabled={loadingModels || availableModels.length === 0}
              >
                <SelectTrigger id="tts-model">
                  <SelectValue placeholder="Select TTS model" />
                </SelectTrigger>
                <SelectContent>
                  {availableModels.map((modelKey) => (
                    <SelectItem key={modelKey} value={modelKey}>
                      {getModelDisplayName(ttsProvider, modelKey)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>Aggression: {aggression[0].toFixed(1)}</Label>
            </div>
            <Slider value={aggression} onValueChange={setAggression} max={1} min={0} step={0.1} />
            <div className="flex items-center justify-between px-1 text-xs text-muted-foreground">
              <span>Passive</span>
              <span>Assertive</span>
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>Patience: {patience[0].toFixed(1)}</Label>
            </div>
            <Slider value={patience} onValueChange={setPatience} max={1} min={0} step={0.1} />
            <div className="flex items-center justify-between px-1 text-xs text-muted-foreground">
              <span>Impatient</span>
              <span>Patient</span>
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>Verbosity: {verbosity[0].toFixed(1)}</Label>
            </div>
            <Slider value={verbosity} onValueChange={setVerbosity} max={1} min={0} step={0.1} />
            <div className="flex items-center justify-between px-1 text-xs text-muted-foreground">
              <span>Concise</span>
              <span>Verbose</span>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end gap-2">
        <Button variant="outline" asChild>
          <Link href={`/personas/${params.id}`}>Cancel</Link>
        </Button>
        <Button onClick={handleSubmit} disabled={!isValid || isSubmitting}>
          {isSubmitting ? "Saving..." : "Save Changes"}
        </Button>
      </div>
    </div>
  );
}
