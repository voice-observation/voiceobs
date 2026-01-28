"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter, useParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { TranscriptViewer } from "@/components/agents/TranscriptViewer";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { AgentStatusBadge } from "@/components/agents/AgentStatusBadge";
import { DeleteAgentDialog } from "@/components/agents/DeleteAgentDialog";
import { EditAgentDialog } from "@/components/agents/EditAgentDialog";
import { useAgentActions } from "@/hooks/useAgentActions";
import { api } from "@/lib/api";
import { logger } from "@/lib/logger";
import type { Agent } from "@/lib/types";
import {
  ArrowLeft,
  Pencil,
  Trash2,
  Phone,
  RefreshCw,
  AlertCircle,
  Clock,
  Power,
} from "lucide-react";

export default function AgentDetailPage() {
  const router = useRouter();
  const params = useParams();
  const agentId = params.id as string;

  const [agent, setAgent] = useState<Agent | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [editAgent, setEditAgent] = useState<Agent | null>(null);

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

  const { verifyAgent, toggleActive, verifyingIds, updatingIds } = useAgentActions({
    onVerified: fetchAgent,
    onDeleted: () => router.push("/agents"),
    onUpdated: fetchAgent,
    onActiveToggled: (_, isActive) => {
      setAgent((prev) => (prev ? { ...prev, is_active: isActive } : null));
    },
  });

  useEffect(() => {
    fetchAgent();
  }, [fetchAgent]);

  // Start polling if agent is currently verifying
  useEffect(() => {
    if (agent?.connection_status === "connecting" && !verifyingIds.has(agentId)) {
      verifyAgent(agentId);
    }
  }, [agent?.connection_status, agentId, verifyAgent, verifyingIds]);

  const handleToggleActive = async () => {
    if (!agent) return;

    // Optimistic update
    const previousIsActive = agent.is_active;
    setAgent((prev) => (prev ? { ...prev, is_active: !prev.is_active } : null));

    try {
      await toggleActive(agentId, previousIsActive);
    } catch {
      // Revert on error (hook already showed toast)
      setAgent((prev) => (prev ? { ...prev, is_active: previousIsActive } : null));
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "Never";
    return new Date(dateString).toLocaleString();
  };

  const isVerifying = verifyingIds.has(agentId);
  const isTogglingActive = updatingIds.has(agentId);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Skeleton className="h-10 w-10" />
          <Skeleton className="h-8 w-48" />
        </div>
        <Skeleton className="h-48 w-full" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-64 w-full" />
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
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => router.push("/agents")}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold">{agent.name}</h1>
            {agent.phone_number && (
              <div className="flex items-center gap-1 text-muted-foreground">
                <Phone className="h-4 w-4" />
                {agent.phone_number}
              </div>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={() => setEditAgent(agent)}>
            <Pencil className="mr-2 h-4 w-4" />
            Edit
          </Button>
          <Button variant="destructive" onClick={() => setDeleteDialogOpen(true)}>
            <Trash2 className="mr-2 h-4 w-4" />
            Delete
          </Button>
        </div>
      </div>

      {/* Status */}
      <div className="flex items-center justify-between">
        <AgentStatusBadge connectionStatus={agent.connection_status} isActive={agent.is_active} />
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Power
              className={`h-4 w-4 ${agent.is_active ? "text-green-500" : "text-muted-foreground"}`}
            />
            <Label htmlFor="active-toggle" className="text-sm font-medium">
              {agent.is_active ? "Active" : "Inactive"}
            </Label>
          </div>
          <Switch
            id="active-toggle"
            checked={agent.is_active}
            onCheckedChange={handleToggleActive}
            disabled={isTogglingActive}
          />
        </div>
      </div>

      {/* Description */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Description</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">{agent.description}</p>
        </CardContent>
      </Card>

      {/* Supported Intents */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Supported Intents</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {agent.supported_intents.map((intent) => (
              <Badge key={intent} variant="secondary">
                {intent}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Verification Status */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">Verification Status</CardTitle>
            <Button
              variant="outline"
              size="sm"
              onClick={() => verifyAgent(agentId)}
              disabled={isVerifying}
            >
              <RefreshCw className={`mr-2 h-4 w-4 ${isVerifying ? "animate-spin" : ""}`} />
              {isVerifying ? "Verifying..." : "Verify Again"}
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">Status</p>
              <AgentStatusBadge
                connectionStatus={agent.connection_status}
                isActive={agent.is_active}
                showActiveStatus={false}
              />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Attempts</p>
              <p className="font-medium">{agent.verification_attempts}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Last Verified</p>
              <div className="flex items-center gap-1">
                <Clock className="h-4 w-4 text-muted-foreground" />
                <span>{formatDate(agent.last_verification_at)}</span>
              </div>
            </div>
          </div>

          {agent.verification_error && (
            <div className="rounded-md bg-destructive/10 p-3">
              <div className="flex items-center gap-2 text-destructive">
                <AlertCircle className="h-4 w-4" />
                <p className="font-medium">Verification Error</p>
              </div>
              <p className="mt-1 text-sm text-destructive">{agent.verification_error}</p>
            </div>
          )}

          {agent.verification_reasoning && (
            <div className="rounded-md bg-muted p-3">
              <p className="text-sm font-medium">Reasoning</p>
              <p className="mt-1 text-sm text-muted-foreground">{agent.verification_reasoning}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Verification Transcript */}
      {agent.verification_transcript && agent.verification_transcript.length > 0 && (
        <Card>
          <CardContent className="p-0">
            <TranscriptViewer
              messages={agent.verification_transcript}
              title="Verification Transcript"
              defaultExpanded={agent.verification_transcript.length <= 10}
            />
          </CardContent>
        </Card>
      )}

      {/* Edit Agent Dialog */}
      <EditAgentDialog
        agent={editAgent}
        onOpenChange={(open) => !open && setEditAgent(null)}
        onUpdated={fetchAgent}
      />

      {/* Delete Confirmation Dialog */}
      <DeleteAgentDialog
        agentId={deleteDialogOpen ? agentId : null}
        agentName={agent.name}
        onOpenChange={setDeleteDialogOpen}
        onDeleted={() => router.push("/agents")}
      />
    </div>
  );
}
