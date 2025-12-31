import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function FailuresPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Failures</h1>
        <p className="text-muted-foreground">Detected quality issues in conversations</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Detected Failures</CardTitle>
          <CardDescription>Quality issues detected in voice conversations</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Loading failures...</p>
        </CardContent>
      </Card>
    </div>
  );
}
