"use client";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { useAgentActions } from "@/hooks/useAgentActions";
import { Loader2 } from "lucide-react";

interface DeleteAgentDialogProps {
  /** Agent ID to delete. null = dialog closed, string = dialog open for that agent */
  agentId: string | null;
  /** Agent name for display in confirmation message */
  agentName?: string;
  /** Called when dialog open state changes */
  onOpenChange: (open: boolean) => void;
  /** Called after successful deletion */
  onDeleted?: () => void;
}

/**
 * Self-contained delete confirmation dialog for agents.
 * Manages its own loading state and handles the delete API call.
 */
export function DeleteAgentDialog({
  agentId,
  agentName,
  onOpenChange,
  onDeleted,
}: DeleteAgentDialogProps) {
  const { deleteAgent, deletingIds } = useAgentActions({
    onDeleted: () => {
      onOpenChange(false);
      onDeleted?.();
    },
  });

  const isDeleting = agentId ? deletingIds.has(agentId) : false;

  const handleDelete = async () => {
    if (!agentId) return;
    await deleteAgent(agentId);
  };

  return (
    <AlertDialog open={!!agentId} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete Agent</AlertDialogTitle>
          <AlertDialogDescription>
            Are you sure you want to delete {agentName ? `"${agentName}"` : "this agent"}? This
            action cannot be undone.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={handleDelete}
            disabled={isDeleting}
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
          >
            {isDeleting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Deleting...
              </>
            ) : (
              "Delete"
            )}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
