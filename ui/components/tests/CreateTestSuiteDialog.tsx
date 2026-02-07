"use client";

import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/primitives/dialog";
import { Button } from "@/components/primitives/button";
import { Input } from "@/components/primitives/input";
import { Label } from "@/components/primitives/label";
import { Textarea } from "@/components/primitives/textarea";
import { Slider } from "@/components/primitives/slider";
import { RadioGroup, RadioGroupItem } from "@/components/primitives/radio-group";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/primitives/select";
import { Zap, Save } from "lucide-react";
import { api } from "@/lib/api";
import { logger } from "@/lib/logger";
import type { TestSuite, TestSuiteCreateRequest, AgentListItem } from "@/lib/types";
import { CheckboxCard } from "@/components/shared/CheckboxCard";
import {
  testScopes,
  edgeCases,
  thoroughnessLabels,
  strictnessOptions,
} from "@/lib/constants/testSuiteConstants";

interface CreateTestSuiteDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** Callback when test suite is created - receives the full TestSuite from API */
  onCreate?: (suite: TestSuite) => void;
  /** When provided, dialog operates in edit mode */
  testSuite?: TestSuite;
  /** Callback when test suite is updated (edit mode) */
  onUpdate?: (suite: TestSuite) => void;
}

export function CreateTestSuiteDialog({
  open,
  onOpenChange,
  onCreate,
  testSuite,
  onUpdate,
}: CreateTestSuiteDialogProps) {
  const isEditMode = !!testSuite;

  const [suiteName, setSuiteName] = useState("");
  const [description, setDescription] = useState("");
  const [agents, setAgents] = useState<AgentListItem[]>([]);
  const [agentId, setAgentId] = useState<string>("");
  const [selectedScopes, setSelectedScopes] = useState<string[]>(["core_flows", "common_mistakes"]);
  const [thoroughness, setThoroughness] = useState([1]); // 0: Light, 1: Standard, 2: Exhaustive
  const [selectedEdgeCases, setSelectedEdgeCases] = useState<string[]>([]);
  const [evaluationStrictness, setEvaluationStrictness] = useState("balanced");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Fetch verified agents when dialog opens
  useEffect(() => {
    const fetchAgents = async () => {
      try {
        const response = await api.agents.listAgents("verified");
        setAgents(response.agents);
      } catch (err) {
        logger.error("Failed to fetch agents", err);
      }
    };
    if (open) {
      fetchAgents();
    }
  }, [open]);

  // Pre-populate form when editing
  useEffect(() => {
    if (testSuite && open) {
      setSuiteName(testSuite.name);
      setDescription(testSuite.description || "");
      setAgentId(testSuite.agent_id || "");
      setSelectedScopes(
        testSuite.test_scopes?.length > 0
          ? testSuite.test_scopes
          : ["core_flows", "common_mistakes"]
      );
      setThoroughness([testSuite.thoroughness ?? 1]);
      setSelectedEdgeCases(testSuite.edge_cases || []);
      setEvaluationStrictness(testSuite.evaluation_strictness || "balanced");
    } else if (!open) {
      // Reset form when dialog closes
      setSuiteName("");
      setDescription("");
      setAgentId("");
      setSelectedScopes(["core_flows", "common_mistakes"]);
      setSelectedEdgeCases([]);
      setThoroughness([1]);
      setEvaluationStrictness("balanced");
    }
  }, [testSuite, open]);

  const handleScopeToggle = (scope: string) => {
    setSelectedScopes((prev) =>
      prev.includes(scope) ? prev.filter((s) => s !== scope) : [...prev, scope]
    );
  };

  const handleEdgeCaseToggle = (edgeCase: string) => {
    setSelectedEdgeCases((prev) =>
      prev.includes(edgeCase) ? prev.filter((e) => e !== edgeCase) : [...prev, edgeCase]
    );
  };

  const handleSubmit = async () => {
    if (!suiteName.trim()) {
      return;
    }

    setIsSubmitting(true);
    try {
      if (isEditMode && testSuite) {
        // Update existing suite - only name and description can be changed
        // Other fields (agent_id, test_scopes, thoroughness, etc.) are immutable
        // because changing them would invalidate existing generated scenarios
        const updatedSuite = await api.testSuites.updateTestSuite(testSuite.id, {
          name: suiteName,
          description: description || null,
        });

        logger.info("Test suite updated", {
          suiteId: updatedSuite.id,
          suiteName: updatedSuite.name,
        });

        if (onUpdate) {
          onUpdate(updatedSuite);
        }
      } else {
        // Create new suite
        const requestData: TestSuiteCreateRequest = {
          name: suiteName,
          description: description || null,
          agent_id: agentId,
          test_scopes: selectedScopes,
          thoroughness: thoroughness[0],
          edge_cases: selectedEdgeCases,
          evaluation_strictness: evaluationStrictness,
        };

        const newSuite = await api.testSuites.createTestSuite(requestData);

        logger.info("Test suite created", { suiteId: newSuite.id, suiteName: newSuite.name });

        if (onCreate) {
          onCreate(newSuite);
        }
      }

      onOpenChange(false);
    } catch (error) {
      logger.error(
        isEditMode ? "Failed to update test suite" : "Failed to create test suite",
        error
      );
      throw error; // Re-throw to let parent handle it
    } finally {
      setIsSubmitting(false);
    }
  };

  const isValid = suiteName.trim().length > 0 && (isEditMode || agentId.length > 0);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] max-w-2xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-xl">
            {isEditMode ? "Edit Test Suite" : "Create New Test Suite"}
          </DialogTitle>
          <p className="text-sm text-muted-foreground">
            {isEditMode
              ? "Only name and description can be changed. To modify test configuration, create a new suite."
              : "Generate synthetic test cases for your voice bot"}
          </p>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Suite Name */}
          <div className="space-y-2">
            <Label htmlFor="suiteName">Suite Name</Label>
            <Input
              id="suiteName"
              placeholder="e.g., Booking Flow - Edge Cases"
              value={suiteName}
              onChange={(e) => setSuiteName(e.target.value)}
            />
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              placeholder="Describe what this test suite covers..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
            />
          </div>

          {/* Configuration fields - only shown in create mode */}
          {!isEditMode && (
            <>
              {/* Agent Selector */}
              <div className="space-y-2">
                <Label htmlFor="agent">Agent *</Label>
                <Select value={agentId} onValueChange={setAgentId}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select an agent to test" />
                  </SelectTrigger>
                  <SelectContent>
                    {agents.map((agent) => (
                      <SelectItem key={agent.id} value={agent.id}>
                        {agent.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Test Scope */}
              <div className="space-y-3">
                <Label>Test Scope</Label>
                <p className="text-sm text-muted-foreground">What should this suite test?</p>
                <div className="grid grid-cols-2 gap-2">
                  {testScopes.map((scope) => (
                    <CheckboxCard
                      key={scope.id}
                      label={scope.label}
                      checked={selectedScopes.includes(scope.id)}
                      onCheckedChange={() => handleScopeToggle(scope.id)}
                    />
                  ))}
                </div>
              </div>

              {/* Test Thoroughness */}
              <div className="space-y-3">
                <Label>Test Thoroughness</Label>
                <div className="px-2 pb-4 pt-2">
                  <Slider
                    value={thoroughness}
                    onValueChange={setThoroughness}
                    max={2}
                    step={1}
                    className="w-full"
                  />
                  <div className="mt-2 flex justify-between text-sm text-muted-foreground">
                    {thoroughnessLabels.map((label, index) => (
                      <span
                        key={label}
                        className={thoroughness[0] === index ? "font-medium text-primary" : ""}
                      >
                        {label}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Edge Cases */}
              <div className="space-y-3">
                <Label>Include Edge Cases</Label>
                <div className="grid grid-cols-2 gap-2">
                  {edgeCases.map((edgeCase) => (
                    <CheckboxCard
                      key={edgeCase.id}
                      label={edgeCase.label}
                      checked={selectedEdgeCases.includes(edgeCase.id)}
                      onCheckedChange={() => handleEdgeCaseToggle(edgeCase.id)}
                    />
                  ))}
                </div>
              </div>

              {/* Evaluation Strictness */}
              <div className="space-y-3">
                <Label>Evaluation Strictness</Label>
                <RadioGroup
                  value={evaluationStrictness}
                  onValueChange={setEvaluationStrictness}
                  className="flex gap-4"
                >
                  {strictnessOptions.map((option) => (
                    <div key={option.value} className="flex items-center gap-2">
                      <RadioGroupItem value={option.value} id={option.value} />
                      <Label htmlFor={option.value} className="cursor-pointer text-sm font-normal">
                        {option.label}
                      </Label>
                    </div>
                  ))}
                </RadioGroup>
              </div>
            </>
          )}
        </div>

        <div className="flex justify-end gap-3 border-t pt-4">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={!isValid || isSubmitting}>
            {isEditMode ? (
              <>
                <Save className="mr-2 h-4 w-4" />
                {isSubmitting ? "Saving..." : "Save Changes"}
              </>
            ) : (
              <>
                <Zap className="mr-2 h-4 w-4" />
                {isSubmitting ? "Creating..." : "Generate Tests"}
              </>
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
