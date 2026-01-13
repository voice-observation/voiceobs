"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Slider } from "@/components/ui/slider";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Zap } from "lucide-react";
import { api } from "@/lib/api";
import { logger } from "@/lib/logger";
import type { TestSuiteCreateRequest } from "@/lib/types";
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
  onCreate?: (suite: { id: string; name: string; description: string | null }) => void;
}

export function CreateTestSuiteDialog({
  open,
  onOpenChange,
  onCreate,
}: CreateTestSuiteDialogProps) {
  const [suiteName, setSuiteName] = useState("");
  const [description, setDescription] = useState("");
  const [selectedScopes, setSelectedScopes] = useState<string[]>(["core_flows", "common_mistakes"]);
  const [thoroughness, setThoroughness] = useState([1]); // 0: Light, 1: Standard, 2: Exhaustive
  const [selectedEdgeCases, setSelectedEdgeCases] = useState<string[]>([]);
  const [evaluationStrictness, setEvaluationStrictness] = useState("balanced");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleScopeToggle = (scope: string) => {
    setSelectedScopes((prev) =>
      prev.includes(scope)
        ? prev.filter((s) => s !== scope)
        : [...prev, scope]
    );
  };

  const handleEdgeCaseToggle = (edgeCase: string) => {
    setSelectedEdgeCases((prev) =>
      prev.includes(edgeCase)
        ? prev.filter((e) => e !== edgeCase)
        : [...prev, edgeCase]
    );
  };

  const handleGenerate = async () => {
    if (!suiteName.trim()) {
      return;
    }

    setIsSubmitting(true);
    try {
      const requestData: TestSuiteCreateRequest = {
        name: suiteName,
        description: description || null,
      };

      const newSuite = await api.testSuites.createTestSuite(requestData);

      logger.info("Test suite created", { suiteId: newSuite.id, suiteName: newSuite.name });

      if (onCreate) {
        onCreate(newSuite);
      }

      // Reset form
      setSuiteName("");
      setDescription("");
      setSelectedScopes(["core_flows", "common_mistakes"]);
      setSelectedEdgeCases([]);
      setThoroughness([1]);
      setEvaluationStrictness("balanced");
      onOpenChange(false);
    } catch (error) {
      logger.error("Failed to create test suite", error);
      throw error; // Re-throw to let parent handle it
    } finally {
      setIsSubmitting(false);
    }
  };

  const isValid = suiteName.trim().length > 0;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-xl">Create New Test Suite</DialogTitle>
          <p className="text-sm text-muted-foreground">
            Generate synthetic test cases for your voice bot
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
            <div className="px-2 pt-2 pb-4">
              <Slider
                value={thoroughness}
                onValueChange={setThoroughness}
                max={2}
                step={1}
                className="w-full"
              />
              <div className="flex justify-between mt-2 text-sm text-muted-foreground">
                {thoroughnessLabels.map((label, index) => (
                  <span
                    key={label}
                    className={thoroughness[0] === index ? "text-primary font-medium" : ""}
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
                  <Label htmlFor={option.value} className="cursor-pointer font-normal text-sm">
                    {option.label}
                  </Label>
                </div>
              ))}
            </RadioGroup>
          </div>
        </div>

        <div className="flex justify-end gap-3 pt-4 border-t">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleGenerate} disabled={!isValid || isSubmitting}>
            <Zap className="w-4 h-4 mr-2" />
            {isSubmitting ? "Creating..." : "Generate Tests"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
