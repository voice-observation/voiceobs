import { render, screen, fireEvent, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { AgentConfigForm } from "../AgentConfigForm";
import type { Agent, AgentCreateRequest, AgentUpdateRequest } from "@/lib/types";

// Mock the tooltip provider to avoid portal issues in tests
jest.mock("@/components/primitives/tooltip", () => ({
  TooltipProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  Tooltip: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  TooltipTrigger: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  TooltipContent: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

// Helper to find checkbox card by label
const findCheckboxCard = (label: string) => {
  return screen.getByText(label).closest("div[class*='cursor-pointer']");
};

// Helper to check if checkbox card is checked
const isCheckboxCardChecked = (label: string) => {
  const card = findCheckboxCard(label);
  return card?.classList.contains("border-primary");
};

const mockAgent: Agent = {
  id: "agent-123",
  name: "Test Agent",
  description: "A test agent for booking appointments",
  agent_type: "phone",
  phone_number: "+14155551234",
  connection_status: "verified",
  is_active: true,
  supported_intents: ["book", "cancel", "custom-intent"],
  verification_attempts: 1,
  last_verification_at: "2024-01-01T00:00:00Z",
  verification_error: null,
  verification_reasoning: null,
  verification_transcript: null,
  metadata: {},
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
  created_by: null,
};

describe("AgentConfigForm", () => {
  const mockOnSubmit = jest.fn();
  const mockOnCancel = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("create mode", () => {
    it("renders empty form in create mode", () => {
      render(<AgentConfigForm onSubmit={mockOnSubmit} />);

      expect(screen.getByLabelText(/agent name/i)).toHaveValue("");
      expect(screen.getByLabelText(/agent description/i)).toHaveValue("");
      expect(screen.getByPlaceholderText(/\+1 \(555\) 123-4567/)).toHaveValue("");
    });

    it("shows Create Agent button in create mode", () => {
      render(<AgentConfigForm onSubmit={mockOnSubmit} />);
      expect(screen.getByRole("button", { name: /create agent/i })).toBeInTheDocument();
    });

    it("shows custom submit label when provided", () => {
      render(<AgentConfigForm onSubmit={mockOnSubmit} submitLabel="Add Agent" />);
      expect(screen.getByRole("button", { name: /add agent/i })).toBeInTheDocument();
    });
  });

  describe("edit mode", () => {
    it("populates form with agent data in edit mode", () => {
      render(<AgentConfigForm agent={mockAgent} onSubmit={mockOnSubmit} />);

      expect(screen.getByLabelText(/agent name/i)).toHaveValue("Test Agent");
      expect(screen.getByLabelText(/agent description/i)).toHaveValue(
        "A test agent for booking appointments"
      );
      expect(screen.getByPlaceholderText(/\+1 \(555\) 123-4567/)).toHaveValue("+14155551234");
    });

    it("shows Save Changes button in edit mode", () => {
      render(<AgentConfigForm agent={mockAgent} onSubmit={mockOnSubmit} />);
      expect(screen.getByRole("button", { name: /save changes/i })).toBeInTheDocument();
    });

    it("pre-selects existing intents", () => {
      render(<AgentConfigForm agent={mockAgent} onSubmit={mockOnSubmit} />);

      // Book and Cancel are default intents that should be checked
      expect(isCheckboxCardChecked("Book")).toBe(true);
      expect(isCheckboxCardChecked("Cancel")).toBe(true);
    });
  });

  describe("validation", () => {
    it("shows error when name is empty", async () => {
      render(<AgentConfigForm onSubmit={mockOnSubmit} />);

      fireEvent.click(screen.getByRole("button", { name: /create agent/i }));

      await waitFor(() => {
        expect(screen.getByText("Name is required")).toBeInTheDocument();
      });
      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    it("shows error when name exceeds 255 characters", async () => {
      render(<AgentConfigForm onSubmit={mockOnSubmit} />);

      const longName = "a".repeat(256);
      fireEvent.change(screen.getByLabelText(/agent name/i), { target: { value: longName } });
      fireEvent.click(screen.getByRole("button", { name: /create agent/i }));

      await waitFor(() => {
        expect(screen.getByText("Name must be 255 characters or less")).toBeInTheDocument();
      });
    });

    it("shows error when description is empty", async () => {
      render(<AgentConfigForm onSubmit={mockOnSubmit} />);

      fireEvent.change(screen.getByLabelText(/agent name/i), { target: { value: "Test" } });
      fireEvent.click(screen.getByRole("button", { name: /create agent/i }));

      await waitFor(() => {
        expect(screen.getByText("Description is required")).toBeInTheDocument();
      });
    });

    it("shows error when phone number is empty", async () => {
      render(<AgentConfigForm onSubmit={mockOnSubmit} />);

      fireEvent.change(screen.getByLabelText(/agent name/i), { target: { value: "Test" } });
      fireEvent.change(screen.getByLabelText(/agent description/i), {
        target: { value: "Description" },
      });
      fireEvent.click(screen.getByRole("button", { name: /create agent/i }));

      await waitFor(() => {
        expect(screen.getByText("Phone number is required")).toBeInTheDocument();
      });
    });

    it("shows error for invalid phone number format", async () => {
      render(<AgentConfigForm onSubmit={mockOnSubmit} />);

      fireEvent.change(screen.getByLabelText(/agent name/i), { target: { value: "Test" } });
      fireEvent.change(screen.getByLabelText(/agent description/i), {
        target: { value: "Description" },
      });
      fireEvent.change(screen.getByPlaceholderText(/\+1 \(555\) 123-4567/), {
        target: { value: "invalid-phone" },
      });
      fireEvent.click(screen.getByRole("button", { name: /create agent/i }));

      await waitFor(() => {
        expect(
          screen.getByText("Please enter a valid phone number (E.164 format)")
        ).toBeInTheDocument();
      });
    });

    it("shows error when no intents are selected", async () => {
      render(<AgentConfigForm onSubmit={mockOnSubmit} />);

      fireEvent.change(screen.getByLabelText(/agent name/i), { target: { value: "Test" } });
      fireEvent.change(screen.getByLabelText(/agent description/i), {
        target: { value: "Description" },
      });
      fireEvent.change(screen.getByPlaceholderText(/\+1 \(555\) 123-4567/), {
        target: { value: "+14155551234" },
      });
      fireEvent.click(screen.getByRole("button", { name: /create agent/i }));

      await waitFor(() => {
        expect(screen.getByText("At least one intent is required")).toBeInTheDocument();
      });
    });

    it("clears intent error when user selects an intent", async () => {
      render(<AgentConfigForm onSubmit={mockOnSubmit} />);

      fireEvent.change(screen.getByLabelText(/agent name/i), { target: { value: "Test" } });
      fireEvent.change(screen.getByLabelText(/agent description/i), {
        target: { value: "Description" },
      });
      fireEvent.change(screen.getByPlaceholderText(/\+1 \(555\) 123-4567/), {
        target: { value: "+14155551234" },
      });
      fireEvent.click(screen.getByRole("button", { name: /create agent/i }));

      await waitFor(() => {
        expect(screen.getByText("At least one intent is required")).toBeInTheDocument();
      });

      // Select an intent
      const bookCard = findCheckboxCard("Book");
      if (bookCard) fireEvent.click(bookCard);

      await waitFor(() => {
        expect(screen.queryByText("At least one intent is required")).not.toBeInTheDocument();
      });
    });

    it("clears error when user provides valid input", async () => {
      render(<AgentConfigForm onSubmit={mockOnSubmit} />);

      // Trigger validation error
      fireEvent.click(screen.getByRole("button", { name: /create agent/i }));
      await waitFor(() => {
        expect(screen.getByText("Name is required")).toBeInTheDocument();
      });

      // Fix the error
      fireEvent.change(screen.getByLabelText(/agent name/i), { target: { value: "Test" } });

      await waitFor(() => {
        expect(screen.queryByText("Name is required")).not.toBeInTheDocument();
      });
    });
  });

  describe("form submission", () => {
    it("submits form with valid data in create mode", async () => {
      mockOnSubmit.mockResolvedValue(undefined);
      render(<AgentConfigForm onSubmit={mockOnSubmit} />);

      fireEvent.change(screen.getByLabelText(/agent name/i), { target: { value: "New Agent" } });
      fireEvent.change(screen.getByLabelText(/agent description/i), {
        target: { value: "New description" },
      });
      fireEvent.change(screen.getByPlaceholderText(/\+1 \(555\) 123-4567/), {
        target: { value: "+14155551234" },
      });
      const bookCard = findCheckboxCard("Book");
      if (bookCard) fireEvent.click(bookCard);
      fireEvent.click(screen.getByRole("button", { name: /create agent/i }));

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith({
          name: "New Agent",
          description: "New description",
          phone_number: "+14155551234",
          supported_intents: ["book"],
        });
      });
    });

    it("submits only changed fields in edit mode", async () => {
      mockOnSubmit.mockResolvedValue(undefined);
      render(<AgentConfigForm agent={mockAgent} onSubmit={mockOnSubmit} />);

      // Only change the name
      fireEvent.change(screen.getByLabelText(/agent name/i), {
        target: { value: "Updated Agent" },
      });
      fireEvent.click(screen.getByRole("button", { name: /save changes/i }));

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith({
          name: "Updated Agent",
        });
      });
    });

    it("shows loading state during submission", async () => {
      mockOnSubmit.mockImplementation(() => new Promise((resolve) => setTimeout(resolve, 100)));
      render(<AgentConfigForm onSubmit={mockOnSubmit} />);

      fireEvent.change(screen.getByLabelText(/agent name/i), { target: { value: "New Agent" } });
      fireEvent.change(screen.getByLabelText(/agent description/i), {
        target: { value: "New description" },
      });
      fireEvent.change(screen.getByPlaceholderText(/\+1 \(555\) 123-4567/), {
        target: { value: "+14155551234" },
      });
      const bookCard = findCheckboxCard("Book");
      if (bookCard) fireEvent.click(bookCard);
      fireEvent.click(screen.getByRole("button", { name: /create agent/i }));

      await waitFor(() => {
        expect(screen.getByText("Creating...")).toBeInTheDocument();
      });
    });

    it("shows saving state in edit mode during submission", async () => {
      mockOnSubmit.mockImplementation(() => new Promise((resolve) => setTimeout(resolve, 100)));
      render(<AgentConfigForm agent={mockAgent} onSubmit={mockOnSubmit} />);

      fireEvent.change(screen.getByLabelText(/agent name/i), {
        target: { value: "Updated Agent" },
      });
      fireEvent.click(screen.getByRole("button", { name: /save changes/i }));

      await waitFor(() => {
        expect(screen.getByText("Saving...")).toBeInTheDocument();
      });
    });
  });

  describe("intents management", () => {
    it("toggles intent selection", () => {
      render(<AgentConfigForm onSubmit={mockOnSubmit} />);

      expect(isCheckboxCardChecked("Book")).toBe(false);

      const bookCard = findCheckboxCard("Book");
      if (bookCard) fireEvent.click(bookCard);
      expect(isCheckboxCardChecked("Book")).toBe(true);

      if (bookCard) fireEvent.click(bookCard);
      expect(isCheckboxCardChecked("Book")).toBe(false);
    });

    it("adds custom intent", async () => {
      render(<AgentConfigForm onSubmit={mockOnSubmit} />);

      const customInput = screen.getByPlaceholderText("Add custom intent...");
      fireEvent.change(customInput, { target: { value: "custom-action" } });

      // Find the add button - it's the button next to the custom intent input
      // The button should not be disabled since we have text in the input
      const inputContainer = customInput.parentElement;
      const addButton = inputContainer?.querySelector('button[type="button"]');

      if (addButton) {
        fireEvent.click(addButton);
      }

      // Check that the custom intent appears
      await waitFor(() => {
        expect(screen.getByText("custom-action")).toBeInTheDocument();
      });
    });

    it("adds custom intent when Enter is pressed", async () => {
      render(<AgentConfigForm onSubmit={mockOnSubmit} />);

      const customInput = screen.getByPlaceholderText("Add custom intent...");
      fireEvent.change(customInput, { target: { value: "enter-intent" } });
      fireEvent.keyDown(customInput, { key: "Enter" });

      await waitFor(() => {
        expect(screen.getByText("enter-intent")).toBeInTheDocument();
      });
    });

    it("prevents duplicate custom intents", async () => {
      render(<AgentConfigForm onSubmit={mockOnSubmit} />);

      const customInput = screen.getByPlaceholderText("Add custom intent...");

      // Add first custom intent
      fireEvent.change(customInput, { target: { value: "unique-intent" } });
      fireEvent.keyDown(customInput, { key: "Enter" });

      // Try to add the same intent again
      fireEvent.change(customInput, { target: { value: "unique-intent" } });
      fireEvent.keyDown(customInput, { key: "Enter" });

      // Should only have one element for this intent
      const intents = screen.getAllByText("unique-intent");
      expect(intents.length).toBe(1);
    });

    it("removes custom intent when clicked", async () => {
      render(<AgentConfigForm onSubmit={mockOnSubmit} />);

      // Add custom intent
      const customInput = screen.getByPlaceholderText("Add custom intent...");
      fireEvent.change(customInput, { target: { value: "removable-intent" } });
      fireEvent.keyDown(customInput, { key: "Enter" });

      // Verify it's there
      expect(screen.getByText("removable-intent")).toBeInTheDocument();

      // Remove it by clicking the card
      const card = findCheckboxCard("removable-intent");
      if (card) fireEvent.click(card);

      // Verify it's gone
      await waitFor(() => {
        expect(screen.queryByText("removable-intent")).not.toBeInTheDocument();
      });
    });
  });

  describe("cancel button", () => {
    it("shows cancel button when onCancel is provided", () => {
      render(<AgentConfigForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);
      expect(screen.getByRole("button", { name: /cancel/i })).toBeInTheDocument();
    });

    it("hides cancel button when onCancel is not provided", () => {
      render(<AgentConfigForm onSubmit={mockOnSubmit} />);
      expect(screen.queryByRole("button", { name: /cancel/i })).not.toBeInTheDocument();
    });

    it("calls onCancel when cancel button is clicked", () => {
      render(<AgentConfigForm onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);
      fireEvent.click(screen.getByRole("button", { name: /cancel/i }));
      expect(mockOnCancel).toHaveBeenCalled();
    });

    it("disables cancel button during submission", async () => {
      mockOnSubmit.mockImplementation(() => new Promise((resolve) => setTimeout(resolve, 100)));
      render(<AgentConfigForm agent={mockAgent} onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);

      fireEvent.change(screen.getByLabelText(/agent name/i), {
        target: { value: "Updated" },
      });
      fireEvent.click(screen.getByRole("button", { name: /save changes/i }));

      await waitFor(() => {
        expect(screen.getByRole("button", { name: /cancel/i })).toBeDisabled();
      });
    });
  });
});
