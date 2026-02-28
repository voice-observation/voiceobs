import { render, screen } from "@testing-library/react";
import { TranscriptViewer } from "../TranscriptViewer";

const mockTranscript = [
  {
    role: "persona" as const,
    text: "Hi, I need to check my order status",
    timestamp_ms: 0,
  },
  {
    role: "agent" as const,
    text: "Sure! Could you provide your order number?",
    timestamp_ms: 1500,
  },
  {
    role: "persona" as const,
    text: "It's 12345",
    timestamp_ms: 4000,
  },
];

describe("TranscriptViewer", () => {
  it("renders all transcript entries", () => {
    render(<TranscriptViewer transcript={mockTranscript} />);
    expect(screen.getByText("Hi, I need to check my order status")).toBeInTheDocument();
    expect(screen.getByText("Sure! Could you provide your order number?")).toBeInTheDocument();
    expect(screen.getByText("It's 12345")).toBeInTheDocument();
  });

  it("labels agent and persona messages", () => {
    render(<TranscriptViewer transcript={mockTranscript} />);
    expect(screen.getAllByText("Agent")).toHaveLength(1);
    expect(screen.getAllByText("Caller")).toHaveLength(2);
  });

  it("shows timestamps", () => {
    render(<TranscriptViewer transcript={mockTranscript} />);
    expect(screen.getByText("0:00")).toBeInTheDocument();
    expect(screen.getByText("0:01")).toBeInTheDocument();
    expect(screen.getByText("0:04")).toBeInTheDocument();
  });

  it("shows empty state when transcript is null", () => {
    render(<TranscriptViewer transcript={null} />);
    expect(screen.getByText(/no transcript/i)).toBeInTheDocument();
  });
});
