import { render, screen } from "@testing-library/react";
import { SuiteRunProgressCard } from "../SuiteRunProgressCard";

const mockSuiteRun = {
  id: "run-1",
  suite_id: "suite-1",
  status: "running" as const,
  total_scenarios: 4,
  completed_scenarios: 2,
  failed_scenarios: 0,
  triggered_by: null,
  started_at: null,
  completed_at: null,
  created_at: null,
  executions: [
    {
      id: "exec-1",
      scenario_id: "scenario-1",
      scenario_name: "Order pizza",
      status: "completed" as const,
      attempt: 1,
      max_attempts: 3,
      audio_url: null,
      transcript: null,
      evaluation_result: {
        passed: true,
        score: 0.9,
        goal_achieved: true,
        intent_handled: true,
        criteria: [],
        reasoning: "",
      },
      error_message: null,
      duration_seconds: null,
      started_at: null,
      completed_at: null,
    },
    {
      id: "exec-2",
      scenario_id: "scenario-2",
      scenario_name: "Cancel order",
      status: "calling" as const,
      attempt: 1,
      max_attempts: 3,
      audio_url: null,
      transcript: null,
      evaluation_result: null,
      error_message: null,
      duration_seconds: null,
      started_at: null,
      completed_at: null,
    },
  ],
};

describe("SuiteRunProgressCard", () => {
  it("renders progress bar and execution list", () => {
    render(<SuiteRunProgressCard suiteRun={mockSuiteRun} />);
    expect(screen.getByText("Running Tests")).toBeInTheDocument();
    expect(screen.getByText("[2/4]")).toBeInTheDocument();
    expect(screen.getByText("Order pizza")).toBeInTheDocument();
    expect(screen.getByText("Cancel order")).toBeInTheDocument();
  });

  it("shows Cancel button when run is not terminal", () => {
    const onCancel = jest.fn();
    render(<SuiteRunProgressCard suiteRun={mockSuiteRun} onCancel={onCancel} />);
    expect(screen.getByText("Cancel")).toBeInTheDocument();
  });

  it("does not show Cancel button when run is completed", () => {
    const completedRun = { ...mockSuiteRun, status: "completed" as const };
    render(<SuiteRunProgressCard suiteRun={completedRun} onCancel={jest.fn()} />);
    expect(screen.queryByText("Cancel")).not.toBeInTheDocument();
  });
});
