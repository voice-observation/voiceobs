"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api, type ConversationDetail, type TurnResponse, type FailureResponse } from "@/lib/api";
import { AlertCircle, ArrowLeft, User, Bot, Clock } from "lucide-react";
import { AudioPlayer } from "@/components/audio/AudioPlayer";
import { getAudioUrl } from "@/lib/audio";

export default function ConversationDetailPage({ params }: { params: { id: string } }) {
  const [conversation, setConversation] = useState<ConversationDetail | null>(null);
  const [failures, setFailures] = useState<FailureResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        setError(null);
        const [convData, failuresData] = await Promise.all([
          api.getConversation(params.id),
          api.listFailures().then((data) =>
            data.failures.filter((f) => f.conversation_id === params.id)
          ),
        ]);
        setConversation(convData);
        setFailures(failuresData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load conversation");
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [params.id]);

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <Skeleton className="h-9 w-48 mb-2" />
          <Skeleton className="h-5 w-96" />
        </div>
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-64" />
            <Skeleton className="h-4 w-96" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-64 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <Button variant="ghost" size="sm" asChild className="mb-4">
            <Link href="/conversations">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Conversations
            </Link>
          </Button>
          <h1 className="text-3xl font-bold tracking-tight">Conversation Details</h1>
          <p className="text-muted-foreground">Conversation ID: {params.id}</p>
        </div>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-destructive">
              <AlertCircle className="h-5 w-5" />
              <p>Error loading conversation: {error}</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!conversation) {
    return (
      <div className="space-y-6">
        <div>
          <Button variant="ghost" size="sm" asChild className="mb-4">
            <Link href="/conversations">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Conversations
            </Link>
          </Button>
          <h1 className="text-3xl font-bold tracking-tight">Conversation Details</h1>
        </div>
        <Card>
          <CardContent className="pt-6">
            <p className="text-muted-foreground">Conversation not found</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const formatDuration = (durationMs: number | null) => {
    if (durationMs === null) return "-";
    if (durationMs < 1000) return `${durationMs.toFixed(0)}ms`;
    return `${(durationMs / 1000).toFixed(1)}s`;
  };

  const getTurnFailures = (turnIndex: number | null) => {
    if (turnIndex === null) return [];
    return failures.filter((f) => f.turn_index === turnIndex);
  };

  const getStageMetrics = (turn: TurnResponse) => {
    const attrs = turn.attributes || {};
    return {
      asr: attrs["voice.asr.duration_ms"] || attrs["asr.duration_ms"],
      llm: attrs["voice.llm.duration_ms"] || attrs["llm.duration_ms"],
      tts: attrs["voice.tts.duration_ms"] || attrs["tts.duration_ms"],
    };
  };

  return (
    <div className="space-y-6">
      <div>
        <Button variant="ghost" size="sm" asChild className="mb-4">
          <Link href="/conversations">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Conversations
          </Link>
        </Button>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Conversation Details</h1>
            <p className="text-muted-foreground">ID: {conversation.id}</p>
          </div>
          {failures.length > 0 && (
            <Badge variant="destructive" className="text-sm">
              {failures.length} {failures.length === 1 ? "Failure" : "Failures"}
            </Badge>
          )}
        </div>
      </div>

      {/* Metadata Header */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Total Turns</CardDescription>
            <CardTitle className="text-2xl">{conversation.turns.length}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Total Spans</CardDescription>
            <CardTitle className="text-2xl">{conversation.span_count}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Failures</CardDescription>
            <CardTitle className="text-2xl">{failures.length}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Status</CardDescription>
            <CardTitle className="text-2xl">
              {failures.length > 0 ? (
                <Badge variant="destructive">Issues</Badge>
              ) : (
                <Badge variant="secondary">Healthy</Badge>
              )}
            </CardTitle>
          </CardHeader>
        </Card>
      </div>

      {/* Audio Player */}
      <Card>
        <CardHeader>
          <CardTitle>Audio</CardTitle>
        </CardHeader>
        <CardContent>
          <AudioPlayer audioUrl={getAudioUrl(conversation.id)} conversationId={conversation.id} />
        </CardContent>
      </Card>

      {/* Tabs for different views */}
      <Tabs defaultValue="turns" className="w-full">
        <TabsList>
          <TabsTrigger value="turns">Turns & Timeline</TabsTrigger>
          <TabsTrigger value="transcript">Transcript</TabsTrigger>
          <TabsTrigger value="analysis">Analysis</TabsTrigger>
        </TabsList>

        <TabsContent value="turns">
          <Card>
            <CardHeader>
              <CardTitle>Conversation Turns</CardTitle>
              <CardDescription>Timeline view of all turns with stage breakdown</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {conversation.turns.map((turn, idx) => {
                  const turnFailures = getTurnFailures(turn.turn_index);
                  const stageMetrics = getStageMetrics(turn);
                  const isUser = turn.actor === "user";

                  return (
                    <div key={turn.id} className="border-l-2 border-muted pl-4 space-y-2">
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-2">
                          {isUser ? (
                            <User className="h-5 w-5 text-blue-500" />
                          ) : (
                            <Bot className="h-5 w-5 text-green-500" />
                          )}
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-medium">
                                {isUser ? "User" : "Agent"} Turn #{turn.turn_index ?? idx}
                              </span>
                              {turnFailures.length > 0 && (
                                <Badge variant="destructive" className="text-xs">
                                  {turnFailures.length} {turnFailures.length === 1 ? "failure" : "failures"}
                                </Badge>
                              )}
                            </div>
                            {turn.transcript && (
                              <p className="text-sm text-muted-foreground mt-1">{turn.transcript}</p>
                            )}
                          </div>
                        </div>
                        <div className="text-right text-sm text-muted-foreground">
                          <div className="flex items-center gap-1">
                            <Clock className="h-4 w-4" />
                            {formatDuration(turn.duration_ms)}
                          </div>
                        </div>
                      </div>

                      {/* Stage Breakdown */}
                      {(stageMetrics.asr || stageMetrics.llm || stageMetrics.tts) && (
                        <div className="ml-7 grid grid-cols-3 gap-2 text-xs">
                          {stageMetrics.asr && (
                            <div className="p-2 bg-blue-50 dark:bg-blue-950 rounded">
                              <div className="font-medium">ASR</div>
                              <div className="text-muted-foreground">
                                {typeof stageMetrics.asr === "number"
                                  ? formatDuration(stageMetrics.asr)
                                  : "-"}
                              </div>
                            </div>
                          )}
                          {stageMetrics.llm && (
                            <div className="p-2 bg-purple-50 dark:bg-purple-950 rounded">
                              <div className="font-medium">LLM</div>
                              <div className="text-muted-foreground">
                                {typeof stageMetrics.llm === "number"
                                  ? formatDuration(stageMetrics.llm)
                                  : "-"}
                              </div>
                            </div>
                          )}
                          {stageMetrics.tts && (
                            <div className="p-2 bg-green-50 dark:bg-green-950 rounded">
                              <div className="font-medium">TTS</div>
                              <div className="text-muted-foreground">
                                {typeof stageMetrics.tts === "number"
                                  ? formatDuration(stageMetrics.tts)
                                  : "-"}
                              </div>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Failure Annotations */}
                      {turnFailures.length > 0 && (
                        <div className="ml-7 space-y-1">
                          {turnFailures.map((failure) => (
                            <div
                              key={failure.id}
                              className="p-2 bg-destructive/10 border border-destructive/20 rounded text-sm"
                            >
                              <div className="flex items-center gap-2">
                                <AlertCircle className="h-4 w-4 text-destructive" />
                                <Badge variant="destructive" className="text-xs">
                                  {failure.severity}
                                </Badge>
                                <span className="font-medium">{failure.type}</span>
                              </div>
                              <p className="text-muted-foreground mt-1">{failure.message}</p>
                              {failure.signal_value !== null && failure.threshold !== null && (
                                <p className="text-xs text-muted-foreground mt-1">
                                  Signal: {failure.signal_value} (threshold: {failure.threshold})
                                </p>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="transcript">
          <Card>
            <CardHeader>
              <CardTitle>Transcript</CardTitle>
              <CardDescription>Full conversation transcript</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {conversation.turns.map((turn, idx) => {
                  const isUser = turn.actor === "user";
                  return (
                    <div
                      key={turn.id}
                      className={`flex gap-3 ${isUser ? "flex-row" : "flex-row-reverse"}`}
                    >
                      <div
                        className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                          isUser ? "bg-blue-100 dark:bg-blue-900" : "bg-green-100 dark:bg-green-900"
                        }`}
                      >
                        {isUser ? (
                          <User className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                        ) : (
                          <Bot className="h-4 w-4 text-green-600 dark:text-green-400" />
                        )}
                      </div>
                      <div
                        className={`flex-1 rounded-lg p-3 ${
                          isUser
                            ? "bg-blue-50 dark:bg-blue-950"
                            : "bg-green-50 dark:bg-green-950"
                        }`}
                      >
                        <div className="text-sm font-medium mb-1">
                          {isUser ? "User" : "Agent"}
                        </div>
                        <div className="text-sm">
                          {turn.transcript || <span className="text-muted-foreground italic">No transcript</span>}
                        </div>
                        {turn.duration_ms !== null && (
                          <div className="text-xs text-muted-foreground mt-2">
                            Duration: {formatDuration(turn.duration_ms)}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="analysis">
          <Card>
            <CardHeader>
              <CardTitle>Analysis</CardTitle>
              <CardDescription>Detailed metrics and analysis for this conversation</CardDescription>
            </CardHeader>
            <CardContent>
              {conversation.analysis ? (
                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg font-semibold mb-3">Stage Metrics</h3>
                    <div className="grid gap-4 md:grid-cols-3">
                      <Card>
                        <CardHeader className="pb-2">
                          <CardDescription>ASR</CardDescription>
                          <CardTitle className="text-xl">
                            {conversation.analysis.stages.asr.mean_ms
                              ? `${conversation.analysis.stages.asr.mean_ms.toFixed(0)}ms`
                              : "-"}
                          </CardTitle>
                          <CardDescription className="text-xs">
                            Count: {conversation.analysis.stages.asr.count}
                          </CardDescription>
                        </CardHeader>
                      </Card>
                      <Card>
                        <CardHeader className="pb-2">
                          <CardDescription>LLM</CardDescription>
                          <CardTitle className="text-xl">
                            {conversation.analysis.stages.llm.mean_ms
                              ? `${conversation.analysis.stages.llm.mean_ms.toFixed(0)}ms`
                              : "-"}
                          </CardTitle>
                          <CardDescription className="text-xs">
                            Count: {conversation.analysis.stages.llm.count}
                          </CardDescription>
                        </CardHeader>
                      </Card>
                      <Card>
                        <CardHeader className="pb-2">
                          <CardDescription>TTS</CardDescription>
                          <CardTitle className="text-xl">
                            {conversation.analysis.stages.tts.mean_ms
                              ? `${conversation.analysis.stages.tts.mean_ms.toFixed(0)}ms`
                              : "-"}
                          </CardTitle>
                          <CardDescription className="text-xs">
                            Count: {conversation.analysis.stages.tts.count}
                          </CardDescription>
                        </CardHeader>
                      </Card>
                    </div>
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold mb-3">Turn Metrics</h3>
                    <div className="grid gap-4 md:grid-cols-2">
                      <Card>
                        <CardHeader className="pb-2">
                          <CardDescription>Interruptions</CardDescription>
                          <CardTitle className="text-xl">
                            {conversation.analysis.turns.interruptions}
                          </CardTitle>
                          <CardDescription className="text-xs">
                            Rate:{" "}
                            {conversation.analysis.turns.interruption_rate !== null
                              ? `${conversation.analysis.turns.interruption_rate.toFixed(1)}%`
                              : "-"}
                          </CardDescription>
                        </CardHeader>
                      </Card>
                      <Card>
                        <CardHeader className="pb-2">
                          <CardDescription>Silence After User</CardDescription>
                          <CardTitle className="text-xl">
                            {conversation.analysis.turns.silence_mean_ms
                              ? `${conversation.analysis.turns.silence_mean_ms.toFixed(0)}ms`
                              : "-"}
                          </CardTitle>
                          <CardDescription className="text-xs">
                            P95:{" "}
                            {conversation.analysis.turns.silence_p95_ms
                              ? `${conversation.analysis.turns.silence_p95_ms.toFixed(0)}ms`
                              : "-"}
                          </CardDescription>
                        </CardHeader>
                      </Card>
                    </div>
                  </div>
                </div>
              ) : (
                <p className="text-muted-foreground">No analysis data available</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
