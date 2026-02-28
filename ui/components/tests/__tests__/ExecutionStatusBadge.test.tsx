import { render, screen } from "@testing-library/react";
import { ExecutionStatusBadge } from "../ExecutionStatusBadge";

describe("ExecutionStatusBadge", () => {
  it("shows 'Queued' for pending status", () => {
    render(<ExecutionStatusBadge status="pending" />);
    expect(screen.getByText("Queued")).toBeInTheDocument();
  });

  it("shows 'In Queue' for queued status", () => {
    render(<ExecutionStatusBadge status="queued" />);
    expect(screen.getByText("In Queue")).toBeInTheDocument();
  });

  it("shows 'Calling' for calling status", () => {
    render(<ExecutionStatusBadge status="calling" />);
    expect(screen.getByText("Calling")).toBeInTheDocument();
  });

  it("shows 'Evaluating' for evaluating status", () => {
    render(<ExecutionStatusBadge status="evaluating" />);
    expect(screen.getByText("Evaluating")).toBeInTheDocument();
  });

  it("shows 'Passed' for completed with passed evaluation", () => {
    render(<ExecutionStatusBadge status="completed" passed={true} />);
    expect(screen.getByText("Passed")).toBeInTheDocument();
  });

  it("shows 'Failed' for completed with failed evaluation", () => {
    render(<ExecutionStatusBadge status="completed" passed={false} />);
    expect(screen.getByText("Failed")).toBeInTheDocument();
  });

  it("shows 'Error' for failed status", () => {
    render(<ExecutionStatusBadge status="failed" />);
    expect(screen.getByText("Error")).toBeInTheDocument();
  });
});
