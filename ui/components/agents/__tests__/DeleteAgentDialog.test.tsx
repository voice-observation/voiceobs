import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { DeleteAgentDialog } from "../DeleteAgentDialog";
import { api } from "@/lib/api";

// Mock the API
jest.mock("@/lib/api", () => ({
  api: {
    agents: {
      deleteAgent: jest.fn(),
    },
  },
}));

// Mock sonner toast
jest.mock("sonner", () => ({
  toast: Object.assign(jest.fn(), {
    error: jest.fn(),
    warning: jest.fn(),
    success: jest.fn(),
  }),
}));
const { toast: mockToast } = require("sonner") as {
  toast: jest.Mock & { error: jest.Mock; warning: jest.Mock; success: jest.Mock };
};

describe("DeleteAgentDialog", () => {
  const mockOnOpenChange = jest.fn();
  const mockOnDeleted = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("dialog visibility", () => {
    it("does not render when agentId is null", () => {
      render(
        <DeleteAgentDialog
          agentId={null}
          onOpenChange={mockOnOpenChange}
          onDeleted={mockOnDeleted}
        />
      );

      expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument();
    });

    it("renders when agentId is provided", () => {
      render(
        <DeleteAgentDialog
          agentId="agent-123"
          onOpenChange={mockOnOpenChange}
          onDeleted={mockOnDeleted}
        />
      );

      expect(screen.getByRole("alertdialog")).toBeInTheDocument();
    });
  });

  describe("dialog content", () => {
    it("displays delete confirmation title", () => {
      render(
        <DeleteAgentDialog
          agentId="agent-123"
          onOpenChange={mockOnOpenChange}
          onDeleted={mockOnDeleted}
        />
      );

      expect(screen.getByText("Delete Agent")).toBeInTheDocument();
    });

    it("displays agent name in confirmation message when provided", () => {
      render(
        <DeleteAgentDialog
          agentId="agent-123"
          agentName="Test Agent"
          onOpenChange={mockOnOpenChange}
          onDeleted={mockOnDeleted}
        />
      );

      expect(
        screen.getByText(/are you sure you want to delete "Test Agent"\?/i)
      ).toBeInTheDocument();
    });

    it("displays generic message when agent name is not provided", () => {
      render(
        <DeleteAgentDialog
          agentId="agent-123"
          onOpenChange={mockOnOpenChange}
          onDeleted={mockOnDeleted}
        />
      );

      expect(screen.getByText(/are you sure you want to delete this agent\?/i)).toBeInTheDocument();
    });

    it("shows warning about irreversible action", () => {
      render(
        <DeleteAgentDialog
          agentId="agent-123"
          onOpenChange={mockOnOpenChange}
          onDeleted={mockOnDeleted}
        />
      );

      expect(screen.getByText(/this action cannot be undone/i)).toBeInTheDocument();
    });
  });

  describe("cancel action", () => {
    it("renders cancel button", () => {
      render(
        <DeleteAgentDialog
          agentId="agent-123"
          onOpenChange={mockOnOpenChange}
          onDeleted={mockOnDeleted}
        />
      );

      expect(screen.getByRole("button", { name: /cancel/i })).toBeInTheDocument();
    });

    it("calls onOpenChange with false when cancel is clicked", () => {
      render(
        <DeleteAgentDialog
          agentId="agent-123"
          onOpenChange={mockOnOpenChange}
          onDeleted={mockOnDeleted}
        />
      );

      fireEvent.click(screen.getByRole("button", { name: /cancel/i }));

      expect(mockOnOpenChange).toHaveBeenCalledWith(false);
    });
  });

  describe("delete action", () => {
    it("renders delete button", () => {
      render(
        <DeleteAgentDialog
          agentId="agent-123"
          onOpenChange={mockOnOpenChange}
          onDeleted={mockOnDeleted}
        />
      );

      expect(screen.getByRole("button", { name: /^delete$/i })).toBeInTheDocument();
    });

    it("calls deleteAgent API when delete is clicked", async () => {
      (api.agents.deleteAgent as jest.Mock).mockResolvedValue(undefined);

      render(
        <DeleteAgentDialog
          agentId="agent-123"
          onOpenChange={mockOnOpenChange}
          onDeleted={mockOnDeleted}
        />
      );

      fireEvent.click(screen.getByRole("button", { name: /^delete$/i }));

      await waitFor(() => {
        expect(api.agents.deleteAgent).toHaveBeenCalledWith("agent-123");
      });
    });

    it("shows loading state while deleting", async () => {
      (api.agents.deleteAgent as jest.Mock).mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      );

      render(
        <DeleteAgentDialog
          agentId="agent-123"
          onOpenChange={mockOnOpenChange}
          onDeleted={mockOnDeleted}
        />
      );

      fireEvent.click(screen.getByRole("button", { name: /^delete$/i }));

      await waitFor(() => {
        expect(screen.getByText("Deleting...")).toBeInTheDocument();
      });
    });

    it("disables cancel button while deleting", async () => {
      (api.agents.deleteAgent as jest.Mock).mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      );

      render(
        <DeleteAgentDialog
          agentId="agent-123"
          onOpenChange={mockOnOpenChange}
          onDeleted={mockOnDeleted}
        />
      );

      fireEvent.click(screen.getByRole("button", { name: /^delete$/i }));

      await waitFor(() => {
        expect(screen.getByRole("button", { name: /cancel/i })).toBeDisabled();
      });
    });

    it("calls onDeleted callback after successful deletion", async () => {
      (api.agents.deleteAgent as jest.Mock).mockResolvedValue(undefined);

      render(
        <DeleteAgentDialog
          agentId="agent-123"
          onOpenChange={mockOnOpenChange}
          onDeleted={mockOnDeleted}
        />
      );

      fireEvent.click(screen.getByRole("button", { name: /^delete$/i }));

      await waitFor(() => {
        expect(mockOnDeleted).toHaveBeenCalled();
      });
    });

    it("closes dialog after successful deletion", async () => {
      (api.agents.deleteAgent as jest.Mock).mockResolvedValue(undefined);

      render(
        <DeleteAgentDialog
          agentId="agent-123"
          onOpenChange={mockOnOpenChange}
          onDeleted={mockOnDeleted}
        />
      );

      fireEvent.click(screen.getByRole("button", { name: /^delete$/i }));

      await waitFor(() => {
        expect(mockOnOpenChange).toHaveBeenCalledWith(false);
      });
    });

    it("shows success toast after successful deletion", async () => {
      (api.agents.deleteAgent as jest.Mock).mockResolvedValue(undefined);

      render(
        <DeleteAgentDialog
          agentId="agent-123"
          onOpenChange={mockOnOpenChange}
          onDeleted={mockOnDeleted}
        />
      );

      fireEvent.click(screen.getByRole("button", { name: /^delete$/i }));

      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith("Agent deleted");
      });
    });

    it("shows error toast when deletion fails", async () => {
      (api.agents.deleteAgent as jest.Mock).mockRejectedValue(new Error("Delete failed"));

      render(
        <DeleteAgentDialog
          agentId="agent-123"
          onOpenChange={mockOnOpenChange}
          onDeleted={mockOnDeleted}
        />
      );

      fireEvent.click(screen.getByRole("button", { name: /^delete$/i }));

      await waitFor(() => {
        expect(mockToast.error).toHaveBeenCalledWith("Failed to delete agent", expect.anything());
      });
    });

    it("does not call onDeleted when deletion fails", async () => {
      (api.agents.deleteAgent as jest.Mock).mockRejectedValue(new Error("Delete failed"));

      render(
        <DeleteAgentDialog
          agentId="agent-123"
          onOpenChange={mockOnOpenChange}
          onDeleted={mockOnDeleted}
        />
      );

      fireEvent.click(screen.getByRole("button", { name: /^delete$/i }));

      await waitFor(() => {
        expect(mockToast.error).toHaveBeenCalled();
      });

      expect(mockOnDeleted).not.toHaveBeenCalled();
    });

    it("does nothing if agentId is null when delete is triggered", async () => {
      // This shouldn't normally happen but tests the guard
      const { rerender } = render(
        <DeleteAgentDialog
          agentId="agent-123"
          onOpenChange={mockOnOpenChange}
          onDeleted={mockOnDeleted}
        />
      );

      // Get reference to delete button before changing agentId
      const deleteButton = screen.getByRole("button", { name: /^delete$/i });

      // Rerender with null agentId (simulating dialog closing)
      rerender(
        <DeleteAgentDialog
          agentId={null}
          onOpenChange={mockOnOpenChange}
          onDeleted={mockOnDeleted}
        />
      );

      // Dialog should be closed, so API should not be called
      expect(api.agents.deleteAgent).not.toHaveBeenCalled();
    });
  });
});
