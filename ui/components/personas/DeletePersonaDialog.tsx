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
} from "@/components/primitives/alert-dialog";
import type { PersonaListItem } from "@/lib/types";

interface DeletePersonaDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  persona: PersonaListItem | null;
  onDelete: () => Promise<void>;
  isDeleting?: boolean;
}

export function DeletePersonaDialog({
  open,
  onOpenChange,
  persona,
  onDelete,
  isDeleting = false,
}: DeletePersonaDialogProps) {
  if (!persona) return null;

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete Persona</AlertDialogTitle>
          <AlertDialogDescription>
            Are you sure you want to delete &quot;{persona.name}&quot;? This action cannot be
            undone.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={async (e) => {
              e.preventDefault();
              await onDelete();
            }}
            disabled={isDeleting}
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
          >
            {isDeleting ? "Deleting..." : "Delete"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
