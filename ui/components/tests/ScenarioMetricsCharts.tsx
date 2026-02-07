"use client";

import {
  AreaChart,
  Area,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/primitives/card";

interface RunData {
  id: string;
  created_at: string;
  passed: boolean;
  duration_seconds?: number;
}

interface ScenarioMetricsChartsProps {
  runs: RunData[];
}

export function ScenarioMetricsCharts({ runs }: ScenarioMetricsChartsProps) {
  // Process runs into chart data - group by date and calculate metrics
  // For pass rate: calculate rolling/daily pass rate
  // For latency: use duration_seconds

  // Sort runs by date
  const sortedRuns = [...runs].sort(
    (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
  );

  // Calculate cumulative pass rate data
  const passRateData = sortedRuns.map((run, index) => {
    const runsUpToNow = sortedRuns.slice(0, index + 1);
    const passCount = runsUpToNow.filter((r) => r.passed).length;
    const passRate = (passCount / runsUpToNow.length) * 100;
    return {
      date: new Date(run.created_at).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
      }),
      passRate: Math.round(passRate),
    };
  });

  // Latency data
  const latencyData = sortedRuns
    .filter((run) => run.duration_seconds != null)
    .map((run) => ({
      date: new Date(run.created_at).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
      }),
      latency: run.duration_seconds,
    }));

  if (runs.length === 0) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-muted-foreground">
          No run data available for charts
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-4">
      {/* Pass Rate Trend */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">Pass Rate Trend</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[200px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={passRateData}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
                <YAxis
                  domain={[0, 100]}
                  tick={{ fontSize: 11 }}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(value) => `${value}%`}
                />
                <Tooltip
                  formatter={(value) => [`${value}%`, "Pass Rate"]}
                  contentStyle={{ fontSize: 12 }}
                />
                <Area
                  type="monotone"
                  dataKey="passRate"
                  stroke="#22c55e"
                  fill="#22c55e"
                  fillOpacity={0.2}
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Latency Chart */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">Response Latency</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[200px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={latencyData}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
                <YAxis
                  tick={{ fontSize: 11 }}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(value) => `${value}s`}
                />
                <Tooltip
                  formatter={(value) => [`${value}s`, "Latency"]}
                  contentStyle={{ fontSize: 12 }}
                />
                <Line
                  type="monotone"
                  dataKey="latency"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={{ fill: "#3b82f6", strokeWidth: 0, r: 3 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
