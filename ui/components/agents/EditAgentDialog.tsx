"use client";

import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/primitives/dialog";
import { AgentConfigForm } from "@/components/agents/AgentConfigForm";
import { useAgentActions } from "@/hooks/useAgentActions";
import type { Agent, AgentCreateRequest, AgentUpdateRequest } from "@/lib/types";

interface EditAgentDialogProps {
  /** Agent to edit. null = dialog closed, Agent = dialog open with that agent */
  agent: Agent | null;
  /** Called when dialog open state changes */
  onOpenChange: (open: boolean) => void;
  /** Called after successful update */
  onUpdated?: (agent: Agent) => void;
}

/**
 * Self-contained edit dialog for agents.
 * Wraps AgentConfigForm and handles the update API call.
 */
export function EditAgentDialog({ agent, onOpenChange, onUpdated }: EditAgentDialogProps) {
  const { updateAgent } = useAgentActions({
    onUpdated: (updatedAgent) => {
      onOpenChange(false);
      onUpdated?.(updatedAgent);
    },
  });

  const handleSubmit = async (data: AgentCreateRequest | AgentUpdateRequest) => {
    if (!agent) return;

    const result = await updateAgent(agent.id, data as AgentUpdateRequest, agent.phone_number);

    // If update failed (returned null), throw to prevent form from closing
    if (!result) {
      throw new Error("Update failed");
    }
  };

  return (
    <Dialog open={!!agent} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] max-w-2xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Edit Agent</DialogTitle>
        </DialogHeader>
        {agent && (
          <AgentConfigForm
            agent={agent}
            onSubmit={handleSubmit}
            onCancel={() => onOpenChange(false)}
            submitLabel="Save Changes"
          />
        )}
      </DialogContent>
    </Dialog>
  );
}
