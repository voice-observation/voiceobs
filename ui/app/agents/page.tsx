"use client";

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { AgentConfigForm } from "@/components/agents/AgentConfigForm";
import {
  Settings2,
  Plus,
  MoreVertical,
  Activity,
  Clock,
  CheckCircle2,
  Pencil,
  Power,
  Trash2,
} from "lucide-react";

const agents = [
  {
    id: "1",
    name: "Healthcare Appointment Scheduler",
    domain: "Healthcare",
    status: "active",
    lastRun: "2 hours ago",
    passRate: 96,
    testsCount: 48,
  },
  {
    id: "2",
    name: "Customer Support Bot",
    domain: "E-commerce",
    status: "active",
    lastRun: "4 hours ago",
    passRate: 78,
    testsCount: 32,
  },
  {
    id: "3",
    name: "Voice Banking Assistant",
    domain: "Finance",
    status: "active",
    lastRun: "6 hours ago",
    passRate: 92,
    testsCount: 56,
  },
  {
    id: "4",
    name: "Real-time Translation",
    domain: "Communication",
    status: "inactive",
    lastRun: "2 days ago",
    passRate: 88,
    testsCount: 24,
  },
];

export default function Agents() {
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [editingAgent, setEditingAgent] = useState<typeof agents[0] | null>(null);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Voice Agents</h1>
          <p className="text-muted-foreground mt-1">
            Configure and manage your voice agent definitions
          </p>
        </div>
        <Button onClick={() => setIsCreateOpen(true)}>
          <Plus className="w-4 h-4 mr-2" />
          New Agent
        </Button>
      </div>

      <div className="grid gap-4">
        {agents.map((agent) => (
          <Card
            key={agent.id}
            className="hover:bg-secondary/30 transition-colors"
          >
            <CardContent className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4">
                  <div className="p-2.5 rounded-lg bg-primary/10">
                    <Settings2 className="w-5 h-5 text-primary" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-medium">{agent.name}</h3>
                      <Badge
                        variant={
                          agent.status === "active"
                            ? "default"
                            : "secondary"
                        }
                        className="text-xs"
                      >
                        {agent.status}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground mt-0.5">
                      {agent.domain}
                    </p>
                    <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                      <div className="flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5" />
                        Last run: {agent.lastRun}
                      </div>
                      <div className="flex items-center gap-1">
                        <Activity className="w-3.5 h-3.5" />
                        {agent.testsCount} tests
                      </div>
                      <div className="flex items-center gap-1">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        {agent.passRate}% pass rate
                      </div>
                    </div>
                  </div>
                </div>

                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon">
                      <MoreVertical className="w-4 h-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="bg-popover">
                    <DropdownMenuItem onClick={() => setEditingAgent(agent)}>
                      <Pencil className="w-4 h-4 mr-2" />
                      Edit
                    </DropdownMenuItem>
                    <DropdownMenuItem>
                      <Power className="w-4 h-4 mr-2" />
                      Deactivate
                    </DropdownMenuItem>
                    <DropdownMenuItem className="text-destructive">
                      <Trash2 className="w-4 h-4 mr-2" />
                      Delete
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Create Agent Dialog */}
      <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Create New Agent</DialogTitle>
          </DialogHeader>
          <AgentConfigForm onGenerate={() => setIsCreateOpen(false)} />
        </DialogContent>
      </Dialog>

      {/* Edit Agent Dialog */}
      <Dialog open={!!editingAgent} onOpenChange={(open) => !open && setEditingAgent(null)}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingAgent?.name}</DialogTitle>
          </DialogHeader>
          <AgentConfigForm onGenerate={() => setEditingAgent(null)} />
        </DialogContent>
      </Dialog>
    </div>
  );
}
