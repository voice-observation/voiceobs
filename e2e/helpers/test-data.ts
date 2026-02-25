/**
 * Generate unique test data to avoid conflicts across test runs
 */

import * as dotenv from 'dotenv';

dotenv.config({ path: '.env.test' });

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

/**
 * Phone number for agent creation in e2e tests.
 * Set E2E_TEST_PHONE_NUMBER in .env.test to use a number reachable by LiveKit SIP for verification.
 * Default +15551234567 may work if configured in the test environment.
 */
export function getE2ETestPhoneNumber(): string {
  return process.env.E2E_TEST_PHONE_NUMBER || '+15551234567';
}

/** Agent create payload matching backend AgentCreateRequest */
export interface AgentCreateData {
  name: string;
  goal: string; // backend uses "goal", frontend shows as "description"
  agent_type: string;
  contact_info: { phone_number: string };
  supported_intents: string[];
  context?: string;
}

/** Default intents from AgentConfigForm */
export const E2E_DEFAULT_INTENTS = [
  "Book",
  "Reschedule",
  "Cancel",
  "Ask hours",
  "Talk to human",
] as const;

export function generateAgentName(): string {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(7);
  return `E2E Test Agent ${timestamp}-${random}`;
}

export function generateAgentData(
  overrides?: Partial<AgentCreateData>
): AgentCreateData {
  return {
    name: generateAgentName(),
    goal: "E2E test agent for automated testing",
    agent_type: "phone",
    contact_info: { phone_number: getE2ETestPhoneNumber() },
    supported_intents: ["Book", "Cancel"],
    context: "Test agent for e2e testing",
    ...overrides,
  };
}

/** Test suite create payload matching backend TestSuiteCreateRequest */
export interface TestSuiteCreateData {
  name: string;
  description?: string;
  agent_id: string;
  test_scopes?: string[];
  thoroughness?: number;
  edge_cases?: string[];
  evaluation_strictness?: string;
}

export function generateTestSuiteName(): string {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(7);
  return `E2E Test Suite ${timestamp}-${random}`;
}

export function generateTestSuiteData(
  agentId: string,
  overrides?: Partial<TestSuiteCreateData>
): TestSuiteCreateData {
  return {
    name: generateTestSuiteName(),
    description: "E2E test suite for automated testing",
    agent_id: agentId,
    test_scopes: ["core_flows"],
    thoroughness: 0, // Light - fastest generation
    edge_cases: [],
    evaluation_strictness: "balanced",
    ...overrides,
  };
}
