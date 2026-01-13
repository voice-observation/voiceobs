import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CheckboxCard } from "@/components/shared/CheckboxCard";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Wand2, Phone, HelpCircle, Plus } from "lucide-react";

interface AgentConfigFormProps {
  onGenerate?: () => void;
}

const DEFAULT_INTENTS = [
  { id: "book", label: "Book" },
  { id: "reschedule", label: "Reschedule" },
  { id: "cancel", label: "Cancel" },
  { id: "ask-hours", label: "Ask hours" },
  { id: "talk-to-human", label: "Talk to human" },
];

export function AgentConfigForm({ onGenerate }: AgentConfigFormProps) {
  const [phoneNumber, setPhoneNumber] = useState("");
  const [selectedIntents, setSelectedIntents] = useState<string[]>([]);
  const [customIntents, setCustomIntents] = useState<string[]>([]);
  const [newCustomIntent, setNewCustomIntent] = useState("");

  const handleIntentToggle = (intentId: string) => {
    setSelectedIntents((prev) =>
      prev.includes(intentId)
        ? prev.filter((id) => id !== intentId)
        : [...prev, intentId]
    );
  };

  const handleAddCustomIntent = () => {
    if (newCustomIntent.trim() && !customIntents.includes(newCustomIntent.trim())) {
      setCustomIntents((prev) => [...prev, newCustomIntent.trim()]);
      setNewCustomIntent("");
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

  return (
    <div className="space-y-6">
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
              defaultValue=""
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="goal">Agent Goal</Label>
            <p className="text-sm text-muted-foreground">
              In one sentence, what should this agent accomplish?
            </p>
            <Input
              id="goal"
              placeholder="Book dentist appointments and handle rescheduling."
              defaultValue=""
            />
          </div>

          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Label>Supported Agent Intents</Label>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <HelpCircle className="w-4 h-4 text-muted-foreground cursor-help" />
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Used to generate realistic test scenarios.</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
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
                <Plus className="w-4 h-4" />
              </Button>
            </div>
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
              <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                id="phone"
                type="tel"
                placeholder="+1 (555) 123-4567"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                className="pl-10"
              />
            </div>
            <p className="text-xs text-muted-foreground">
              Enter the phone number to call the voice agent
            </p>
          </div>
        </CardContent>
      </Card>

      <Button className="w-full" size="lg" onClick={onGenerate}>
        <Wand2 className="w-4 h-4 mr-2" />
        Save Agent
      </Button>
    </div>
  );
}
