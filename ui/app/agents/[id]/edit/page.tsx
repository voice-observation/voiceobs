"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter, useParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { AgentConfigForm } from "@/components/agents/AgentConfigForm";
import { useVerificationPolling } from "@/hooks/useVerificationPolling";
import { api } from "@/lib/api";
import { logger } from "@/lib/logger";
import { useToast } from "@/hooks/use-toast";
import type { Agent, AgentUpdateRequest } from "@/lib/types";
import { ArrowLeft, AlertCircle } from "lucide-react";

export default function AgentEditPage() {
  const router = useRouter();
  const params = useParams();
  const { toast } = useToast();
  const agentId = params.id as string;

  const [agent, setAgent] = useState<Agent | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const { startPolling } = useVerificationPolling({
    onComplete: (status, verificationError) => {
      if (status === "verified") {
        toast({
          title: "Agent verified",
          description: "The agent has been successfully verified.",
        });
      } else if (status === "failed") {
        toast({
          title: "Verification failed",
          description: verificationError || "Agent verification failed.",
          variant: "destructive",
        });
      }
    },
  });

  const fetchAgent = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.agents.getAgent(agentId);
      setAgent(data);
    } catch (err) {
      logger.error("Failed to fetch agent", err);
      setError(err instanceof Error ? err.message : "Failed to load agent");
    } finally {
      setLoading(false);
    }
  }, [agentId]);

  useEffect(() => {
    fetchAgent();
  }, [fetchAgent]);

  const handleSubmit = async (data: AgentUpdateRequest) => {
    try {
      // Check if phone number changed (will trigger re-verification)
      const phoneChanged =
        data.phone_number !== undefined && data.phone_number !== agent?.phone_number;

      await api.agents.updateAgent(agentId, data);

      if (phoneChanged) {
        toast({
          title: "Agent updated",
          description: "Re-verification in progress...",
        });
        // Start polling for verification
        startPolling(agentId);
      } else {
        toast({
          title: "Agent updated",
        });
      }

      router.push(`/agents/${agentId}`);
    } catch (err) {
      logger.error("Failed to update agent", err);
      toast({
        title: "Failed to update agent",
        description: err instanceof Error ? err.message : "Unknown error",
        variant: "destructive",
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
        <Button variant="ghost" onClick={() => router.push("/agents")} className="gap-2">
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
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.push(`/agents/${agentId}`)}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold">Edit Agent</h1>
          <p className="text-muted-foreground">{agent.name}</p>
        </div>
      </div>

      {/* Form */}
      <AgentConfigForm
        agent={agent}
        onSubmit={handleSubmit}
        onCancel={() => router.push(`/agents/${agentId}`)}
        submitLabel="Save Changes"
      />
    </div>
  );
}
