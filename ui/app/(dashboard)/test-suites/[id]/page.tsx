"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter, useParams } from "next/navigation";
import { Button } from "@/components/primitives/button";
import { Badge } from "@/components/primitives/badge";
import { Card, CardContent } from "@/components/primitives/card";
import { Skeleton } from "@/components/primitives/skeleton";
import { CreateTestSuiteDialog } from "@/components/tests/CreateTestSuiteDialog";
import { DeleteTestSuiteDialog } from "@/components/tests/DeleteTestSuiteDialog";
import { TestScenarioDialog } from "@/components/tests/TestScenarioDialog";
import { TestSuiteStatusBadge } from "@/components/tests/TestSuiteStatusBadge";
import { GenerateMoreDialog } from "@/components/tests/GenerateMoreDialog";
import { DeleteTestScenarioDialog } from "@/components/tests/DeleteTestScenarioDialog";
import { TestScenariosTable } from "@/components/tests/TestScenariosTable";
import { Pagination } from "@/components/primitives/pagination";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/primitives/dropdown-menu";
import {
  ArrowLeft,
  Settings,
  Play,
  MoreHorizontal,
  Copy,
  Download,
  Trash2,
  Sparkles,
  Plus,
  AlertCircle,
  Pencil,
  Loader2,
} from "lucide-react";
import { api } from "@/lib/api";
import { logger } from "@/lib/logger";
import { useAuth } from "@/contexts/auth-context";
import { useTestSuiteActions } from "@/hooks/useTestSuiteActions";
import { useGenerationPolling, useTestScenarios } from "@/hooks";
import { toast } from "sonner";
import type { TestSuite, TestScenario } from "@/lib/types";
import { getPassRateFromStatus, formatRelativeTime } from "@/lib/utils/testSuiteUtils";

export default function TestSuiteDetailPage() {
  const router = useRouter();
  const params = useParams();
  const suiteId = params.id as string;
  const { activeOrg } = useAuth();
  const orgId = activeOrg?.id ?? "";

  const [suite, setSuite] = useState<TestSuite | null>(null);
  const [loading, setLoading] = useState(true);
  const [isInitialLoad, setIsInitialLoad] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Use the shared hook for scenarios (replaces manual fetch)
  const {
    scenarios,
    testSuites,
    personas,
    filters: scenarioFilters,
    setFilters: setScenarioFilters,
    page,
    pageSize,
    totalCount,
    totalPages,
    setPage,
    setPageSize,
    loading: scenariosLoading,
    refetch: refetchScenarios,
    deleteScenario,
    isDeleting: isDeletingScenario,
  } = useTestScenarios({
    orgId,
    initialFilters: { suiteId },
  });

  // Dialog states
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [createTestDialogOpen, setCreateTestDialogOpen] = useState(false);
  const [generateMoreOpen, setGenerateMoreOpen] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

  // Scenario edit/delete state
  const [selectedScenario, setSelectedScenario] = useState<TestScenario | null>(null);
  const [editScenarioDialogOpen, setEditScenarioDialogOpen] = useState(false);
  const [deleteScenarioDialogOpen, setDeleteScenarioDialogOpen] = useState(false);

  const { deleteSuite, deletingIds } = useTestSuiteActions({
    onDeleted: () => {
      router.push("/test-suites");
    },
  });

  // Determine if generation is in progress
  const isGeneratingStatus = suite?.status === "pending" || suite?.status === "generating";

  // Poll generation status when suite is generating
  useGenerationPolling({
    suiteId: suite?.id || null,
    enabled: isGeneratingStatus,
    onComplete: (status) => {
      // Refresh suite data silently (no loading skeleton)
      fetchData(false);
      // Refresh scenarios via hook
      refetchScenarios();
      if (status.status === "ready") {
        toast("Generation Complete", {
          description: `Generated ${status.scenario_count} test scenarios.`,
        });
      } else if (status.status === "generation_failed") {
        toast.error("Generation Failed", {
          description: status.error || "Failed to generate test scenarios.",
        });
      }
    },
    onError: (error) => {
      logger.error("Generation polling error", error);
    },
  });

  const fetchData = useCallback(
    async (showLoading = true) => {
      try {
        if (showLoading) {
          setLoading(true);
        }
        setError(null);
        const suiteData = await api.testSuites.getTestSuite(suiteId);
        setSuite(suiteData);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Failed to load test suite";
        setError(errorMessage);
        logger.error("Failed to load test suite", err);
      } finally {
        setLoading(false);
        setIsInitialLoad(false);
      }
    },
    [suiteId]
  );

  useEffect(() => {
    if (suiteId) {
      fetchData();
    }
  }, [suiteId, fetchData]);

  const handleSuiteUpdated = async (updatedSuite: TestSuite) => {
    setSuite(updatedSuite);
    setEditDialogOpen(false);
  };

  const handleTestCreated = async () => {
    await refetchScenarios();
  };

  const handleGenerateMore = async (prompt?: string) => {
    if (!suite) return;
    setIsGenerating(true);
    try {
      await api.testSuites.generateMoreScenarios(suite.id, prompt ? { prompt } : undefined);
      setGenerateMoreOpen(false);
      // Update suite status locally to trigger polling - don't call fetchData
      // which would show a loading skeleton. Polling will refresh data when complete.
      setSuite((prev) => (prev ? { ...prev, status: "generating" } : null));
      toast("Generation Started", {
        description: "AI is generating additional test scenarios...",
      });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to start generation";
      toast.error("Generation Failed", {
        description: errorMessage,
      });
      logger.error("Failed to generate more scenarios", err);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleScenarioUpdated = async () => {
    await refetchScenarios();
    setSelectedScenario(null);
    toast("Scenario Updated", { description: "Test scenario has been updated successfully." });
  };

  const handleConfirmDeleteScenario = async () => {
    if (!selectedScenario) return;
    try {
      await deleteScenario(selectedScenario.id);
      toast("Scenario Deleted", { description: `"${selectedScenario.name}" has been deleted.` });
      setDeleteScenarioDialogOpen(false);
      setSelectedScenario(null);
    } catch {
      toast.error("Delete Failed", { description: "Failed to delete scenario." });
    }
  };

  if (loading && isInitialLoad) {
    return (
      <div className="space-y-6 p-8">
        <div className="flex items-center gap-4">
          <Skeleton className="h-10 w-10" />
          <div className="flex-1">
            <Skeleton className="mb-2 h-8 w-64" />
            <Skeleton className="h-4 w-96" />
          </div>
        </div>
        <div className="flex gap-4">
          <Skeleton className="h-6 w-24" />
          <Skeleton className="h-6 w-24" />
          <Skeleton className="h-6 w-24" />
        </div>
        <div className="grid gap-4 lg:grid-cols-2">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-40 w-full" />
          ))}
        </div>
      </div>
    );
  }

  if (error || !suite) {
    return (
      <div className="space-y-6 p-8">
        <Button variant="ghost" size="icon" onClick={() => router.push("/test-suites")}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-destructive">
              <AlertCircle className="h-5 w-5" />
              <p>Error loading test suite: {error || "Suite not found"}</p>
            </div>
            <Button variant="outline" className="mt-4" onClick={() => router.push("/test-suites")}>
              Back to Test Suites
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const passRate = getPassRateFromStatus(suite.status);

  return (
    <div className="space-y-6 p-8">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-4">
          <Button
            variant="ghost"
            size="icon"
            className="mt-1"
            onClick={() => router.push("/test-suites")}
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold">{suite.name}</h1>
              <TestSuiteStatusBadge status={suite.status} error={suite.generation_error} />
            </div>
            {suite.description && <p className="mt-1 text-muted-foreground">{suite.description}</p>}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => setEditDialogOpen(true)}>
            <Pencil className="mr-2 h-4 w-4" />
            Edit
          </Button>
          <Button variant="outline" size="sm">
            <Settings className="mr-2 h-4 w-4" />
            Configure
          </Button>
          <Button size="sm">
            <Play className="mr-2 h-4 w-4" />
            Run Suite
          </Button>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon">
                <MoreHorizontal className="h-5 w-5" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem>
                <Copy className="mr-2 h-4 w-4" />
                Duplicate Suite
              </DropdownMenuItem>
              <DropdownMenuItem>
                <Download className="mr-2 h-4 w-4" />
                Export Tests
              </DropdownMenuItem>
              <DropdownMenuItem
                className="text-destructive"
                onClick={() => setDeleteDialogOpen(true)}
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Delete Suite
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Stats Row */}
      <div className="flex items-center gap-6 text-sm">
        <div className="flex items-center gap-2">
          <span className="text-muted-foreground">Tests:</span>
          <Badge variant="secondary">{scenarios.length}</Badge>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-muted-foreground">Pass Rate:</span>
          <span
            className={
              passRate >= 90 ? "text-success" : passRate >= 70 ? "text-warning" : "text-destructive"
            }
          >
            {passRate}%
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-muted-foreground">Last Run:</span>
          <span>{formatRelativeTime(suite.created_at)}</span>
        </div>
      </div>

      {/* Actions Bar */}
      <div className="flex items-center justify-end gap-2">
        {suite.status === "ready" && (
          <Button variant="outline" onClick={() => setGenerateMoreOpen(true)}>
            <Sparkles className="mr-2 h-4 w-4" />
            Generate More
          </Button>
        )}
        {isGeneratingStatus && (
          <Button variant="outline" disabled>
            <Sparkles className="mr-2 h-4 w-4 animate-pulse" />
            Generating...
          </Button>
        )}
        <Button onClick={() => setCreateTestDialogOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Add Test
        </Button>
      </div>

      {/* Generation Progress Banner */}
      {isGeneratingStatus && (
        <Card className="border-primary/50 bg-primary/5">
          <CardContent className="flex items-center gap-4 py-4">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
              <Sparkles className="h-5 w-5 animate-pulse text-primary" />
            </div>
            <div className="flex-1">
              <p className="font-medium text-foreground">Generating Test Scenarios</p>
              <p className="text-sm text-muted-foreground">
                AI is analyzing your agent and creating test scenarios...
              </p>
            </div>
            <Loader2 className="h-5 w-5 animate-spin text-primary" />
          </CardContent>
        </Card>
      )}

      {/* Scenarios Table */}
      <TestScenariosTable
        scenarios={scenarios}
        testSuites={testSuites}
        personas={personas}
        filters={scenarioFilters}
        onFiltersChange={setScenarioFilters}
        showSuiteColumn={false}
        showSuiteFilter={false}
        loading={scenariosLoading}
        onRowClick={(s) => router.push(`/test-scenarios/${s.id}`)}
        onEdit={(s) => {
          setSelectedScenario(s);
          setEditScenarioDialogOpen(true);
        }}
        onDelete={(s) => {
          setSelectedScenario(s);
          setDeleteScenarioDialogOpen(true);
        }}
      />

      {/* Pagination */}
      {!scenariosLoading && totalCount > 0 && (
        <Pagination
          currentPage={page}
          totalPages={totalPages}
          totalItems={totalCount}
          pageSize={pageSize}
          onPageChange={setPage}
          onPageSizeChange={setPageSize}
        />
      )}

      {/* Edit Suite Dialog */}
      <CreateTestSuiteDialog
        open={editDialogOpen}
        onOpenChange={setEditDialogOpen}
        testSuite={suite}
        onUpdate={handleSuiteUpdated}
      />

      {/* Delete Suite Dialog */}
      <DeleteTestSuiteDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        suiteName={suite.name}
        isDeleting={deletingIds.has(suite.id)}
        onConfirm={() => deleteSuite(suite.id)}
      />

      {/* Generate More Dialog */}
      <GenerateMoreDialog
        open={generateMoreOpen}
        onOpenChange={setGenerateMoreOpen}
        onGenerate={handleGenerateMore}
        isGenerating={isGenerating}
      />

      {/* Create/Edit Scenario Dialog */}
      <TestScenarioDialog
        open={createTestDialogOpen || editScenarioDialogOpen}
        onOpenChange={(open) => {
          if (!open) {
            setCreateTestDialogOpen(false);
            setEditScenarioDialogOpen(false);
            setSelectedScenario(null);
          }
        }}
        orgId={orgId}
        scenario={editScenarioDialogOpen ? (selectedScenario ?? undefined) : undefined}
        suiteId={suite.id}
        onCreate={handleTestCreated}
        onUpdate={handleScenarioUpdated}
      />

      {/* Delete Scenario Dialog */}
      {selectedScenario && (
        <DeleteTestScenarioDialog
          open={deleteScenarioDialogOpen}
          onOpenChange={(open) => {
            setDeleteScenarioDialogOpen(open);
            if (!open) setSelectedScenario(null);
          }}
          scenarioName={selectedScenario.name}
          isDeleting={isDeletingScenario}
          onConfirm={handleConfirmDeleteScenario}
        />
      )}
    </div>
  );
}
