"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/primitives/dialog";
import { Button } from "@/components/primitives/button";
import { Textarea } from "@/components/primitives/textarea";
import { Label } from "@/components/primitives/label";
import { Loader2, Sparkles } from "lucide-react";

interface GenerateMoreDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onGenerate: (prompt?: string) => Promise<void>;
  isGenerating: boolean;
}

/**
 * Dialog component for generating additional test scenarios using AI.
 * Allows users to optionally provide specific requirements or focus areas.
 */
export function GenerateMoreDialog({
  open,
  onOpenChange,
  onGenerate,
  isGenerating,
}: GenerateMoreDialogProps) {
  const [prompt, setPrompt] = useState("");

  const handleGenerate = async () => {
    await onGenerate(prompt || undefined);
    setPrompt("");
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5" />
            Generate More Scenarios
          </DialogTitle>
          <DialogDescription>
            Generate additional test scenarios using AI. Optionally provide specific requirements or
            focus areas.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="prompt">Additional Requirements (Optional)</Label>
            <Textarea
              id="prompt"
              placeholder="e.g., Generate scenarios for angry customers who want refunds..."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              rows={4}
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleGenerate} disabled={isGenerating}>
            {isGenerating ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Sparkles className="mr-2 h-4 w-4" />
                Generate
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
