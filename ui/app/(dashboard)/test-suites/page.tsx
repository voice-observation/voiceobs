"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/primitives/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/primitives/table";
import { Card, CardContent } from "@/components/primitives/card";
import { Skeleton } from "@/components/primitives/skeleton";
import { TestSuiteStatusBadge } from "@/components/tests/TestSuiteStatusBadge";
import { CreateTestSuiteDialog } from "@/components/tests/CreateTestSuiteDialog";
import { DeleteTestSuiteDialog } from "@/components/tests/DeleteTestSuiteDialog";
import { Filter, Plus, Eye, Copy, Play, Trash2, Pencil, AlertCircle, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { logger } from "@/lib/logger";
import { useTestSuiteActions } from "@/hooks/useTestSuiteActions";
import { toast } from "sonner";
import type { TestSuite } from "@/lib/types";
import {
  getPassRateFromStatus,
  formatRelativeTime,
  getPassRateColor,
} from "@/lib/utils/testSuiteUtils";

export default function TestSuitesPage() {
  const router = useRouter();
  const [testSuites, setTestSuites] = useState<TestSuite[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isInitialLoad, setIsInitialLoad] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editingSuite, setEditingSuite] = useState<TestSuite | null>(null);
  const [deletingSuite, setDeletingSuite] = useState<{ id: string; name: string } | null>(null);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const { deleteSuite, runSuite, deletingIds, runningIds } = useTestSuiteActions({
    onDeleted: (suiteId) => {
      setTestSuites((prev) => prev.filter((suite) => suite.id !== suiteId));
      setDeletingSuite(null);
    },
  });

  const fetchData = useCallback(async (showLoading = true) => {
    try {
      if (showLoading) {
        setLoading(true);
      }
      setError(null);

      const suitesResponse = await api.testSuites.listTestSuites();
      setTestSuites(suitesResponse.suites);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to load test suites";
      setError(errorMessage);
      logger.error("Failed to load test suites", err);
    } finally {
      setLoading(false);
      setIsInitialLoad(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Get IDs of suites that need polling (pending or generating)
  const generatingSuiteIds = testSuites
    .filter((suite) => suite.status === "pending" || suite.status === "generating")
    .map((suite) => suite.id);

  // Poll for suites that are generating
  useEffect(() => {
    // Clear existing interval
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }

    // If no suites are generating, don't start polling
    if (generatingSuiteIds.length === 0) {
      return;
    }

    const pollGeneratingStatus = async () => {
      for (const suiteId of generatingSuiteIds) {
        try {
          const status = await api.testSuites.getGenerationStatus(suiteId);

          // Update suite in list when status changes
          setTestSuites((prev) =>
            prev.map((s) => {
              if (s.id !== suiteId) return s;

              // Only update if something changed
              if (s.status === status.status && s.scenario_count === status.scenario_count) {
                return s;
              }

              // Show toast when generation completes
              if (status.status === "ready" && s.status !== "ready") {
                toast("Generation Complete", {
                  description: `"${s.name}" generated ${status.scenario_count} test scenarios.`,
                });
              } else if (
                status.status === "generation_failed" &&
                s.status !== "generation_failed"
              ) {
                toast.error("Generation Failed", {
                  description: status.error || `Failed to generate scenarios for "${s.name}".`,
                });
              }

              return {
                ...s,
                status: status.status,
                scenario_count: status.scenario_count,
                generation_error: status.error,
              };
            })
          );
        } catch (err) {
          logger.error("Failed to poll generation status", { suiteId, error: err });
        }
      }
    };

    // Initial poll
    pollGeneratingStatus();

    // Start polling interval (every 2 seconds)
    pollingIntervalRef.current = setInterval(pollGeneratingStatus, 2000);

    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    };
    // Only re-run effect when the set of generating suite IDs changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [generatingSuiteIds.join(",")]);

  const handleCreateSuite = async (newSuite: TestSuite) => {
    // Optimistically add the new suite to the list without showing loading skeleton
    setTestSuites((prev) => [newSuite, ...prev]);
  };

  const handleUpdateSuite = async (updatedSuite: TestSuite) => {
    // Update the suite in the list without showing loading skeleton
    setTestSuites((prev) =>
      prev.map((suite) => (suite.id === updatedSuite.id ? updatedSuite : suite))
    );
    setEditingSuite(null);
  };

  const handleEdit = (suite: TestSuite, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingSuite(suite);
  };

  const handleDelete = (suite: TestSuite, e: React.MouseEvent) => {
    e.stopPropagation();
    setDeletingSuite({ id: suite.id, name: suite.name });
  };

  const handleRun = (suiteId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    runSuite(suiteId);
  };

  const handleView = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    router.push(`/test-suites/${id}`);
  };

  if (loading && isInitialLoad) {
    return (
      <div className="space-y-6 p-8">
        <div>
          <Skeleton className="mb-2 h-9 w-48" />
          <Skeleton className="h-5 w-96" />
        </div>
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-4">
              {[1, 2, 3, 4].map((i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6 p-8">
        <div>
          <h1 className="text-2xl font-bold">Test Suites</h1>
        </div>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-destructive">
              <AlertCircle className="h-5 w-5" />
              <p>Error loading test suites: {error}</p>
            </div>
            <Button variant="outline" className="mt-4" onClick={() => fetchData()}>
              Try Again
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Test Suites</h1>
          <p className="mt-1 text-muted-foreground">Manage and configure your test scenarios</p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline">
            <Filter className="mr-2 h-4 w-4" />
            Filter
          </Button>
          <Button onClick={() => setCreateDialogOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            New Suite
          </Button>
        </div>
      </div>

      {testSuites.length === 0 ? (
        <Card>
          <CardContent className="pt-6">
            <div className="py-12 text-center text-muted-foreground">
              <p>No test suites found</p>
              <Button variant="outline" className="mt-4" onClick={() => setCreateDialogOpen(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Create Your First Test Suite
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="rounded-lg border border-border bg-card">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[280px]">SUITE NAME</TableHead>
                <TableHead className="w-[100px]">SCENARIOS</TableHead>
                <TableHead className="w-[140px]">STATUS</TableHead>
                <TableHead className="w-[180px]">PASS RATE</TableHead>
                <TableHead className="w-[120px]">CREATED</TableHead>
                <TableHead className="text-right">ACTIONS</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {testSuites.map((suite) => {
                const passRate = getPassRateFromStatus(suite.status);

                return (
                  <TableRow
                    key={suite.id}
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() => router.push(`/test-suites/${suite.id}`)}
                  >
                    <TableCell className="font-medium">{suite.name}</TableCell>
                    <TableCell>{suite.scenario_count ?? "-"}</TableCell>
                    <TableCell>
                      <TestSuiteStatusBadge status={suite.status} error={suite.generation_error} />
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className="h-2 w-20 overflow-hidden rounded-full bg-muted">
                          <div
                            className={`h-full ${getPassRateColor(passRate)}`}
                            style={{ width: `${passRate}%` }}
                          />
                        </div>
                        <span className="text-sm text-muted-foreground">{passRate}%</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {formatRelativeTime(suite.created_at)}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          onClick={(e) => handleView(suite.id, e)}
                          title="View details"
                        >
                          <Eye className="h-4 w-4 text-muted-foreground" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          onClick={(e) => handleEdit(suite, e)}
                          title="Edit suite"
                        >
                          <Pencil className="h-4 w-4 text-muted-foreground" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          onClick={(e) => e.stopPropagation()}
                          title="Duplicate suite"
                        >
                          <Copy className="h-4 w-4 text-muted-foreground" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          onClick={(e) => handleRun(suite.id, e)}
                          disabled={runningIds.has(suite.id)}
                          title="Run suite"
                        >
                          {runningIds.has(suite.id) ? (
                            <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                          ) : (
                            <Play className="h-4 w-4 text-muted-foreground" />
                          )}
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          onClick={(e) => handleDelete(suite, e)}
                          disabled={deletingIds.has(suite.id)}
                          title="Delete suite"
                        >
                          {deletingIds.has(suite.id) ? (
                            <Loader2 className="h-4 w-4 animate-spin text-destructive" />
                          ) : (
                            <Trash2 className="h-4 w-4 text-destructive" />
                          )}
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      )}

      {/* Create Dialog */}
      <CreateTestSuiteDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
        onCreate={handleCreateSuite}
      />

      {/* Edit Dialog */}
      <CreateTestSuiteDialog
        open={!!editingSuite}
        onOpenChange={(open) => !open && setEditingSuite(null)}
        testSuite={editingSuite || undefined}
        onUpdate={handleUpdateSuite}
      />

      {/* Delete Dialog */}
      {deletingSuite && (
        <DeleteTestSuiteDialog
          open={!!deletingSuite}
          onOpenChange={(open) => !open && setDeletingSuite(null)}
          suiteName={deletingSuite.name}
          isDeleting={deletingIds.has(deletingSuite.id)}
          onConfirm={() => deleteSuite(deletingSuite.id)}
        />
      )}
    </div>
  );
}
