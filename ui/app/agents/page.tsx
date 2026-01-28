"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { AgentConfigForm } from "@/components/agents/AgentConfigForm";
import { AgentStatusBadge } from "@/components/agents/AgentStatusBadge";
import { DeleteAgentDialog } from "@/components/agents/DeleteAgentDialog";
import { EditAgentDialog } from "@/components/agents/EditAgentDialog";
import { useAgentActions } from "@/hooks/useAgentActions";
import { api } from "@/lib/api";
import { logger } from "@/lib/logger";
import { useToast } from "@/hooks/use-toast";
import type { Agent, AgentListItem, AgentCreateRequest, AgentUpdateRequest } from "@/lib/types";
import {
  Settings2,
  Plus,
  MoreVertical,
  Eye,
  Pencil,
  Power,
  Trash2,
  RefreshCw,
  AlertCircle,
  Phone,
} from "lucide-react";

export default function AgentsPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [agents, setAgents] = useState<AgentListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [editAgent, setEditAgent] = useState<Agent | null>(null);
  const [isEditLoading, setIsEditLoading] = useState(false);
  const [deleteAgentId, setDeleteAgentId] = useState<string | null>(null);

  const refreshAgentList = useCallback(async () => {
    try {
      const response = await api.agents.listAgents();
      setAgents(response.agents);
    } catch (err) {
      logger.error("Failed to refresh agents", err);
    }
  }, []);

  const { verifyAgent, resumePolling, toggleActive, verifyingIds } = useAgentActions({
    onVerified: refreshAgentList,
    onDeleted: () => {
      setAgents((prev) => prev.filter((a) => a.id !== deleteAgentId));
    },
    onUpdated: refreshAgentList,
    onActiveToggled: (agentId, isActive) => {
      setAgents((prev) => prev.map((a) => (a.id === agentId ? { ...a, is_active: isActive } : a)));
    },
  });

  const fetchAgents = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.agents.listAgents();
      setAgents(response.agents);

      // Resume polling for agents already in "connecting" state
      // This does NOT call /verify - it only polls for status updates
      // User must manually click "Verify" to start a new verification
      const connecting = response.agents.filter(
        (a) => a.connection_status === "connecting" && !verifyingIds.has(a.id)
      );
      connecting.forEach((a) => {
        resumePolling(a.id);
      });
    } catch (err) {
      logger.error("Failed to fetch agents", err);
      setError(err instanceof Error ? err.message : "Failed to load agents");
    } finally {
      setLoading(false);
    }
  }, [resumePolling, verifyingIds]);

  useEffect(() => {
    fetchAgents();
  }, [fetchAgents]);

  const handleCreateAgent = useCallback(
    async (data: AgentCreateRequest | AgentUpdateRequest) => {
      try {
        const newAgent = await api.agents.createAgent(data as AgentCreateRequest);
        toast({
          title: "Agent created",
          description: "Verification in progress...",
        });
        setIsCreateOpen(false);

        // Start polling for verification
        verifyAgent(newAgent.id);

        // Refresh list
        refreshAgentList();
      } catch (err) {
        logger.error("Failed to create agent", err);
        toast({
          title: "Failed to create agent",
          description: err instanceof Error ? err.message : "Unknown error",
          variant: "destructive",
        });
        throw err;
      }
    },
    [toast, refreshAgentList, verifyAgent]
  );

  const handleOpenEditDialog = useCallback(
    async (agentId: string) => {
      try {
        setIsEditLoading(true);
        const fullAgent = await api.agents.getAgent(agentId);
        setEditAgent(fullAgent);
      } catch (err) {
        logger.error("Failed to fetch agent for editing", err);
        toast({
          title: "Failed to load agent",
          description: err instanceof Error ? err.message : "Unknown error",
          variant: "destructive",
        });
      } finally {
        setIsEditLoading(false);
      }
    },
    [toast]
  );

  const handleToggleActive = async (agent: AgentListItem) => {
    // Optimistic update
    const previousIsActive = agent.is_active;
    setAgents((prev) =>
      prev.map((a) => (a.id === agent.id ? { ...a, is_active: !agent.is_active } : a))
    );

    try {
      await toggleActive(agent.id, agent.is_active);
    } catch {
      // Revert on error (hook already showed toast)
      setAgents((prev) =>
        prev.map((a) => (a.id === agent.id ? { ...a, is_active: previousIsActive } : a))
      );
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <Skeleton className="mb-2 h-8 w-48" />
            <Skeleton className="h-5 w-96" />
          </div>
          <Skeleton className="h-10 w-32" />
        </div>
        <div className="grid gap-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-24 w-full" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Voice Agents</h1>
        </div>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-destructive">
              <AlertCircle className="h-5 w-5" />
              <p>Error loading agents: {error}</p>
            </div>
            <Button variant="outline" className="mt-4" onClick={fetchAgents}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Voice Agents</h1>
          <p className="mt-1 text-muted-foreground">
            Configure and manage your voice agent definitions
          </p>
        </div>
        <Button onClick={() => setIsCreateOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          New Agent
        </Button>
      </div>

      {agents.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <div className="py-12 text-center text-muted-foreground">
              <Settings2 className="mx-auto mb-4 h-12 w-12 opacity-50" />
              <p>No agents found</p>
              <Button variant="outline" className="mt-4" onClick={() => setIsCreateOpen(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Create Your First Agent
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {agents.map((agent) => (
            <Card
              key={agent.id}
              className="cursor-pointer transition-colors hover:bg-secondary/30"
              onClick={() => router.push(`/agents/${agent.id}`)}
            >
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-4">
                    <div className="rounded-lg bg-primary/10 p-2.5">
                      <Settings2 className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <div className="mb-1 flex items-center gap-2">
                        <h3 className="font-medium">{agent.name}</h3>
                        <AgentStatusBadge
                          connectionStatus={agent.connection_status}
                          isActive={agent.is_active}
                        />
                      </div>
                      <p className="line-clamp-1 text-sm text-muted-foreground">
                        {agent.description}
                      </p>
                      {agent.phone_number && (
                        <div className="mt-2 flex items-center gap-1 text-xs text-muted-foreground">
                          <Phone className="h-3.5 w-3.5" />
                          {agent.phone_number}
                        </div>
                      )}
                    </div>
                  </div>

                  <DropdownMenu>
                    <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                      <Button variant="ghost" size="icon">
                        <MoreVertical className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="bg-popover">
                      <DropdownMenuItem
                        onClick={(e) => {
                          e.stopPropagation();
                          router.push(`/agents/${agent.id}`);
                        }}
                      >
                        <Eye className="mr-2 h-4 w-4" />
                        View
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={(e) => {
                          e.stopPropagation();
                          handleOpenEditDialog(agent.id);
                        }}
                      >
                        <Pencil className="mr-2 h-4 w-4" />
                        Edit
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={(e) => {
                          e.stopPropagation();
                          verifyAgent(agent.id);
                        }}
                        disabled={verifyingIds.has(agent.id)}
                      >
                        <RefreshCw
                          className={`mr-2 h-4 w-4 ${
                            verifyingIds.has(agent.id) ? "animate-spin" : ""
                          }`}
                        />
                        {verifyingIds.has(agent.id) ? "Verifying..." : "Verify"}
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={(e) => {
                          e.stopPropagation();
                          handleToggleActive(agent);
                        }}
                      >
                        <Power className="mr-2 h-4 w-4" />
                        {agent.is_active ? "Deactivate" : "Activate"}
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        className="text-destructive"
                        onClick={(e) => {
                          e.stopPropagation();
                          setDeleteAgentId(agent.id);
                        }}
                      >
                        <Trash2 className="mr-2 h-4 w-4" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Create Agent Dialog */}
      <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
        <DialogContent className="max-h-[90vh] max-w-2xl overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Create New Agent</DialogTitle>
          </DialogHeader>
          <AgentConfigForm onSubmit={handleCreateAgent} onCancel={() => setIsCreateOpen(false)} />
        </DialogContent>
      </Dialog>

      {/* Edit Agent Dialog */}
      <EditAgentDialog
        agent={editAgent}
        onOpenChange={(open) => !open && setEditAgent(null)}
        onUpdated={refreshAgentList}
      />

      {/* Loading Overlay for Edit */}
      {isEditLoading && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/50">
          <div className="flex items-center gap-2 rounded-lg bg-card p-4 shadow-lg">
            <RefreshCw className="h-4 w-4 animate-spin" />
            <span>Loading agent...</span>
          </div>
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      <DeleteAgentDialog
        agentId={deleteAgentId}
        agentName={agents.find((a) => a.id === deleteAgentId)?.name}
        onOpenChange={(open) => !open && setDeleteAgentId(null)}
        onDeleted={refreshAgentList}
      />
    </div>
  );
}
