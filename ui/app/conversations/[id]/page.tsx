import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function ConversationDetailPage({ params }: { params: { id: string } }) {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Conversation Details</h1>
        <p className="text-muted-foreground">Conversation ID: {params.id}</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Conversation {params.id}</CardTitle>
          <CardDescription>Detailed view of conversation turns and analysis</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Loading conversation details...</p>
        </CardContent>
      </Card>
    </div>
  );
}
