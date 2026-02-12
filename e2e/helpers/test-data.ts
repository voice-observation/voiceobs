/**
 * Generate unique test data to avoid conflicts across test runs
 */

export function generateOrgName(): string {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(7);
  return `E2ETest Org ${timestamp}-${random}`;
}

export function generateEmail(): string {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(7);
  return `e2e-${timestamp}-${random}@test.voiceobs.com`;
}

export function generatePersonaName(): string {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(7);
  return `E2E Test Persona ${timestamp}-${random}`;
}

/** Persona create payload matching backend PersonaCreateRequest */
export interface PersonaCreateData {
  name: string;
  description?: string | null;
  aggression?: number;
  patience?: number;
  verbosity?: number;
  traits?: string[];
  tts_provider?: string;
  tts_config?: Record<string, unknown>;
}

/** Valid traits from backend trait vocabulary - use for API and UI selection */
export const E2E_TRAITS = ["polite", "patient", "cooperative"] as const;

/** Elevenlabs model key from tts_provider_models.json - Brian voice */
export const E2E_ELEVENLABS_MODEL_KEY = "brian_turbo";

/** Elevenlabs model display text shown in dropdown (voice_name + key) */
export const E2E_ELEVENLABS_MODEL_DISPLAY = "Brian";

export function generatePersonaData(
  overrides?: Partial<PersonaCreateData>
): PersonaCreateData {
  return {
    name: generatePersonaName(),
    description: "E2E test persona for automated testing",
    aggression: 0.5,
    patience: 0.6,
    verbosity: 0.4,
    traits: [...E2E_TRAITS],
    tts_provider: "elevenlabs",
    tts_config: {
      voice_id: "ByWUwXA3MMLREYmxtB32",
      voice_name: "Brian",
      model_id: "eleven_turbo_v2_5",
    },
    ...overrides,
  };
}
