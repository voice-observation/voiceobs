import { render, screen } from "@testing-library/react";
import { AgentStatusBadge } from "../AgentStatusBadge";
import type { ConnectionStatus } from "@/lib/types";

describe("AgentStatusBadge", () => {
  describe("connection status display", () => {
    it("renders verified status with correct label and icon", () => {
      render(<AgentStatusBadge connectionStatus="verified" isActive={true} />);
      expect(screen.getByText("Verified")).toBeInTheDocument();
    });

    it("renders pending status with correct label", () => {
      render(<AgentStatusBadge connectionStatus="pending" isActive={true} />);
      expect(screen.getByText("Pending")).toBeInTheDocument();
    });

    it("renders saved status with correct label", () => {
      render(<AgentStatusBadge connectionStatus="saved" isActive={true} />);
      expect(screen.getByText("Saved")).toBeInTheDocument();
    });

    it("renders connecting status with verifying label", () => {
      render(<AgentStatusBadge connectionStatus="connecting" isActive={true} />);
      expect(screen.getByText("Verifying...")).toBeInTheDocument();
    });

    it("renders failed status with correct label", () => {
      render(<AgentStatusBadge connectionStatus="failed" isActive={true} />);
      expect(screen.getByText("Failed")).toBeInTheDocument();
    });

    it("falls back to pending for unknown status", () => {
      render(<AgentStatusBadge connectionStatus={"unknown" as ConnectionStatus} isActive={true} />);
      expect(screen.getByText("Pending")).toBeInTheDocument();
    });
  });

  describe("active status display", () => {
    it("shows Active badge when isActive is true", () => {
      render(<AgentStatusBadge connectionStatus="verified" isActive={true} />);
      expect(screen.getByText("Active")).toBeInTheDocument();
    });

    it("shows Inactive badge when isActive is false", () => {
      render(<AgentStatusBadge connectionStatus="verified" isActive={false} />);
      expect(screen.getByText("Inactive")).toBeInTheDocument();
    });

    it("hides active status when showActiveStatus is false", () => {
      render(
        <AgentStatusBadge connectionStatus="verified" isActive={true} showActiveStatus={false} />
      );
      expect(screen.queryByText("Active")).not.toBeInTheDocument();
      expect(screen.queryByText("Inactive")).not.toBeInTheDocument();
    });

    it("shows active status by default (showActiveStatus defaults to true)", () => {
      render(<AgentStatusBadge connectionStatus="verified" isActive={true} />);
      expect(screen.getByText("Active")).toBeInTheDocument();
    });
  });

  describe("badge variants", () => {
    it("applies default variant for verified status", () => {
      const { container } = render(
        <AgentStatusBadge connectionStatus="verified" isActive={true} />
      );
      const badge = container.querySelector('[class*="bg-primary"]');
      expect(badge).toBeInTheDocument();
    });

    it("applies destructive variant for failed status", () => {
      const { container } = render(<AgentStatusBadge connectionStatus="failed" isActive={true} />);
      const badge = container.querySelector('[class*="bg-destructive"]');
      expect(badge).toBeInTheDocument();
    });
  });
});
