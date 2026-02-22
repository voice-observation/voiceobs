"use client";

import { useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { useAuth } from "@/contexts/auth-context";

/**
 * Redirects /agents/[id]/edit to /orgs/[orgId]/agents/[id]/edit.
 * Agents are now org-scoped.
 */
export default function AgentEditRedirectPage() {
  const router = useRouter();
  const params = useParams();
  const agentId = params.id as string;
  const { activeOrg, isLoading } = useAuth();

  useEffect(() => {
    if (isLoading) return;

    if (activeOrg?.id) {
      router.replace(`/orgs/${activeOrg.id}/agents/${agentId}/edit`);
    } else {
      router.replace("/");
    }
  }, [activeOrg?.id, agentId, isLoading, router]);

  return null;
}
