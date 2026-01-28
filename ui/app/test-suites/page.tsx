"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { CreateTestSuiteDialog } from "@/components/tests/CreateTestSuiteDialog";
import { Filter, Plus, Eye, Copy, Play, Trash2, Pencil, AlertCircle } from "lucide-react";
import { api } from "@/lib/api";
import { logger } from "@/lib/logger";
import type { TestSuite } from "@/lib/types";
import {
  getPassRateFromStatus,
  getStatusBadgeType,
  getStatusLabel,
  formatRelativeTime,
  getPassRateColor,
} from "@/lib/utils/testSuiteUtils";

export default function TestSuitesPage() {
  const router = useRouter();
  const [testSuites, setTestSuites] = useState<TestSuite[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        setError(null);
        const response = await api.testSuites.listTestSuites();
        setTestSuites(response.suites);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Failed to load test suites";
        setError(errorMessage);
        logger.error("Failed to load test suites", err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const handleCreateSuite = async (suite: {
    id: string;
    name: string;
    description: string | null;
  }) => {
    try {
      // Refresh the list
      const response = await api.testSuites.listTestSuites();
      setTestSuites(response.suites);
      logger.info("Test suite created and list refreshed", { suiteId: suite.id });
    } catch (err) {
      logger.error("Failed to refresh test suites after creation", err);
    }
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this test suite?")) {
      return;
    }

    try {
      await api.testSuites.deleteTestSuite(id);
      setTestSuites((prev) => prev.filter((suite) => suite.id !== id));
      logger.info("Test suite deleted", { suiteId: id });
    } catch (err) {
      logger.error("Failed to delete test suite", err, { suiteId: id });
      alert("Failed to delete test suite. Please try again.");
    }
  };

  const handleView = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    router.push(`/test-suites/${id}`);
  };

  if (loading) {
    return (
      <div className="space-y-6">
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
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Test Suites</h1>
        </div>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-destructive">
              <AlertCircle className="h-5 w-5" />
              <p>Error loading test suites: {error}</p>
            </div>
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
                <TableHead className="w-[80px]">TESTS</TableHead>
                <TableHead className="w-[180px]">PASS RATE</TableHead>
                <TableHead className="w-[120px]">LAST RUN</TableHead>
                <TableHead className="w-[120px]">STATUS</TableHead>
                <TableHead className="text-right">ACTIONS</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {testSuites.map((suite) => {
                const passRate = getPassRateFromStatus(suite.status);
                const statusBadgeType = getStatusBadgeType(suite.status);
                const statusLabel = getStatusLabel(suite.status);
                // Mock tests count - in real app, fetch from scenarios
                const testsCount = 0;

                return (
                  <TableRow
                    key={suite.id}
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() => router.push(`/test-suites/${suite.id}`)}
                  >
                    <TableCell className="font-medium">{suite.name}</TableCell>
                    <TableCell>{testsCount}</TableCell>
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
                      <StatusBadge status={statusBadgeType}>{statusLabel}</StatusBadge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          onClick={(e) => handleView(suite.id, e)}
                        >
                          <Eye className="h-4 w-4 text-muted-foreground" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <Pencil className="h-4 w-4 text-muted-foreground" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <Copy className="h-4 w-4 text-muted-foreground" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <Play className="h-4 w-4 text-muted-foreground" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          onClick={(e) => handleDelete(suite.id, e)}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
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

      <CreateTestSuiteDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
        onCreate={handleCreateSuite}
      />
    </div>
  );
}
