"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/primitives/card";
import { Badge } from "@/components/primitives/badge";
import { Input } from "@/components/primitives/input";
import { Textarea } from "@/components/primitives/textarea";
import { Label } from "@/components/primitives/label";
import { Button } from "@/components/primitives/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/primitives/select";
import { Target, User, MessageSquare, AlertTriangle, Plus, Trash2, FolderOpen } from "lucide-react";
import { cn } from "@/lib/utils";
import type { TestScenario, PersonaListItem } from "@/lib/types";

export interface ScenarioEditForm {
  name: string;
  goal: string;
  intent: string;
  persona_id: string;
  caller_behaviors: string[];
  max_turns: number | null;
  tags: string[];
}

interface ScenarioDetailsCardProps {
  scenario: TestScenario;
  persona: PersonaListItem | null;
  personas?: PersonaListItem[];
  isEditing?: boolean;
  editForm?: ScenarioEditForm;
  onEditFormChange?: (form: ScenarioEditForm) => void;
}

export function ScenarioDetailsCard({
  scenario,
  persona,
  personas = [],
  isEditing = false,
  editForm,
  onEditFormChange,
}: ScenarioDetailsCardProps) {
  // Helper for persona badge color
  const getPersonaColor = (personaName: string): string => {
    const name = personaName.toLowerCase();
    if (name.includes("neutral") || name.includes("calm"))
      return "bg-blue-500/10 text-blue-600 border-blue-200";
    if (name.includes("rush") || name.includes("hurr") || name.includes("urgent"))
      return "bg-orange-500/10 text-orange-600 border-orange-200";
    if (name.includes("confus") || name.includes("uncertain"))
      return "bg-purple-500/10 text-purple-600 border-purple-200";
    if (name.includes("frustrat") || name.includes("angry") || name.includes("upset"))
      return "bg-red-500/10 text-red-600 border-red-200";
    if (name.includes("elder") || name.includes("senior"))
      return "bg-amber-500/10 text-amber-600 border-amber-200";
    if (name.includes("non-native") || name.includes("accent"))
      return "bg-teal-500/10 text-teal-600 border-teal-200";
    return "bg-muted text-muted-foreground border-muted";
  };

  // Helper functions for edit mode
  const updateFormField = <K extends keyof ScenarioEditForm>(
    field: K,
    value: ScenarioEditForm[K]
  ) => {
    if (editForm && onEditFormChange) {
      onEditFormChange({ ...editForm, [field]: value });
    }
  };

  const updateBehaviorAtIndex = (index: number, value: string) => {
    if (editForm && onEditFormChange) {
      const newBehaviors = [...editForm.caller_behaviors];
      newBehaviors[index] = value;
      onEditFormChange({ ...editForm, caller_behaviors: newBehaviors });
    }
  };

  const removeBehaviorAtIndex = (index: number) => {
    if (editForm && onEditFormChange) {
      const newBehaviors = editForm.caller_behaviors.filter((_, i) => i !== index);
      onEditFormChange({ ...editForm, caller_behaviors: newBehaviors });
    }
  };

  const addBehavior = () => {
    if (editForm && onEditFormChange) {
      onEditFormChange({
        ...editForm,
        caller_behaviors: [...editForm.caller_behaviors, ""],
      });
    }
  };

  const parseCommaSeparated = (value: string): string[] => {
    return value
      .split(",")
      .map((s) => s.trim())
      .filter((s) => s.length > 0);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Scenario Details</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {isEditing && editForm && onEditFormChange ? (
          <div className="space-y-4">
            {/* Row 1: Name + Persona */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Scenario Name</Label>
                <Input
                  value={editForm.name}
                  onChange={(e) => updateFormField("name", e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label>Persona</Label>
                <Select
                  value={editForm.persona_id}
                  onValueChange={(value) => updateFormField("persona_id", value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select a persona" />
                  </SelectTrigger>
                  <SelectContent>
                    {personas.map((p) => (
                      <SelectItem key={p.id} value={p.id}>
                        {p.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Goal */}
            <div className="space-y-2">
              <Label>Goal</Label>
              <Textarea
                value={editForm.goal}
                onChange={(e) => updateFormField("goal", e.target.value)}
                rows={2}
              />
            </div>

            {/* Intent */}
            <div className="space-y-2">
              <Label>Intent</Label>
              <Input
                value={editForm.intent}
                onChange={(e) => updateFormField("intent", e.target.value)}
                placeholder="e.g., billing_inquiry, support_request"
              />
            </div>

            {/* Caller Behaviors - dynamic list */}
            <div className="space-y-2">
              <Label>Caller Behaviors</Label>
              <div className="space-y-2">
                {editForm.caller_behaviors.map((behavior, index) => (
                  <div key={index} className="flex gap-2">
                    <Input
                      value={behavior}
                      onChange={(e) => updateBehaviorAtIndex(index, e.target.value)}
                    />
                    {editForm.caller_behaviors.length > 1 && (
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => removeBehaviorAtIndex(index)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                ))}
                <Button variant="outline" size="sm" onClick={addBehavior}>
                  <Plus className="mr-1 h-4 w-4" />
                  Add Behavior
                </Button>
              </div>
            </div>

            {/* Max Turns */}
            <div className="space-y-2">
              <Label>Max Turns</Label>
              <Input
                type="number"
                value={editForm.max_turns ?? ""}
                onChange={(e) =>
                  updateFormField("max_turns", e.target.value ? parseInt(e.target.value, 10) : null)
                }
              />
            </div>

            {/* Tags */}
            <div className="space-y-2">
              <Label>Tags (comma-separated)</Label>
              <Input
                value={editForm.tags.join(", ")}
                onChange={(e) => updateFormField("tags", parseCommaSeparated(e.target.value))}
              />
            </div>
          </div>
        ) : (
          <>
            {/* Goal Section */}
            <div>
              <div className="mb-1.5 flex items-center gap-2 text-xs text-muted-foreground">
                <Target className="h-3.5 w-3.5" />
                <span className="font-medium uppercase tracking-wide">Goal</span>
              </div>
              <div className="rounded-md bg-blue-500/10 px-3 py-2 text-sm text-foreground">
                {scenario.goal || "No goal specified"}
              </div>
            </div>

            {/* Intent Section */}
            {scenario.intent && (
              <div>
                <div className="mb-1.5 flex items-center gap-2 text-xs text-muted-foreground">
                  <FolderOpen className="h-3.5 w-3.5" />
                  <span className="font-medium uppercase tracking-wide">Intent</span>
                </div>
                <Badge variant="secondary">{scenario.intent}</Badge>
              </div>
            )}

            {/* Persona & Caller Behaviors - 2 column grid */}
            <div className="grid grid-cols-2 gap-6">
              <div>
                <div className="mb-1.5 flex items-center gap-2 text-xs text-muted-foreground">
                  <User className="h-3.5 w-3.5" />
                  <span className="font-medium uppercase tracking-wide">Persona</span>
                </div>
                {persona ? (
                  <Badge
                    variant="outline"
                    className={cn("capitalize", getPersonaColor(persona.name))}
                  >
                    {persona.name}
                  </Badge>
                ) : (
                  <span className="text-sm text-muted-foreground">Unknown</span>
                )}
              </div>
              <div>
                <div className="mb-1.5 flex items-center gap-2 text-xs text-muted-foreground">
                  <MessageSquare className="h-3.5 w-3.5" />
                  <span className="font-medium uppercase tracking-wide">Caller Behaviors</span>
                </div>
                {scenario.caller_behaviors && scenario.caller_behaviors.length > 0 ? (
                  <ul className="space-y-0.5 text-sm">
                    {scenario.caller_behaviors.map((behavior, i) => (
                      <li key={i} className="flex items-start gap-1.5">
                        <span className="text-muted-foreground">•</span>
                        <span>{behavior}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <span className="text-sm text-muted-foreground">None specified</span>
                )}
              </div>
            </div>

            {/* Constraints */}
            {scenario.max_turns && (
              <div>
                <div className="mb-1.5 flex items-center gap-2 text-xs text-muted-foreground">
                  <AlertTriangle className="h-3.5 w-3.5 text-orange-500" />
                  <span className="font-medium uppercase tracking-wide">Constraints</span>
                </div>
                <div className="rounded-md bg-orange-500/5 px-3 py-2 text-sm">
                  <span>
                    <span className="text-muted-foreground">Max turns:</span>{" "}
                    <span className="font-medium">{scenario.max_turns}</span>
                  </span>
                </div>
              </div>
            )}

            {/* Tags */}
            {scenario.tags && scenario.tags.length > 0 && (
              <div className="flex gap-1.5">
                {scenario.tags.map((tag) => (
                  <Badge key={tag} variant="secondary" className="text-xs">
                    {tag}
                  </Badge>
                ))}
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
