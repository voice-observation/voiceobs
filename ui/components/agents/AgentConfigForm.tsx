"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CheckboxCard } from "@/components/shared/CheckboxCard";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { Loader2, Phone, HelpCircle, Plus, Save } from "lucide-react";
import type { Agent, AgentCreateRequest, AgentUpdateRequest } from "@/lib/types";

interface AgentConfigFormProps {
  /** Existing agent for edit mode */
  agent?: Agent;
  /** Called when form is submitted */
  onSubmit: (data: AgentCreateRequest | AgentUpdateRequest) => Promise<void>;
  /** Called when cancel is clicked */
  onCancel?: () => void;
  /** Submit button text override */
  submitLabel?: string;
}

const DEFAULT_INTENTS = [
  { id: "book", label: "Book" },
  { id: "reschedule", label: "Reschedule" },
  { id: "cancel", label: "Cancel" },
  { id: "ask-hours", label: "Ask hours" },
  { id: "talk-to-human", label: "Talk to human" },
];

export function AgentConfigForm({ agent, onSubmit, onCancel, submitLabel }: AgentConfigFormProps) {
  const isEditMode = !!agent;

  const [name, setName] = useState(agent?.name || "");
  const [description, setDescription] = useState(agent?.description || "");
  const [phoneNumber, setPhoneNumber] = useState(agent?.phone_number || "");
  const [selectedIntents, setSelectedIntents] = useState<string[]>(() => {
    if (agent?.supported_intents) {
      // Filter to only default intents that are selected
      return DEFAULT_INTENTS.filter((i) => agent.supported_intents.includes(i.id)).map((i) => i.id);
    }
    return [];
  });
  const [customIntents, setCustomIntents] = useState<string[]>(() => {
    if (agent?.supported_intents) {
      // Filter out default intents to get custom ones
      const defaultIds = DEFAULT_INTENTS.map((i) => i.id);
      return agent.supported_intents.filter((i) => !defaultIds.includes(i));
    }
    return [];
  });
  const [newCustomIntent, setNewCustomIntent] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleIntentToggle = (intentId: string) => {
    setSelectedIntents((prev) =>
      prev.includes(intentId) ? prev.filter((id) => id !== intentId) : [...prev, intentId]
    );
    // Clear intent error when user makes a selection
    if (errors.intents) {
      setErrors((prev) => ({ ...prev, intents: "" }));
    }
  };

  const handleAddCustomIntent = () => {
    const intent = newCustomIntent.trim();
    if (intent && !customIntents.includes(intent)) {
      setCustomIntents((prev) => [...prev, intent]);
      setNewCustomIntent("");
      // Clear intent error when user adds an intent
      if (errors.intents) {
        setErrors((prev) => ({ ...prev, intents: "" }));
      }
    }
  };

  const handleRemoveCustomIntent = (intent: string) => {
    setCustomIntents((prev) => prev.filter((i) => i !== intent));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleAddCustomIntent();
    }
  };

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!name.trim()) {
      newErrors.name = "Name is required";
    } else if (name.length > 255) {
      newErrors.name = "Name must be 255 characters or less";
    }

    if (!description.trim()) {
      newErrors.description = "Description is required";
    }

    if (!phoneNumber.trim()) {
      newErrors.phoneNumber = "Phone number is required";
    } else if (!/^\+?[1-9]\d{1,14}$/.test(phoneNumber.replace(/[\s\-()]/g, ""))) {
      newErrors.phoneNumber = "Please enter a valid phone number (E.164 format)";
    }

    const allIntents = [...selectedIntents, ...customIntents];
    if (allIntents.length === 0) {
      newErrors.intents = "At least one intent is required";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) return;

    setIsSubmitting(true);
    try {
      const allIntents = [...selectedIntents, ...customIntents];
      const cleanPhoneNumber = phoneNumber.replace(/[\s\-()]/g, "");

      if (isEditMode) {
        // For edit mode, only include changed fields
        const updates: AgentUpdateRequest = {};
        if (name !== agent.name) updates.name = name;
        if (description !== agent.description) updates.description = description;
        if (cleanPhoneNumber !== agent.phone_number) updates.phone_number = cleanPhoneNumber;

        // Compare intents arrays
        const currentIntents = agent.supported_intents || [];
        const intentsChanged =
          allIntents.length !== currentIntents.length ||
          !allIntents.every((i) => currentIntents.includes(i));
        if (intentsChanged) updates.supported_intents = allIntents;

        await onSubmit(updates);
      } else {
        // For create mode, include all fields
        const data: AgentCreateRequest = {
          name: name.trim(),
          description: description.trim(),
          phone_number: cleanPhoneNumber,
          supported_intents: allIntents,
        };
        await onSubmit(data);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Agent Overview</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Agent Name</Label>
            <Input
              id="name"
              placeholder="e.g., Customer Service Bot"
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                if (errors.name) setErrors((prev) => ({ ...prev, name: "" }));
              }}
              className={errors.name ? "border-destructive" : ""}
            />
            {errors.name && <p className="text-sm text-destructive">{errors.name}</p>}
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Agent Description</Label>
            <p className="text-sm text-muted-foreground">
              In one sentence, what should this agent accomplish?
            </p>
            <Textarea
              id="description"
              placeholder="Book dentist appointments and handle rescheduling."
              value={description}
              onChange={(e) => {
                setDescription(e.target.value);
                if (errors.description) setErrors((prev) => ({ ...prev, description: "" }));
              }}
              className={errors.description ? "border-destructive" : ""}
              rows={3}
            />
            {errors.description && <p className="text-sm text-destructive">{errors.description}</p>}
          </div>

          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Label>Supported Agent Intents</Label>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button type="button" className="inline-flex">
                      <HelpCircle className="h-4 w-4 cursor-help text-muted-foreground" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Used to generate realistic test scenarios.</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>

            <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
              {DEFAULT_INTENTS.map((intent) => (
                <CheckboxCard
                  key={intent.id}
                  label={intent.label}
                  checked={selectedIntents.includes(intent.id)}
                  onCheckedChange={() => handleIntentToggle(intent.id)}
                />
              ))}
              {customIntents.map((intent) => (
                <CheckboxCard
                  key={intent}
                  label={intent}
                  checked={true}
                  onCheckedChange={() => handleRemoveCustomIntent(intent)}
                />
              ))}
            </div>

            <div className="flex gap-2">
              <Input
                placeholder="Add custom intent..."
                value={newCustomIntent}
                onChange={(e) => setNewCustomIntent(e.target.value)}
                onKeyDown={handleKeyDown}
                className="flex-1"
              />
              <Button
                type="button"
                variant="outline"
                size="icon"
                onClick={handleAddCustomIntent}
                disabled={!newCustomIntent.trim()}
              >
                <Plus className="h-4 w-4" />
              </Button>
            </div>

            {errors.intents && <p className="text-sm text-destructive">{errors.intents}</p>}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Agent Connection</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="phone">Phone Number</Label>
            <div className="relative">
              <Phone className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                id="phone"
                type="tel"
                placeholder="+1 (555) 123-4567"
                value={phoneNumber}
                onChange={(e) => {
                  setPhoneNumber(e.target.value);
                  if (errors.phoneNumber) setErrors((prev) => ({ ...prev, phoneNumber: "" }));
                }}
                className={`pl-10 ${errors.phoneNumber ? "border-destructive" : ""}`}
              />
            </div>
            <p className="text-xs text-muted-foreground">
              Enter the phone number to call the voice agent (E.164 format, e.g., +14155551234)
            </p>
            {errors.phoneNumber && <p className="text-sm text-destructive">{errors.phoneNumber}</p>}
          </div>
        </CardContent>
      </Card>

      <div className="flex gap-3">
        {onCancel && (
          <Button
            type="button"
            variant="outline"
            onClick={onCancel}
            disabled={isSubmitting}
            className="flex-1"
          >
            Cancel
          </Button>
        )}
        <Button
          type="submit"
          disabled={isSubmitting}
          className={onCancel ? "flex-1" : "w-full"}
          size="lg"
        >
          {isSubmitting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              {isEditMode ? "Saving..." : "Creating..."}
            </>
          ) : (
            <>
              <Save className="mr-2 h-4 w-4" />
              {submitLabel || (isEditMode ? "Save Changes" : "Create Agent")}
            </>
          )}
        </Button>
      </div>
    </form>
  );
}
