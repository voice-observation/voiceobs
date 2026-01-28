"use client";

import { useState, useEffect } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Slider } from "@/components/ui/slider";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { api } from "@/lib/api";
import { logger } from "@/lib/logger";
import type { PersonaCreateRequest } from "@/lib/types";

interface CreatePersonaDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreate: (data: PersonaCreateRequest) => Promise<void>;
}

type TTSModels = Record<string, Record<string, Record<string, unknown>>>;

// Default values for persona attributes
const DEFAULT_AGGRESSION = 0.5;
const DEFAULT_PATIENCE = 0.6;
const DEFAULT_VERBOSITY = 0.4;

export function CreatePersonaDialog({ open, onOpenChange, onCreate }: CreatePersonaDialogProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [aggression, setAggression] = useState([DEFAULT_AGGRESSION]);
  const [patience, setPatience] = useState([DEFAULT_PATIENCE]);
  const [verbosity, setVerbosity] = useState([DEFAULT_VERBOSITY]);
  const [traits, setTraits] = useState("");
  const [ttsProvider, setTtsProvider] = useState<string>("");
  const [ttsModel, setTtsModel] = useState<string>("");
  const [ttsModels, setTtsModels] = useState<TTSModels>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [loadingModels, setLoadingModels] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Load TTS models when dialog opens
  useEffect(() => {
    if (open) {
      loadTTSModels();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  const loadTTSModels = async () => {
    try {
      setLoadingModels(true);
      const models = await api.personas.getTTSModels();
      setTtsModels(models);
      // Set default provider and model if available
      const providers = Object.keys(models);
      if (providers.length > 0 && !ttsProvider) {
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

  const handleSubmit = async () => {
    if (!name.trim() || !description.trim()) {
      return;
    }

    // Only validate TTS fields if advanced section is enabled
    if (showAdvanced && (!ttsProvider || !ttsModel)) {
      logger.warn("TTS provider and model must be selected when advanced options are enabled");
      return;
    }

    setIsSubmitting(true);
    try {
      const requestData: PersonaCreateRequest = {
        name,
        description: description || null,
        traits: traits
          .split(",")
          .map((t) => t.trim())
          .filter((t) => t.length > 0),
      };

      // Only include advanced fields if advanced section is enabled
      if (showAdvanced) {
        // Get the model config from the selected provider and model
        const modelConfig = ttsModels[ttsProvider]?.[ttsModel];
        if (!modelConfig) {
          throw new Error("Selected TTS model configuration not found");
        }

        requestData.aggression = aggression[0];
        requestData.patience = patience[0];
        requestData.verbosity = verbosity[0];
        requestData.tts_provider = ttsProvider;
        requestData.tts_config = modelConfig as Record<string, unknown>;
      }

      await onCreate(requestData);
      // Reset form
      setName("");
      setDescription("");
      setAggression([DEFAULT_AGGRESSION]);
      setPatience([DEFAULT_PATIENCE]);
      setVerbosity([DEFAULT_VERBOSITY]);
      setTraits("");
      setTtsProvider("");
      setTtsModel("");
      setShowAdvanced(false);
      onOpenChange(false);
    } catch (error) {
      logger.error("Failed to create persona", error);
      throw error; // Re-throw to let parent handle it
    } finally {
      setIsSubmitting(false);
    }
  };

  // Validation: name and description are required
  // Advanced fields are optional, but if advanced is enabled, TTS fields are required
  const isValid = name.trim() && description.trim() && (!showAdvanced || (ttsProvider && ttsModel));

  // Get available models for selected provider
  const availableModels = ttsProvider ? Object.keys(ttsModels[ttsProvider] || {}) : [];

  // Get model display name helper
  const getModelDisplayName = (provider: string, modelKey: string): string => {
    const model = ttsModels[provider]?.[modelKey];
    if (!model) return modelKey;

    // For ElevenLabs, show voice_name
    if (provider === "elevenlabs" && "voice_name" in model) {
      return `${model.voice_name as string} (${modelKey})`;
    }
    // For OpenAI, show voice
    if (provider === "openai" && "voice" in model) {
      return `${model.voice as string} (${model.model as string})`;
    }
    // For Deepgram, show model
    if (provider === "deepgram" && "model" in model) {
      return `${model.model as string}`;
    }
    return modelKey;
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex max-h-[90vh] flex-col overflow-hidden sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Create New Persona</DialogTitle>
        </DialogHeader>

        <div className="flex-1 space-y-4 overflow-y-auto overflow-x-hidden px-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="name">Name *</Label>
            <div className="w-full">
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., Friendly Assistant"
                className="w-full"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description *</Label>
            <div className="w-full">
              <Textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe the persona's speaking style and behavior..."
                rows={3}
                className="w-full resize-none"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="traits">Traits (comma-separated)</Label>
            <div className="w-full">
              <Input
                id="traits"
                value={traits}
                onChange={(e) => setTraits(e.target.value)}
                placeholder="e.g., polite, patient, helpful"
                className="w-full"
              />
            </div>
          </div>

          {/* Advanced Options Section */}
          <div className="mt-2 pt-2">
            <Button
              type="button"
              variant="ghost"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="h-auto w-full justify-between p-0 font-normal hover:bg-transparent hover:text-foreground"
            >
              <span className="text-sm font-medium">Advanced Options</span>
              {showAdvanced ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </Button>

            {showAdvanced && (
              <div className="mt-4 space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="tts-provider">TTS Provider</Label>
                  <Select
                    value={ttsProvider}
                    onValueChange={(value) => {
                      setTtsProvider(value);
                      // Reset model when provider changes
                      const providerModels = Object.keys(ttsModels[value] || {});
                      setTtsModel(providerModels.length > 0 ? providerModels[0] : "");
                    }}
                    disabled={loadingModels}
                  >
                    <SelectTrigger id="tts-provider" className="w-full max-w-full">
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
                      <SelectTrigger id="tts-model" className="w-full max-w-full">
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

                <div className="space-y-4 pt-2">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label>Aggression: {aggression[0].toFixed(1)}</Label>
                    </div>
                    <Slider
                      value={aggression}
                      onValueChange={setAggression}
                      max={1}
                      min={0}
                      step={0.1}
                      className="w-full"
                    />
                    <div className="flex items-center justify-between px-1 text-xs text-muted-foreground">
                      <span>Passive</span>
                      <span>Assertive</span>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label>Patience: {patience[0].toFixed(1)}</Label>
                    </div>
                    <Slider
                      value={patience}
                      onValueChange={setPatience}
                      max={1}
                      min={0}
                      step={0.1}
                      className="w-full"
                    />
                    <div className="flex items-center justify-between px-1 text-xs text-muted-foreground">
                      <span>Impatient</span>
                      <span>Patient</span>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label>Verbosity: {verbosity[0].toFixed(1)}</Label>
                    </div>
                    <Slider
                      value={verbosity}
                      onValueChange={setVerbosity}
                      max={1}
                      min={0}
                      step={0.1}
                      className="w-full"
                    />
                    <div className="flex items-center justify-between px-1 text-xs text-muted-foreground">
                      <span>Concise</span>
                      <span>Verbose</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={!isValid || isSubmitting}>
            {isSubmitting ? "Creating..." : "Create Persona"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
