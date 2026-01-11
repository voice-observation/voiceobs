"use client";

import { useState } from "react";
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
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { PersonaCreateRequest } from "@/lib/types";

interface CreatePersonaDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreate: (data: PersonaCreateRequest) => Promise<void>;
}

export function CreatePersonaDialog({
  open,
  onOpenChange,
  onCreate,
}: CreatePersonaDialogProps) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [accent, setAccent] = useState<string>("");
  const [gender, setGender] = useState<"male" | "female" | "neutral">("neutral");
  const [backgroundNoise, setBackgroundNoise] = useState(false);
  const [temperature, setTemperature] = useState([0.7]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!name.trim() || !description.trim()) {
      return;
    }
    setIsSubmitting(true);
    try {
      await onCreate({
        name,
        description: description || null,
        aggression: 0.5, // Default value
        patience: 0.5, // Default value
        verbosity: 0.5, // Default value
        accent: accent ? accent.toLowerCase() : null,
        gender: gender || null,
        background_noise: backgroundNoise,
        temperature: temperature[0],
      });
      // Reset form
      setName("");
      setDescription("");
      setAccent("");
      setGender("neutral");
      setBackgroundNoise(false);
      setTemperature([0.7]);
      onOpenChange(false);
    } catch (error) {
      console.error("Failed to create persona:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const isValid = name.trim() && description.trim();

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Create New Persona</DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="name">Name</Label>
            <Input
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Friendly Assistant"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe the persona's speaking style and behavior..."
              rows={3}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="gender">Gender</Label>
              <Select value={gender} onValueChange={(v: "male" | "female" | "neutral") => setGender(v)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="male">Male</SelectItem>
                  <SelectItem value="female">Female</SelectItem>
                  <SelectItem value="neutral">Neutral</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="accent">Accent</Label>
              <Select value={accent} onValueChange={setAccent}>
                <SelectTrigger>
                  <SelectValue placeholder="Select accent" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="American">American</SelectItem>
                  <SelectItem value="British">British</SelectItem>
                  <SelectItem value="Australian">Australian</SelectItem>
                  <SelectItem value="Indian">Indian</SelectItem>
                  <SelectItem value="Canadian">Canadian</SelectItem>
                  <SelectItem value="Irish">Irish</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>Temperature: {temperature[0]}</Label>
            </div>
            <Slider
              value={temperature}
              onValueChange={setTemperature}
              max={1}
              min={0}
              step={0.1}
              className="w-full"
            />
          </div>

          <div className="flex items-center justify-between">
            <Label htmlFor="backgroundNoise">Background Noise</Label>
            <Switch
              id="backgroundNoise"
              checked={backgroundNoise}
              onCheckedChange={setBackgroundNoise}
            />
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
