/**
 * Constants for test suite configuration and options.
 */

import { MessageSquare, Volume2, AlertCircle, RefreshCw } from "lucide-react";

export const testScopes = [
  { id: "core_flows", label: "Core flows (happy paths)" },
  { id: "common_mistakes", label: "Common user mistakes" },
  { id: "noise_interruptions", label: "Real-world noise & interruptions" },
  { id: "safety_adversarial", label: "Safety & adversarial behavior" },
];

export const edgeCases = [
  { id: "hesitations", label: 'Hesitations & filler words ("um", "uh")', icon: MessageSquare },
  { id: "interrupts", label: "User interrupts or changes mind", icon: RefreshCw },
  { id: "noisy_environments", label: "Noisy environments (car, cafe)", icon: Volume2 },
  { id: "adversarial", label: "Confusing or adversarial requests", icon: AlertCircle },
];

export const thoroughnessLabels = ["Light", "Standard", "Exhaustive"];

export const strictnessOptions = [
  { value: "strict", label: "Strict (exact intent match)" },
  { value: "balanced", label: "Balanced (recommended)" },
  { value: "flexible", label: "Flexible (semantic)" },
];
