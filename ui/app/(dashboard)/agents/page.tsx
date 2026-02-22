"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/auth-context";

/**
 * Redirects /agents to /orgs/[orgId]/agents.
 * Agents are now org-scoped.
 */
export default function AgentsRedirectPage() {
  const router = useRouter();
  const { activeOrg, isLoading } = useAuth();

  useEffect(() => {
    if (isLoading) return;

    if (activeOrg?.id) {
      router.replace(`/orgs/${activeOrg.id}/agents`);
    } else {
      router.replace("/");
    }
  }, [activeOrg?.id, isLoading, router]);

  return null;
}
