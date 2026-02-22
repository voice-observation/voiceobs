"use client";

import { useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/contexts/auth-context";
import { Building2, ChevronDown, Check, Plus } from "lucide-react";
import { Button } from "@/components/primitives/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/primitives/dropdown-menu";
import { CreateOrgDialog } from "./CreateOrgDialog";

export function OrgSwitcher() {
  const router = useRouter();
  const pathname = usePathname();
  const { activeOrg, orgs, isLoading, switchOrg } = useAuth();
  const [createDialogOpen, setCreateDialogOpen] = useState(false);

  const handleSwitchOrg = (orgId: string) => {
    switchOrg(orgId);
    // Redirect if currently on org-scoped path (agents, test-suites)
    const orgScopedMatch = pathname?.match(/^\/orgs\/([^/]+)(\/.*)?$/);
    if (orgScopedMatch) {
      const newPath = `/orgs/${orgId}${orgScopedMatch[2] || ""}`;
      router.replace(newPath);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 px-3 py-2">
        <Building2 className="h-4 w-4 text-muted-foreground" />
        <span className="text-sm text-muted-foreground">Loading...</span>
      </div>
    );
  }

  if (!activeOrg) {
    return null;
  }

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" className="h-auto w-full justify-between px-3 py-2">
            <div className="flex min-w-0 items-center gap-2">
              <Building2 className="h-4 w-4 shrink-0 text-muted-foreground" />
              <span className="truncate text-sm font-medium">{activeOrg.name}</span>
            </div>
            <ChevronDown className="h-4 w-4 shrink-0 text-muted-foreground" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" className="w-56">
          {orgs.map((org) => (
            <DropdownMenuItem
              key={org.id}
              onClick={() => handleSwitchOrg(org.id)}
              className="flex items-center justify-between"
            >
              <span className="truncate">{org.name}</span>
              {org.id === activeOrg.id && <Check className="h-4 w-4 shrink-0" />}
            </DropdownMenuItem>
          ))}
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={() => setCreateDialogOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Create organization
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <CreateOrgDialog open={createDialogOpen} onOpenChange={setCreateDialogOpen} />
    </>
  );
}
