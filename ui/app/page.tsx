"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { api, type AnalysisResponse, type ConversationsListResponse, type FailuresListResponse } from "@/lib/api";
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from "recharts";
import { AlertCircle, TrendingUp, MessageSquare, AlertTriangle } from "lucide-react";

const COLORS = {
  low: "#10b981",
  medium: "#f59e0b",
  high: "#ef4444",
  critical: "#dc2626",
};

export default function DashboardPage() {
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [conversations, setConversations] = useState<ConversationsListResponse | null>(null);
  const [failures, setFailures] = useState<FailuresListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        setError(null);
        const [analysisData, conversationsData, failuresData] = await Promise.all([
          api.conversations.analyzeAll(),
          api.conversations.listConversations(),
          api.conversations.listFailures(),
        ]);
        setAnalysis(analysisData);
        setConversations(conversationsData);
        setFailures(failuresData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load dashboard data");
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <Skeleton className="h-9 w-48 mb-2" />
          <Skeleton className="h-5 w-96" />
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <Skeleton className="h-4 w-32" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-16 mb-2" />
                <Skeleton className="h-4 w-24" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">Overview of your voice AI conversations</p>
        </div>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-destructive">
              <AlertCircle className="h-5 w-5" />
              <p>Error loading dashboard: {error}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const totalConversations = analysis?.summary.total_conversations ?? 0;
  const totalFailures = failures?.count ?? 0;
  const avgLatency = analysis?.stages.llm.mean_ms ?? null;
  const totalTurns = analysis?.summary.total_turns ?? 0;

  // Prepare failure breakdown data
  const failureBreakdown = failures?.by_type
    ? Object.entries(failures.by_type).map(([type, count]) => ({
        name: type.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase()),
        value: count,
      }))
    : [];

  // Prepare latency data for trend chart (using stage metrics)
  const latencyData = analysis?.stages
    ? [
        {
          stage: "ASR",
          mean: analysis.stages.asr.mean_ms ?? 0,
          p95: analysis.stages.asr.p95_ms ?? 0,
        },
        {
          stage: "LLM",
          mean: analysis.stages.llm.mean_ms ?? 0,
          p95: analysis.stages.llm.p95_ms ?? 0,
        },
        {
          stage: "TTS",
          mean: analysis.stages.tts.mean_ms ?? 0,
          p95: analysis.stages.tts.p95_ms ?? 0,
        },
      ]
    : [];

  // Get recent conversations (first 5)
  const recentConversations = conversations?.conversations.slice(0, 5) ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">Overview of your voice AI conversations</p>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Conversations</CardTitle>
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalConversations}</div>
            <p className="text-xs text-muted-foreground">{totalTurns} total turns</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Failures</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalFailures}</div>
            <p className="text-xs text-muted-foreground">
              {failures?.by_severity
                ? Object.entries(failures.by_severity)
                    .map(([sev, count]) => `${sev}: ${count}`)
                    .join(", ")
                : "No failures"}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Latency</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {avgLatency !== null ? `${avgLatency.toFixed(0)}ms` : "-"}
            </div>
            <p className="text-xs text-muted-foreground">LLM mean latency</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Spans</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analysis?.summary.total_spans ?? 0}</div>
            <p className="text-xs text-muted-foreground">All pipeline stages</p>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Failure Breakdown Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Failure Breakdown</CardTitle>
            <CardDescription>Failures grouped by type</CardDescription>
          </CardHeader>
          <CardContent>
            {failureBreakdown.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={failureBreakdown}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name}: ${((percent ?? 0) * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {failureBreakdown.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[Object.keys(COLORS)[index % 4] as keyof typeof COLORS]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-[300px] text-muted-foreground">
                No failures detected
              </div>
            )}
          </CardContent>
        </Card>

        {/* Latency Trend Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Stage Latency</CardTitle>
            <CardDescription>Mean and P95 latency by stage</CardDescription>
          </CardHeader>
          <CardContent>
            {latencyData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={latencyData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="stage" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="mean" fill="#8884d8" name="Mean (ms)" />
                  <Bar dataKey="p95" fill="#82ca9d" name="P95 (ms)" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-[300px] text-muted-foreground">
                No latency data available
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent Conversations */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Recent Conversations</CardTitle>
              <CardDescription>Latest voice conversations</CardDescription>
            </div>
            <Button variant="outline" asChild>
              <Link href="/conversations">View All</Link>
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {recentConversations.length > 0 ? (
            <div className="space-y-4">
              {recentConversations.map((conv) => (
                <div
                  key={conv.id}
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-accent transition-colors"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <Link
                        href={`/conversations/${conv.id}`}
                        className="font-medium hover:underline"
                      >
                        {conv.id}
                      </Link>
                      {conv.has_failures && (
                        <Badge variant="destructive" className="text-xs">
                          Has Failures
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <span>{conv.turn_count} turns</span>
                      <span>{conv.span_count} spans</span>
                    </div>
                  </div>
                  <Button variant="ghost" size="sm" asChild>
                    <Link href={`/conversations/${conv.id}`}>View →</Link>
                  </Button>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <MessageSquare className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>No conversations yet</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
