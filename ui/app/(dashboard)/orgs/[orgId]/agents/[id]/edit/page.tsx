"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter, useParams } from "next/navigation";
import { Button } from "@/components/primitives/button";
import { Card, CardContent } from "@/components/primitives/card";
import { Skeleton } from "@/components/primitives/skeleton";
import { AgentConfigForm } from "@/components/agents/AgentConfigForm";
import { useVerificationPolling } from "@/hooks/useVerificationPolling";
import { api } from "@/lib/api";
import { logger } from "@/lib/logger";
import { toast } from "sonner";
import type { Agent, AgentUpdateRequest } from "@/lib/types";
import { ArrowLeft, AlertCircle } from "lucide-react";

export default function OrgAgentEditPage() {
  const router = useRouter();
  const params = useParams();
  const orgId = params.orgId as string;
  const agentId = params.id as string;
  const agentsBasePath = `/orgs/${orgId}/agents`;

  const [agent, setAgent] = useState<Agent | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const { startPolling } = useVerificationPolling({
    orgId,
    onComplete: (status, verificationError) => {
      if (status === "verified") {
        toast("Agent verified", { description: "The agent has been successfully verified." });
      } else if (status === "failed") {
        toast.error("Verification failed", {
          description: verificationError || "Agent verification failed.",
        });
      }
    },
  });

  const fetchAgent = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      if (!orgId) return;
      const data = await api.agents.getAgent(orgId, agentId);
      setAgent(data);
    } catch (err) {
      logger.error("Failed to fetch agent", err);
      setError(err instanceof Error ? err.message : "Failed to load agent");
    } finally {
      setLoading(false);
    }
  }, [orgId, agentId]);

  useEffect(() => {
    fetchAgent();
  }, [fetchAgent]);

  const handleSubmit = async (data: AgentUpdateRequest) => {
    try {
      const phoneChanged =
        data.phone_number !== undefined && data.phone_number !== agent?.phone_number;

      if (!orgId) return;
      await api.agents.updateAgent(orgId, agentId, data);

      if (phoneChanged) {
        toast("Agent updated", { description: "Re-verification in progress..." });
        startPolling(agentId);
      } else {
        toast("Agent updated");
      }

      router.push(`${agentsBasePath}/${agentId}`);
    } catch (err) {
      logger.error("Failed to update agent", err);
      toast.error("Failed to update agent", {
        description: err instanceof Error ? err.message : "Unknown error",
      });
      throw err;
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Skeleton className="h-10 w-10" />
          <Skeleton className="h-8 w-48" />
        </div>
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (error || !agent) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" onClick={() => router.push(agentsBasePath)} className="gap-2">
          <ArrowLeft className="h-4 w-4" />
          Back to Agents
        </Button>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-destructive">
              <AlertCircle className="h-5 w-5" />
              <p>{error || "Agent not found"}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => router.push(`${agentsBasePath}/${agentId}`)}
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold">Edit Agent</h1>
          <p className="text-muted-foreground">{agent.name}</p>
        </div>
      </div>

      <AgentConfigForm
        agent={agent}
        onSubmit={handleSubmit}
        onCancel={() => router.push(`${agentsBasePath}/${agentId}`)}
        submitLabel="Save Changes"
      />
    </div>
  );
}
