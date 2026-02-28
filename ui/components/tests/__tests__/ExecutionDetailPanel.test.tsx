import { render, screen } from "@testing-library/react";
import { ExecutionDetailPanel } from "../ExecutionDetailPanel";

jest.mock("@/lib/api", () => ({
  api: {
    suiteRuns: {
      getExecutionAudioUrl: jest.fn().mockResolvedValue({ url: "https://example.com/audio.wav" }),
    },
  },
}));

const mockExecution = {
  id: "exec-1",
  scenario_id: "scenario-1",
  scenario_name: "Order status check",
  status: "completed" as const,
  attempt: 1,
  max_attempts: 3,
  audio_url: "https://example.com/audio.wav",
  transcript: [
    { role: "persona" as const, text: "Hi", timestamp_ms: 0 },
    { role: "agent" as const, text: "Hello", timestamp_ms: 500 },
  ],
  evaluation_result: {
    passed: true,
    score: 0.9,
    goal_achieved: true,
    intent_handled: true,
    criteria: [] as { name: string; passed: boolean; score: number; evidence: string }[],
    reasoning: "Good response",
  },
  error_message: null,
  duration_seconds: null,
  started_at: null,
  completed_at: null,
};

describe("ExecutionDetailPanel", () => {
  it("renders audio player, transcript, and evaluation", () => {
    render(<ExecutionDetailPanel orgId="org-1" execution={mockExecution} />);
    expect(screen.getByText("Order status check")).toBeInTheDocument();
    expect(screen.getByText("Recording")).toBeInTheDocument();
    expect(screen.getByText("Transcript")).toBeInTheDocument();
    expect(screen.getByText("Evaluation")).toBeInTheDocument();
    expect(screen.getByText("Hi")).toBeInTheDocument();
    expect(screen.getByText("Hello")).toBeInTheDocument();
    expect(screen.getByText("Good response")).toBeInTheDocument();
  });

  it("shows error message when present", () => {
    const execWithError = { ...mockExecution, error_message: "Call failed" };
    render(<ExecutionDetailPanel orgId="org-1" execution={execWithError} />);
    expect(screen.getByText("Call failed")).toBeInTheDocument();
  });

  it("shows attempt count", () => {
    render(<ExecutionDetailPanel orgId="org-1" execution={mockExecution} />);
    expect(screen.getByText("Attempt 1 of 3")).toBeInTheDocument();
  });
});
