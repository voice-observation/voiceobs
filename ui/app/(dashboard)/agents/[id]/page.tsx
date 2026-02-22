"use client";

import { useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import { useAuth } from "@/contexts/auth-context";

/**
 * Redirects /agents/[id] to /orgs/[orgId]/agents/[id].
 * Agents are now org-scoped.
 */
export default function AgentDetailRedirectPage() {
  const router = useRouter();
  const params = useParams();
  const agentId = params.id as string;
  const { activeOrg, isLoading } = useAuth();

  useEffect(() => {
    if (isLoading) return;

    if (activeOrg?.id) {
      router.replace(`/orgs/${activeOrg.id}/agents/${agentId}`);
    } else {
      router.replace("/");
    }
  }, [activeOrg?.id, agentId, isLoading, router]);

  return null;
}
