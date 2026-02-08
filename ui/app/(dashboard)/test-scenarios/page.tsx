"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useTestScenarios } from "@/hooks";
import { toast } from "sonner";
import { Button } from "@/components/primitives/button";
import { TestScenariosTable } from "@/components/tests/TestScenariosTable";
import { TestScenarioDialog } from "@/components/tests/TestScenarioDialog";
import { DeleteTestScenarioDialog } from "@/components/tests/DeleteTestScenarioDialog";
import { Pagination } from "@/components/primitives/pagination";
import { Plus } from "lucide-react";
import type { TestScenario } from "@/lib/types";

export default function TestScenariosPage() {
  const router = useRouter();
  const {
    scenarios,
    testSuites,
    personas,
    filters,
    setFilters,
    page,
    pageSize,
    totalCount,
    totalPages,
    setPage,
    setPageSize,
    loading,
    refetch,
    deleteScenario,
    isDeleting,
  } = useTestScenarios();

  // Dialog state
  const [selectedScenario, setSelectedScenario] = useState<TestScenario | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  const handleUpdate = async () => {
    await refetch();
    setSelectedScenario(null);
    toast("Scenario Updated", { description: "Test scenario has been updated." });
  };

  const handleDelete = async () => {
    if (!selectedScenario) return;
    try {
      await deleteScenario(selectedScenario.id);
      setDeleteDialogOpen(false);
      setSelectedScenario(null);
      toast("Scenario Deleted", { description: `"${selectedScenario.name}" deleted.` });
    } catch {
      toast.error("Delete Failed", { description: "Failed to delete scenario." });
    }
  };

  const handleScenarioCreated = async () => {
    await refetch();
    toast("Scenario Created", { description: "Test scenario has been created." });
  };

  return (
    <div className="space-y-6 p-8">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Test Scenarios</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            All test scenarios across test suites
          </p>
        </div>
        <Button onClick={() => setCreateDialogOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Add Test Scenario
        </Button>
      </div>

      {/* Table */}
      <TestScenariosTable
        scenarios={scenarios}
        testSuites={testSuites}
        personas={personas}
        filters={filters}
        onFiltersChange={setFilters}
        showSuiteColumn={true}
        showSuiteFilter={true}
        loading={loading}
        onRowClick={(s) => router.push(`/test-scenarios/${s.id}`)}
        onEdit={(s) => {
          setSelectedScenario(s);
          setEditDialogOpen(true);
        }}
        onDelete={(s) => {
          setSelectedScenario(s);
          setDeleteDialogOpen(true);
        }}
      />

      {/* Pagination */}
      {!loading && totalCount > 0 && (
        <Pagination
          currentPage={page}
          totalPages={totalPages}
          totalItems={totalCount}
          pageSize={pageSize}
          onPageChange={setPage}
          onPageSizeChange={setPageSize}
        />
      )}

      {/* Delete Dialog */}
      {selectedScenario && (
        <DeleteTestScenarioDialog
          open={deleteDialogOpen}
          onOpenChange={(open) => {
            setDeleteDialogOpen(open);
            if (!open) setSelectedScenario(null);
          }}
          scenarioName={selectedScenario.name}
          isDeleting={isDeleting}
          onConfirm={handleDelete}
        />
      )}

      {/* Create/Edit Dialog */}
      <TestScenarioDialog
        open={createDialogOpen || editDialogOpen}
        onOpenChange={(open) => {
          if (!open) {
            setCreateDialogOpen(false);
            setEditDialogOpen(false);
            setSelectedScenario(null);
          }
        }}
        scenario={editDialogOpen ? (selectedScenario ?? undefined) : undefined}
        onCreate={handleScenarioCreated}
        onUpdate={handleUpdate}
      />
    </div>
  );
}
