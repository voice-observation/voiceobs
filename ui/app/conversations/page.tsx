import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function ConversationsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Conversations</h1>
        <p className="text-muted-foreground">View and analyze voice conversations</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Conversations List</CardTitle>
          <CardDescription>All voice conversations will appear here</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Loading conversations...</p>
        </CardContent>
      </Card>
    </div>
  );
}
