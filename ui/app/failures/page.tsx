"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { api, type FailuresListResponse, type FailureResponse } from "@/lib/api";
import { AlertCircle, Filter, AlertTriangle } from "lucide-react";

export default function FailuresPage() {
  const [data, setData] = useState<FailuresListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [severityFilter, setSeverityFilter] = useState<string>("all");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [groupBy, setGroupBy] = useState<"none" | "severity" | "type">("none");

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        setError(null);
        const response = await api.conversations.listFailures(
          severityFilter !== "all" ? severityFilter : undefined,
          typeFilter !== "all" ? typeFilter : undefined
        );
        setData(response);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load failures");
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [severityFilter, typeFilter]);

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <Skeleton className="h-9 w-48 mb-2" />
          <Skeleton className="h-5 w-96" />
        </div>
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-48" />
            <Skeleton className="h-4 w-64" />
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {[1, 2, 3, 4, 5].map((i) => (
                <Skeleton key={i} className="h-12 w-full" />
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
          <h1 className="text-3xl font-bold tracking-tight">Failures</h1>
          <p className="text-muted-foreground">Detected quality issues in conversations</p>
        </div>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-destructive">
              <AlertCircle className="h-5 w-5" />
              <p>Error loading failures: {error}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const failures = data?.failures ?? [];
  const severities = data?.by_severity ? Object.keys(data.by_severity) : [];
  const types = data?.by_type ? Object.keys(data.by_type) : [];

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case "critical":
        return "destructive";
      case "high":
        return "destructive";
      case "medium":
        return "default";
      case "low":
        return "secondary";
      default:
        return "secondary";
    }
  };

  // Group failures if needed
  const groupedFailures = (() => {
    if (groupBy === "none") {
      return { "All Failures": failures };
    }
    if (groupBy === "severity") {
      const grouped: Record<string, FailureResponse[]> = {};
      failures.forEach((failure) => {
        const key = failure.severity;
        if (!grouped[key]) grouped[key] = [];
        grouped[key].push(failure);
      });
      return grouped;
    }
    if (groupBy === "type") {
      const grouped: Record<string, FailureResponse[]> = {};
      failures.forEach((failure) => {
        const key = failure.type;
        if (!grouped[key]) grouped[key] = [];
        grouped[key].push(failure);
      });
      return grouped;
    }
    return { "All Failures": failures };
  })();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Failures</h1>
        <p className="text-muted-foreground">Detected quality issues in conversations</p>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Total Failures</CardDescription>
            <CardTitle className="text-2xl">{data?.count ?? 0}</CardTitle>
          </CardHeader>
        </Card>
        {severities.map((severity) => (
          <Card key={severity}>
            <CardHeader className="pb-2">
              <CardDescription className="capitalize">{severity} Severity</CardDescription>
              <CardTitle className="text-2xl">{data?.by_severity[severity] ?? 0}</CardTitle>
            </CardHeader>
          </Card>
        ))}
      </div>

      {/* Filters and Grouping */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>All Failures</CardTitle>
              <CardDescription>
                {failures.length} {failures.length === 1 ? "failure" : "failures"} detected
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <Select value={severityFilter} onValueChange={setSeverityFilter}>
                <SelectTrigger className="w-[140px]">
                  <SelectValue placeholder="Severity" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Severities</SelectItem>
                  {severities.map((sev) => (
                    <SelectItem key={sev} value={sev}>
                      {sev.charAt(0).toUpperCase() + sev.slice(1)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={typeFilter} onValueChange={setTypeFilter}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  {types.map((type) => (
                    <SelectItem key={type} value={type}>
                      {type.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={groupBy} onValueChange={(v) => setGroupBy(v as typeof groupBy)}>
                <SelectTrigger className="w-[140px]">
                  <SelectValue placeholder="Group By" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">No Grouping</SelectItem>
                  <SelectItem value="severity">Group by Severity</SelectItem>
                  <SelectItem value="type">Group by Type</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {failures.length > 0 ? (
            <div className="space-y-6">
              {Object.entries(groupedFailures).map(([groupName, groupFailures]) => (
                <div key={groupName} className="space-y-2">
                  {groupBy !== "none" && (
                    <h3 className="text-lg font-semibold mb-2">{groupName}</h3>
                  )}
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Type</TableHead>
                        <TableHead>Severity</TableHead>
                        <TableHead>Message</TableHead>
                        <TableHead>Conversation</TableHead>
                        <TableHead>Turn</TableHead>
                        <TableHead>Signal</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {groupFailures.map((failure) => (
                        <TableRow key={failure.id}>
                          <TableCell>
                            <Badge variant="outline">
                              {failure.type.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <Badge variant={getSeverityColor(failure.severity) as any}>
                              {failure.severity}
                            </Badge>
                          </TableCell>
                          <TableCell className="max-w-md">
                            <div className="flex items-start gap-2">
                              <AlertTriangle className="h-4 w-4 text-destructive mt-0.5 flex-shrink-0" />
                              <span className="text-sm">{failure.message}</span>
                            </div>
                          </TableCell>
                          <TableCell>
                            {failure.conversation_id ? (
                              <Link
                                href={`/conversations/${failure.conversation_id}`}
                                className="text-primary hover:underline text-sm"
                              >
                                {failure.conversation_id.slice(0, 8)}...
                              </Link>
                            ) : (
                              <span className="text-muted-foreground text-sm">-</span>
                            )}
                          </TableCell>
                          <TableCell>
                            {failure.turn_index !== null ? (
                              <span className="text-sm">Turn #{failure.turn_index}</span>
                            ) : (
                              <span className="text-muted-foreground text-sm">-</span>
                            )}
                          </TableCell>
                          <TableCell>
                            {failure.signal_name && failure.signal_value !== null ? (
                              <div className="text-sm">
                                <div className="font-medium">{failure.signal_name}</div>
                                <div className="text-muted-foreground">
                                  {failure.signal_value.toFixed(2)}
                                  {failure.threshold !== null && (
                                    <span> / {failure.threshold.toFixed(2)}</span>
                                  )}
                                </div>
                              </div>
                            ) : (
                              <span className="text-muted-foreground text-sm">-</span>
                            )}
                          </TableCell>
                          <TableCell className="text-right">
                            {failure.conversation_id && (
                              <Button variant="ghost" size="sm" asChild>
                                <Link href={`/conversations/${failure.conversation_id}`}>
                                  View Conversation
                                </Link>
                              </Button>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-muted-foreground">
              <AlertCircle className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>No failures found</p>
              {(severityFilter !== "all" || typeFilter !== "all") && (
                <p className="text-sm mt-2">Try adjusting your filters</p>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
