"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { api } from "@/lib/api";
import { logger } from "@/lib/logger";
import type {
  TestScenario,
  TestScenarioFilters,
  TestScenarioUpdateRequest,
  TestSuite,
  PersonaListItem,
} from "@/lib/types";

export interface UseTestScenariosFilters {
  suiteId?: string;
  personaId?: string;
  status?: "ready" | "draft";
  search?: string;
}

export interface UseTestScenariosOptions {
  /** Organization ID for scoping persona queries */
  orgId?: string;
  initialFilters?: UseTestScenariosFilters;
  debounceMs?: number;
  pageSize?: number;
}

export interface UseTestScenariosReturn {
  // Data
  scenarios: TestScenario[];
  testSuites: TestSuite[];
  personas: PersonaListItem[];

  // Filter state
  filters: UseTestScenariosFilters;
  setFilters: (filters: UseTestScenariosFilters) => void;

  // Pagination state
  page: number;
  pageSize: number;
  totalCount: number;
  totalPages: number;
  setPage: (page: number) => void;
  setPageSize: (pageSize: number) => void;

  // Loading/error
  loading: boolean;
  error: string | null;

  // Fetch action
  refetch: () => Promise<void>;

  // Mutation actions
  updateScenario: (id: string, data: TestScenarioUpdateRequest) => Promise<TestScenario>;
  deleteScenario: (id: string) => Promise<void>;

  // Mutation state
  isUpdating: boolean;
  isDeleting: boolean;
}

export function useTestScenarios(options: UseTestScenariosOptions = {}): UseTestScenariosReturn {
  const {
    orgId = "",
    initialFilters = {},
    debounceMs = 300,
    pageSize: initialPageSize = 20,
  } = options;

  // State
  const [scenarios, setScenarios] = useState<TestScenario[]>([]);
  const [testSuites, setTestSuites] = useState<TestSuite[]>([]);
  const [personas, setPersonas] = useState<PersonaListItem[]>([]);
  const [filters, setFiltersState] = useState<UseTestScenariosFilters>(initialFilters);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isUpdating, setIsUpdating] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  // Pagination state
  const [page, setPageState] = useState(1);
  const [pageSize, setPageSizeState] = useState(initialPageSize);
  const [totalCount, setTotalCount] = useState(0);
  const totalPages = Math.ceil(totalCount / pageSize);

  // Debounce timer ref
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Track request ID to ignore stale responses
  const requestIdRef = useRef(0);

  // Track previous search value to detect changes without stale closure
  const prevSearchRef = useRef<string | undefined>(initialFilters.search);

  // Convert our filters to API filters format
  const buildApiFilters = useCallback(
    (f: UseTestScenariosFilters, currentPage: number): TestScenarioFilters => {
      const apiFilters: TestScenarioFilters = {};
      if (f.suiteId) apiFilters.suite_id = f.suiteId;
      if (f.personaId) apiFilters.persona_id = f.personaId;
      if (f.status) apiFilters.status = f.status;
      if (f.search) apiFilters.search = f.search;
      // Add pagination
      apiFilters.limit = pageSize;
      apiFilters.offset = (currentPage - 1) * pageSize;
      return apiFilters;
    },
    [pageSize]
  );

  // Fetch scenarios with current filters and page
  const fetchScenarios = useCallback(
    async (currentFilters: UseTestScenariosFilters, currentPage: number) => {
      const requestId = ++requestIdRef.current;
      try {
        setLoading(true);
        setError(null);
        const apiFilters = buildApiFilters(currentFilters, currentPage);
        const response = await api.testScenarios.listTestScenarios(apiFilters);
        // Ignore stale responses
        if (requestId !== requestIdRef.current) return;
        setScenarios(response.scenarios);
        setTotalCount(response.count);
      } catch (err) {
        // Ignore errors from stale requests
        if (requestId !== requestIdRef.current) return;
        const errorMessage = err instanceof Error ? err.message : "Failed to load scenarios";
        setError(errorMessage);
        logger.error("Failed to fetch scenarios", err);
      } finally {
        // Only update loading state for current request
        if (requestId === requestIdRef.current) {
          setLoading(false);
        }
      }
    },
    [buildApiFilters]
  );

  // Fetch reference data (suites and personas) - called once on mount
  const fetchReferenceData = useCallback(async () => {
    if (!orgId) return;
    try {
      const [suitesResponse, personasResponse] = await Promise.all([
        api.testSuites.listTestSuites(orgId),
        api.personas.listPersonas(orgId, true), // active personas only
      ]);
      setTestSuites(suitesResponse.suites);
      setPersonas(personasResponse.personas);
    } catch (err) {
      logger.error("Failed to fetch reference data", err);
      // Non-critical error - don't set error state, filters will still work
    }
  }, [orgId]);

  // Initial fetch on mount
  useEffect(() => {
    fetchReferenceData();
    fetchScenarios(initialFilters, 1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Set filters with debounced fetch for search (resets page to 1)
  const setFilters = useCallback(
    (newFilters: UseTestScenariosFilters) => {
      setFiltersState(newFilters);
      setPageState(1); // Reset to first page when filters change

      // Clear existing timer
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }

      // Check if search changed (needs debounce) vs other filters (immediate)
      const searchChanged = newFilters.search !== prevSearchRef.current;
      prevSearchRef.current = newFilters.search; // Update ref immediately

      if (searchChanged && newFilters.search) {
        // Debounce search
        debounceTimerRef.current = setTimeout(() => {
          fetchScenarios(newFilters, 1);
        }, debounceMs);
      } else {
        // Immediate fetch for non-search filter changes
        fetchScenarios(newFilters, 1);
      }
    },
    [debounceMs, fetchScenarios]
  );

  // Set page and fetch
  const setPage = useCallback(
    (newPage: number) => {
      setPageState(newPage);
      fetchScenarios(filters, newPage);
    },
    [fetchScenarios, filters]
  );

  // Set page size and reset to page 1
  const setPageSize = useCallback(
    (newPageSize: number) => {
      setPageSizeState(newPageSize);
      setPageState(1); // Reset to first page when page size changes
      // Need to fetch with new page size - buildApiFilters will use updated state
      // We fetch immediately since pageSize state update is async
      const apiFilters: TestScenarioFilters = {};
      if (filters.suiteId) apiFilters.suite_id = filters.suiteId;
      if (filters.personaId) apiFilters.persona_id = filters.personaId;
      if (filters.status) apiFilters.status = filters.status;
      if (filters.search) apiFilters.search = filters.search;
      apiFilters.limit = newPageSize;
      apiFilters.offset = 0;

      const requestId = ++requestIdRef.current;
      setLoading(true);
      api.testScenarios
        .listTestScenarios(apiFilters)
        .then((response) => {
          if (requestId === requestIdRef.current) {
            setScenarios(response.scenarios);
            setTotalCount(response.count);
            setLoading(false);
          }
        })
        .catch((err) => {
          if (requestId === requestIdRef.current) {
            setError(err instanceof Error ? err.message : "Failed to load scenarios");
            setLoading(false);
          }
        });
    },
    [filters]
  );

  // Cleanup debounce timer on unmount
  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);

  // Refetch with current filters and page
  const refetch = useCallback(async () => {
    await fetchScenarios(filters, page);
  }, [fetchScenarios, filters, page]);

  // Update a scenario and refetch list
  const updateScenario = useCallback(
    async (id: string, data: TestScenarioUpdateRequest): Promise<TestScenario> => {
      setIsUpdating(true);
      try {
        const updated = await api.testScenarios.updateTestScenario(id, data);
        // Refetch to get updated list
        await fetchScenarios(filters, page);
        return updated;
      } catch (err) {
        logger.error("Failed to update scenario", err);
        throw err;
      } finally {
        setIsUpdating(false);
      }
    },
    [fetchScenarios, filters, page]
  );

  // Delete a scenario and refetch list
  const deleteScenario = useCallback(
    async (id: string): Promise<void> => {
      setIsDeleting(true);
      try {
        await api.testScenarios.deleteTestScenario(id);
        // Refetch to get updated list
        await fetchScenarios(filters, page);
      } catch (err) {
        logger.error("Failed to delete scenario", err);
        throw err;
      } finally {
        setIsDeleting(false);
      }
    },
    [fetchScenarios, filters, page]
  );

  return {
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
    error,
    refetch,
    updateScenario,
    deleteScenario,
    isUpdating,
    isDeleting,
  };
}
