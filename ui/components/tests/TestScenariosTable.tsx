"use client";

import { Input } from "@/components/primitives/input";
import { Badge } from "@/components/primitives/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/primitives/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/primitives/table";
import { Skeleton } from "@/components/primitives/skeleton";
import { Search, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import type { UseTestScenariosFilters } from "@/hooks/useTestScenarios";
import type { TestScenario, TestSuite, PersonaListItem } from "@/lib/types";

export interface TestScenariosTableProps {
  // Data
  scenarios: TestScenario[];
  testSuites: TestSuite[];
  personas: PersonaListItem[];

  // Filters
  filters: UseTestScenariosFilters;
  onFiltersChange: (filters: UseTestScenariosFilters) => void;

  // Display options
  showSuiteColumn?: boolean;
  showSuiteFilter?: boolean;
  loading?: boolean;

  // Row actions
  onRowClick?: (scenario: TestScenario) => void;
  onEdit?: (scenario: TestScenario) => void;
  onDelete?: (scenario: TestScenario) => void;
}

export function TestScenariosTable({
  scenarios,
  testSuites,
  personas,
  filters,
  onFiltersChange,
  showSuiteColumn = true,
  showSuiteFilter = true,
  loading = false,
  onRowClick,
  onEdit,
  onDelete,
}: TestScenariosTableProps) {
  // Helper: Get suite name by ID
  const getSuiteName = (suiteId: string): string => {
    return testSuites.find((s) => s.id === suiteId)?.name || "Unknown Suite";
  };

  // Helper: Get persona name by ID
  const getPersonaName = (personaId: string): string => {
    return personas.find((p) => p.id === personaId)?.name || "Unknown";
  };

  // Filter handlers
  const handleSearchChange = (value: string) => {
    onFiltersChange({ ...filters, search: value || undefined });
  };

  const handleSuiteChange = (value: string) => {
    onFiltersChange({ ...filters, suiteId: value === "all" ? undefined : value });
  };

  const handlePersonaChange = (value: string) => {
    onFiltersChange({ ...filters, personaId: value === "all" ? undefined : value });
  };

  const handleStatusChange = (value: string) => {
    onFiltersChange({
      ...filters,
      status: value === "all" ? undefined : (value as "ready" | "draft"),
    });
  };

  // Loading skeleton
  if (loading && scenarios.length === 0) {
    return (
      <div className="space-y-4">
        <div className="flex gap-3">
          <Skeleton className="h-10 w-64" />
          <Skeleton className="h-10 w-36" />
          <Skeleton className="h-10 w-36" />
          <Skeleton className="h-10 w-32" />
        </div>
        <div className="rounded-lg border">
          <div className="space-y-3 p-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filter Bar */}
      <div className="flex flex-wrap items-center gap-3">
        {/* Search */}
        <div className="relative max-w-sm flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search scenarios..."
            value={filters.search || ""}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="pl-9"
          />
        </div>

        {/* Suite Filter */}
        {showSuiteFilter && (
          <Select value={filters.suiteId || "all"} onValueChange={handleSuiteChange}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder="All Test Suites" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Test Suites</SelectItem>
              {testSuites.map((suite) => (
                <SelectItem key={suite.id} value={suite.id}>
                  {suite.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}

        {/* Persona Filter */}
        <Select value={filters.personaId || "all"} onValueChange={handlePersonaChange}>
          <SelectTrigger className="w-36">
            <SelectValue placeholder="All Personas" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Personas</SelectItem>
            {personas.map((persona) => (
              <SelectItem key={persona.id} value={persona.id}>
                {persona.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* Status Filter */}
        <Select value={filters.status || "all"} onValueChange={handleStatusChange}>
          <SelectTrigger className="w-32">
            <SelectValue placeholder="All Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="ready">Ready</SelectItem>
            <SelectItem value="draft">Draft</SelectItem>
          </SelectContent>
        </Select>

        {/* Results Count */}
        <span className="ml-auto text-sm text-muted-foreground">
          {scenarios.length} scenario{scenarios.length !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Empty State */}
      {scenarios.length === 0 ? (
        <div className="py-12 text-center text-muted-foreground">
          No scenarios found matching your filters.
        </div>
      ) : (
        /* Table */
        <div className="rounded-lg border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[300px]">Scenario</TableHead>
                {showSuiteColumn && <TableHead>Test Suite</TableHead>}
                <TableHead>Persona</TableHead>
                <TableHead className="text-center">Status</TableHead>
                <TableHead className="w-[100px] text-center">Pass %</TableHead>
                <TableHead className="w-[160px]">Last Run</TableHead>
                <TableHead className="w-[50px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {scenarios.map((scenario) => {
                const personaName = scenario.persona_name ?? getPersonaName(scenario.persona_id);
                return (
                  <TableRow
                    key={scenario.id}
                    className="cursor-pointer hover:bg-muted/50"
                    onClick={() => onRowClick?.(scenario)}
                  >
                    <TableCell>
                      <div className="flex flex-col gap-1">
                        <span className="font-medium">{scenario.name}</span>
                        {scenario.tags && scenario.tags.length > 0 && (
                          <div className="flex gap-1">
                            {scenario.tags.slice(0, 2).map((tag) => (
                              <Badge key={tag} variant="secondary" className="text-xs">
                                {tag}
                              </Badge>
                            ))}
                            {scenario.tags.length > 2 && (
                              <span className="text-xs text-muted-foreground">
                                +{scenario.tags.length - 2}
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                    </TableCell>
                    {showSuiteColumn && (
                      <TableCell className="text-muted-foreground">
                        {getSuiteName(scenario.suite_id)}
                      </TableCell>
                    )}
                    <TableCell className="capitalize">{personaName}</TableCell>
                    <TableCell className="text-center">
                      <Badge
                        variant="outline"
                        className={cn(
                          scenario.status === "ready"
                            ? "border-green-200 bg-green-500/10 text-green-600"
                            : "border-yellow-200 bg-yellow-500/10 text-yellow-600"
                        )}
                      >
                        {scenario.status === "ready" ? "Ready" : "Draft"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-center font-medium">—</TableCell>
                    <TableCell className="text-sm text-muted-foreground">Never</TableCell>
                    <TableCell>
                      <ChevronRight className="h-4 w-4 text-muted-foreground" />
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}
