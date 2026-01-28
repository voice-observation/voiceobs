import { render, screen, fireEvent } from "@testing-library/react";
import { TranscriptViewer } from "../TranscriptViewer";

const mockMessages = [
  { role: "user", content: "Hello, I need help" },
  { role: "assistant", content: "Hi! How can I assist you today?" },
  { role: "user", content: "I want to book an appointment" },
  { role: "assistant", content: "Sure, let me help you with that." },
];

describe("TranscriptViewer", () => {
  describe("rendering", () => {
    it("returns null when messages array is empty", () => {
      const { container } = render(<TranscriptViewer messages={[]} />);
      expect(container.firstChild).toBeNull();
    });

    it("returns null when messages is undefined", () => {
      const { container } = render(
        <TranscriptViewer messages={undefined as unknown as typeof mockMessages} />
      );
      expect(container.firstChild).toBeNull();
    });

    it("renders the title", () => {
      render(<TranscriptViewer messages={mockMessages} />);
      expect(screen.getByText("Transcript")).toBeInTheDocument();
    });

    it("renders custom title when provided", () => {
      render(<TranscriptViewer messages={mockMessages} title="Call Recording" />);
      expect(screen.getByText("Call Recording")).toBeInTheDocument();
    });

    it("displays message count", () => {
      render(<TranscriptViewer messages={mockMessages} />);
      expect(screen.getByText("4 messages")).toBeInTheDocument();
    });
  });

  describe("expand/collapse behavior", () => {
    it("is collapsed by default", () => {
      render(<TranscriptViewer messages={mockMessages} />);
      expect(screen.getByText("Expand")).toBeInTheDocument();
      expect(screen.queryByText("Hello, I need help")).not.toBeInTheDocument();
    });

    it("expands when defaultExpanded is true", () => {
      render(<TranscriptViewer messages={mockMessages} defaultExpanded={true} />);
      expect(screen.getByText("Collapse")).toBeInTheDocument();
      expect(screen.getByText("Hello, I need help")).toBeInTheDocument();
    });

    it("toggles expanded state when header is clicked", () => {
      render(<TranscriptViewer messages={mockMessages} />);

      // Initially collapsed
      expect(screen.getByText("Expand")).toBeInTheDocument();
      expect(screen.queryByText("Hello, I need help")).not.toBeInTheDocument();

      // Click to expand
      fireEvent.click(screen.getByRole("button"));
      expect(screen.getByText("Collapse")).toBeInTheDocument();
      expect(screen.getByText("Hello, I need help")).toBeInTheDocument();

      // Click to collapse
      fireEvent.click(screen.getByRole("button"));
      expect(screen.getByText("Expand")).toBeInTheDocument();
      expect(screen.queryByText("Hello, I need help")).not.toBeInTheDocument();
    });
  });

  describe("message display", () => {
    it("renders all messages when expanded", () => {
      render(<TranscriptViewer messages={mockMessages} defaultExpanded={true} />);
      expect(screen.getByText("Hello, I need help")).toBeInTheDocument();
      expect(screen.getByText("Hi! How can I assist you today?")).toBeInTheDocument();
      expect(screen.getByText("I want to book an appointment")).toBeInTheDocument();
      expect(screen.getByText("Sure, let me help you with that.")).toBeInTheDocument();
    });

    it("displays Agent label for assistant messages", () => {
      render(<TranscriptViewer messages={mockMessages} defaultExpanded={true} />);
      const agentLabels = screen.getAllByText("Agent");
      expect(agentLabels.length).toBe(2); // Two assistant messages
    });

    it("displays System label for user messages", () => {
      render(<TranscriptViewer messages={mockMessages} defaultExpanded={true} />);
      const systemLabels = screen.getAllByText("System");
      expect(systemLabels.length).toBe(2); // Two user messages
    });
  });

  describe("styling", () => {
    it("applies maxHeight style when provided", () => {
      const { container } = render(
        <TranscriptViewer messages={mockMessages} defaultExpanded={true} maxHeight="500px" />
      );
      const contentDiv = container.querySelector('[style*="max-height"]');
      expect(contentDiv).toHaveStyle({ maxHeight: "500px" });
    });

    it("uses default maxHeight of 24rem when not provided", () => {
      const { container } = render(
        <TranscriptViewer messages={mockMessages} defaultExpanded={true} />
      );
      const contentDiv = container.querySelector('[style*="max-height"]');
      expect(contentDiv).toHaveStyle({ maxHeight: "24rem" });
    });
  });
});
