import { render, screen } from "@testing-library/react";
import { EvaluationResultCard } from "../EvaluationResultCard";

const mockResult = {
  passed: true,
  score: 0.88,
  goal_achieved: true,
  intent_handled: true,
  criteria: [
    {
      name: "Greeting",
      passed: true,
      score: 0.95,
      evidence: "Agent said hello",
    },
    {
      name: "Order Confirmation",
      passed: false,
      score: 0.4,
      evidence: "Did not confirm",
    },
  ],
  reasoning: "The agent handled the request well overall.",
};

describe("EvaluationResultCard", () => {
  it("shows overall pass/fail badge", () => {
    render(<EvaluationResultCard result={mockResult} />);
    expect(screen.getByText("Passed")).toBeInTheDocument();
  });

  it("shows overall score", () => {
    render(<EvaluationResultCard result={mockResult} />);
    expect(screen.getByText("88%")).toBeInTheDocument();
  });

  it("shows criteria breakdown", () => {
    render(<EvaluationResultCard result={mockResult} />);
    expect(screen.getByText("Greeting")).toBeInTheDocument();
    expect(screen.getByText("Order Confirmation")).toBeInTheDocument();
  });

  it("shows reasoning", () => {
    render(<EvaluationResultCard result={mockResult} />);
    expect(screen.getByText("The agent handled the request well overall.")).toBeInTheDocument();
  });

  it("shows empty state when result is null", () => {
    render(<EvaluationResultCard result={null} />);
    expect(screen.getByText(/no evaluation/i)).toBeInTheDocument();
  });
});
