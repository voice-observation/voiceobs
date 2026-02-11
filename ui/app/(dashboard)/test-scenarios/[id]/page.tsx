"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter, useParams } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/primitives/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/primitives/card";
import { Badge } from "@/components/primitives/badge";
import { Skeleton } from "@/components/primitives/skeleton";
import { TestScenarioStatusBadge } from "@/components/tests/TestScenarioStatusBadge";
import { TestScenarioDialog } from "@/components/tests/TestScenarioDialog";
import { DeleteTestScenarioDialog } from "@/components/tests/DeleteTestScenarioDialog";
import { ScenarioDetailsCard } from "@/components/tests/ScenarioDetailsCard";
import { ScenarioMetricsCharts } from "@/components/tests/ScenarioMetricsCharts";
import { ScenarioRunHistory } from "@/components/tests/ScenarioRunHistory";
import { ArrowLeft, Pencil, Trash2, AlertCircle, Play } from "lucide-react";
import { api } from "@/lib/api";
import { logger } from "@/lib/logger";
import { useAuth } from "@/contexts/auth-context";
import { toast } from "sonner";
import type { TestScenario, TestSuite, PersonaListItem } from "@/lib/types";

export default function TestScenarioDetailPage() {
  const router = useRouter();
  const params = useParams();
  const scenarioId = params.id as string;
  const { activeOrg } = useAuth();
  const orgId = activeOrg?.id ?? "";

  const [scenario, setScenario] = useState<TestScenario | null>(null);
  const [testSuite, setTestSuite] = useState<TestSuite | null>(null);
  const [persona, setPersona] = useState<PersonaListItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Dialog states
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch the scenario
      const scenarioData = await api.testScenarios.getTestScenario(scenarioId);
      setScenario(scenarioData);

      // Fetch the parent test suite
      try {
        const suiteData = await api.testSuites.getTestSuite(scenarioData.suite_id);
        setTestSuite(suiteData);
      } catch (err) {
        logger.warn("Failed to fetch test suite", { error: err });
        // Non-critical error, continue
      }

      // Fetch the persona
      try {
        const personaData = await api.personas.getPersona(orgId, scenarioData.persona_id);
        setPersona(personaData as PersonaListItem);
      } catch (err) {
        logger.warn("Failed to fetch persona", { error: err });
        // Non-critical error, continue
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to load test scenario";
      setError(errorMessage);
      logger.error("Failed to load test scenario", err);
    } finally {
      setLoading(false);
    }
  }, [scenarioId, orgId]);

  useEffect(() => {
    if (scenarioId && orgId) {
      fetchData();
    }
  }, [scenarioId, fetchData, orgId]);

  const handleScenarioUpdated = async (updatedScenario: TestScenario) => {
    setScenario(updatedScenario);
    toast("Scenario Updated", { description: "Test scenario has been updated successfully." });
  };

  const handleConfirmDelete = async () => {
    if (!scenario) return;
    setIsDeleting(true);
    try {
      await api.testScenarios.deleteTestScenario(scenario.id);
      toast("Scenario Deleted", { description: `"${scenario.name}" has been deleted.` });
      // Navigate back to list or suite detail
      if (testSuite) {
        router.push(`/test-suites/${testSuite.id}`);
      } else {
        router.push("/test-scenarios");
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to delete scenario";
      toast.error("Delete Failed", { description: errorMessage });
      logger.error("Failed to delete scenario", err);
    } finally {
      setIsDeleting(false);
    }
  };

  // Loading skeleton
  if (loading) {
    return (
      <div className="space-y-6 p-8">
        <div className="flex items-center gap-4">
          <Skeleton className="h-10 w-10" />
          <div className="flex-1">
            <Skeleton className="mb-2 h-8 w-64" />
            <Skeleton className="h-4 w-96" />
          </div>
        </div>
        <div className="grid gap-6 lg:grid-cols-2">
          <Skeleton className="h-48 w-full" />
          <Skeleton className="h-48 w-full" />
        </div>
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  // Error state
  if (error || !scenario) {
    return (
      <div className="space-y-6 p-8">
        <Button variant="ghost" size="icon" onClick={() => router.push("/test-scenarios")}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-destructive">
              <AlertCircle className="h-5 w-5" />
              <p>Error loading test scenario: {error || "Scenario not found"}</p>
            </div>
            <Button
              variant="outline"
              className="mt-4"
              onClick={() => router.push("/test-scenarios")}
            >
              Back to Test Scenarios
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-8">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-4">
          <Button
            variant="ghost"
            size="icon"
            className="mt-1"
            onClick={() => {
              if (testSuite) {
                router.push(`/test-suites/${testSuite.id}`);
              } else {
                router.push("/test-scenarios");
              }
            }}
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold">{scenario.name}</h1>
              <TestScenarioStatusBadge status={scenario.status} />
            </div>
            {testSuite && (
              <p className="mt-1 text-sm text-muted-foreground">
                Part of{" "}
                <Link
                  href={`/test-suites/${testSuite.id}`}
                  className="font-medium text-primary hover:underline"
                >
                  {testSuite.name}
                </Link>
              </p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button size="sm">
            <Play className="mr-2 h-4 w-4" />
            Run Test
          </Button>
          <Button variant="outline" size="sm" onClick={() => setEditDialogOpen(true)}>
            <Pencil className="mr-2 h-4 w-4" />
            Edit
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="text-destructive hover:bg-destructive hover:text-destructive-foreground"
            onClick={() => setDeleteDialogOpen(true)}
          >
            <Trash2 className="mr-2 h-4 w-4" />
            Delete
          </Button>
        </div>
      </div>

      {/* Scenario Details Card */}
      <ScenarioDetailsCard scenario={scenario} persona={persona} />

      {/* Metrics Charts - TODO: fetch runs from API */}
      <ScenarioMetricsCharts runs={[]} />

      {/* Run History */}
      <ScenarioRunHistory runs={[]} onRowClick={(runId) => router.push(`/test-runs/${runId}`)} />

      {/* Edit Dialog */}
      <TestScenarioDialog
        open={editDialogOpen}
        onOpenChange={setEditDialogOpen}
        orgId={orgId}
        scenario={scenario}
        onUpdate={handleScenarioUpdated}
      />

      {/* Delete Dialog */}
      <DeleteTestScenarioDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        scenarioName={scenario.name}
        isDeleting={isDeleting}
        onConfirm={handleConfirmDelete}
      />
    </div>
  );
}
