"use client";

import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/primitives/dialog";
import { Button } from "@/components/primitives/button";
import { Input } from "@/components/primitives/input";
import { Label } from "@/components/primitives/label";
import { Textarea } from "@/components/primitives/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/primitives/select";
import { Plus, X } from "lucide-react";
import { api } from "@/lib/api";
import { logger } from "@/lib/logger";
import type {
  TestSuite,
  PersonaListItem,
  TestScenario,
  TestScenarioUpdateRequest,
} from "@/lib/types";

interface TestScenarioDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** When provided, dialog is in edit mode with pre-populated values */
  scenario?: TestScenario;
  /** Pre-select suite (hides selector in create mode if provided) */
  suiteId?: string;
  /** Called after successful create */
  onCreate?: (scenario: { id: string; name: string; suite_id: string }) => void;
  /** Called after successful update */
  onUpdate?: (scenario: TestScenario) => void;
}

export function TestScenarioDialog({
  open,
  onOpenChange,
  scenario,
  suiteId,
  onCreate,
  onUpdate,
}: TestScenarioDialogProps) {
  // Determine mode
  const isEditMode = !!scenario;

  // Form state
  const [selectedSuiteId, setSelectedSuiteId] = useState<string>("");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [personaId, setPersonaId] = useState("");
  const [maxTurns, setMaxTurns] = useState("10");
  const [timeout, setTimeout] = useState("300");
  const [callerBehaviors, setCallerBehaviors] = useState<string[]>([]);
  const [tags, setTags] = useState("");

  // Data loading state
  const [availableSuites, setAvailableSuites] = useState<TestSuite[]>([]);
  const [availablePersonas, setAvailablePersonas] = useState<PersonaListItem[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [loading, setLoading] = useState(false);

  // Determine if suite selection should be shown
  // In create mode: show if suiteId prop is not provided
  // In edit mode: always show (to allow moving scenarios)
  const showSuiteSelection = isEditMode || !suiteId;

  // Get the effective suite ID
  const getEffectiveSuiteId = () => {
    if (isEditMode) {
      return selectedSuiteId || scenario.suite_id;
    }
    return suiteId || selectedSuiteId;
  };

  // Fetch available suites and personas when dialog opens
  useEffect(() => {
    if (open) {
      setLoading(true);
      Promise.all([api.testSuites.listTestSuites(), api.personas.listPersonas()])
        .then(([suitesResponse, personasResponse]) => {
          setAvailableSuites(suitesResponse.suites);
          setAvailablePersonas(personasResponse.personas);

          if (isEditMode && scenario) {
            // Edit mode: pre-populate form with scenario data
            setSelectedSuiteId(scenario.suite_id);
            setTitle(scenario.name || "");
            setDescription(scenario.goal || "");
            setPersonaId(scenario.persona_id || "");
            setMaxTurns(scenario.max_turns?.toString() || "10");
            setTimeout(scenario.timeout?.toString() || "300");
            setCallerBehaviors(scenario.caller_behaviors || []);
            setTags((scenario.tags || []).join(", "));
          } else {
            // Create mode: reset form, pre-select first persona if available
            resetForm();
            if (personasResponse.personas.length > 0) {
              setPersonaId(personasResponse.personas[0].id);
            }
          }
        })
        .catch((err) => {
          logger.error("Failed to load data for test scenario dialog", err);
        })
        .finally(() => {
          setLoading(false);
        });
    }
  }, [open, scenario, isEditMode]);

  const resetForm = () => {
    setTitle("");
    setDescription("");
    setPersonaId("");
    setMaxTurns("10");
    setTimeout("300");
    setCallerBehaviors([]);
    setTags("");
    setSelectedSuiteId("");
  };

  // Caller behaviors list management
  const handleAddCallerBehavior = () => {
    setCallerBehaviors([...callerBehaviors, ""]);
  };

  const handleRemoveCallerBehavior = (index: number) => {
    setCallerBehaviors(callerBehaviors.filter((_, i) => i !== index));
  };

  const handleCallerBehaviorChange = (index: number, value: string) => {
    const updated = [...callerBehaviors];
    updated[index] = value;
    setCallerBehaviors(updated);
  };

  // Parse tags from comma-separated string
  const parseTags = (tagsString: string): string[] => {
    return tagsString
      .split(",")
      .map((t) => t.trim())
      .filter((t) => t.length > 0);
  };

  const handleSubmit = async () => {
    const effectiveSuiteId = getEffectiveSuiteId();
    if (!title.trim() || !effectiveSuiteId || !personaId) {
      return;
    }

    setIsSubmitting(true);
    try {
      const filteredBehaviors = callerBehaviors.filter((b) => b.trim().length > 0);
      const parsedTags = parseTags(tags);

      if (isEditMode && scenario) {
        // Update existing scenario
        const updateData: TestScenarioUpdateRequest = {
          suite_id: selectedSuiteId !== scenario.suite_id ? selectedSuiteId : undefined,
          name: title.trim(),
          goal: description.trim() || null,
          persona_id: personaId !== scenario.persona_id ? personaId : undefined,
          max_turns: maxTurns ? parseInt(maxTurns, 10) : null,
          timeout: timeout ? parseInt(timeout, 10) : null,
          caller_behaviors: filteredBehaviors,
          tags: parsedTags,
        };

        const updatedScenario = await api.testScenarios.updateTestScenario(scenario.id, updateData);

        logger.info("Test scenario updated", {
          scenarioId: updatedScenario.id,
          suiteId: updatedScenario.suite_id,
        });

        if (onUpdate) {
          onUpdate(updatedScenario);
        }
      } else {
        // Create new scenario
        const newScenario = await api.testScenarios.createTestScenario({
          suite_id: effectiveSuiteId,
          name: title,
          goal: description || title,
          persona_id: personaId,
          max_turns: maxTurns ? parseInt(maxTurns, 10) : null,
          timeout: timeout ? parseInt(timeout, 10) : null,
          caller_behaviors: filteredBehaviors.length > 0 ? filteredBehaviors : undefined,
          tags: parsedTags.length > 0 ? parsedTags : undefined,
        });

        logger.info("Test scenario created", {
          scenarioId: newScenario.id,
          suiteId: effectiveSuiteId,
        });

        if (onCreate) {
          onCreate({
            id: newScenario.id,
            name: newScenario.name,
            suite_id: newScenario.suite_id,
          });
        }
      }

      onOpenChange(false);
    } catch (error) {
      logger.error(`Failed to ${isEditMode ? "update" : "create"} test scenario`, error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const effectiveSuiteId = getEffectiveSuiteId();
  const isValid = title.trim().length > 0 && effectiveSuiteId && personaId;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex max-h-[90vh] max-w-xl flex-col overflow-hidden">
        <DialogHeader>
          <DialogTitle className="text-xl">
            {isEditMode ? "Edit Test Scenario" : "Create New Test Scenario"}
          </DialogTitle>
          <p className="text-sm text-muted-foreground">
            {isEditMode
              ? "Update the test scenario details"
              : showSuiteSelection
                ? "Add a new test scenario to a test suite"
                : "Add a new test scenario to this suite"}
          </p>
        </DialogHeader>

        <div className="flex-1 space-y-6 overflow-y-auto px-1 py-4">
          {/* Test Suite Selection */}
          {showSuiteSelection && (
            <div className="space-y-2">
              <Label htmlFor="testSuite">Test Suite</Label>
              <Select value={selectedSuiteId} onValueChange={setSelectedSuiteId}>
                <SelectTrigger id="testSuite">
                  <SelectValue placeholder="Select a test suite" />
                </SelectTrigger>
                <SelectContent>
                  {availableSuites.map((suite) => (
                    <SelectItem key={suite.id} value={suite.id}>
                      {suite.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {availableSuites.length === 0 && !loading && (
                <p className="text-sm text-muted-foreground">
                  No test suites available. Create one first.
                </p>
              )}
            </div>
          )}

          {/* Test Name */}
          <div className="space-y-2">
            <Label htmlFor="testTitle">Test Name *</Label>
            <Input
              id="testTitle"
              placeholder="e.g., Happy Path - Book Appointment"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>

          {/* Goal/Description */}
          <div className="space-y-2">
            <Label htmlFor="testDescription">Goal</Label>
            <Textarea
              id="testDescription"
              placeholder="Describe what this test scenario validates..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="resize-none"
            />
          </div>

          {/* Persona Selection */}
          <div className="space-y-2">
            <Label htmlFor="persona">Persona *</Label>
            <Select value={personaId} onValueChange={setPersonaId}>
              <SelectTrigger id="persona">
                <SelectValue placeholder="Select a persona" />
              </SelectTrigger>
              <SelectContent>
                {availablePersonas.map((persona) => (
                  <SelectItem key={persona.id} value={persona.id}>
                    {persona.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {availablePersonas.length === 0 && !loading && (
              <p className="text-sm text-muted-foreground">
                No personas available. Create one first.
              </p>
            )}
          </div>

          {/* Max Turns & Timeout */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="maxTurns">Max Turns</Label>
              <Input
                id="maxTurns"
                type="number"
                min="1"
                placeholder="10"
                value={maxTurns}
                onChange={(e) => setMaxTurns(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="timeout">Timeout (seconds)</Label>
              <Input
                id="timeout"
                type="number"
                min="1"
                placeholder="300"
                value={timeout}
                onChange={(e) => setTimeout(e.target.value)}
              />
            </div>
          </div>

          {/* Caller Behaviors (Optional) */}
          <div className="space-y-2">
            <Label>Caller Behaviors (Optional)</Label>
            <p className="text-sm text-muted-foreground">
              Steps the simulated caller should perform during the test
            </p>
            <div className="space-y-2">
              {callerBehaviors.map((behavior, index) => (
                <div key={index} className="flex items-center gap-2">
                  <Input
                    value={behavior}
                    onChange={(e) => handleCallerBehaviorChange(index, e.target.value)}
                    placeholder={`Step ${index + 1}`}
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() => handleRemoveCallerBehavior(index)}
                    className="h-9 w-9 shrink-0"
                  >
                    <X className="h-4 w-4" />
                    <span className="sr-only">Remove step</span>
                  </Button>
                </div>
              ))}
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleAddCallerBehavior}
                className="mt-1"
              >
                <Plus className="mr-1 h-4 w-4" />
                Add Step
              </Button>
            </div>
          </div>

          {/* Tags/Intents (Optional) */}
          <div className="space-y-2">
            <Label htmlFor="tags">Tags (Optional)</Label>
            <Input
              id="tags"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="e.g., happy-path, booking, regression (comma-separated)"
            />
            <p className="text-sm text-muted-foreground">
              Comma-separated list of tags to categorize this test scenario
            </p>
          </div>
        </div>

        <DialogFooter className="border-t pt-4">
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={!isValid || isSubmitting}>
            {isEditMode ? (
              isSubmitting ? (
                "Saving..."
              ) : (
                "Save Changes"
              )
            ) : (
              <>
                <Plus className="mr-2 h-4 w-4" />
                {isSubmitting ? "Creating..." : "Create Test"}
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
