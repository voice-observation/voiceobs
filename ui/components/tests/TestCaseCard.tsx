"use client";

import { Card } from "@/components/primitives/card";
import { Badge } from "@/components/primitives/badge";
import { Button } from "@/components/primitives/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/primitives/dropdown-menu";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { TestScenarioStatusBadge } from "@/components/tests/TestScenarioStatusBadge";
import {
  ChevronRight,
  Clock,
  MessageSquare,
  MoreHorizontal,
  Pencil,
  Target,
  Trash2,
  User,
} from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * Get color classes for persona match score badge.
 * Green: >= 50%, Yellow: >= 25%, Orange: < 25%
 */
function getMatchScoreColor(score: number): string {
  if (score >= 0.5) return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200";
  if (score >= 0.25) return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200";
  return "bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200";
}

export interface TestCaseCardProps {
  id: string;
  title: string;
  description: string;
  /** @deprecated Use scenario metadata instead. Kept for backward compatibility. */
  turns?: number;
  /** @deprecated Use scenario metadata instead. Kept for backward compatibility. */
  duration?: string;
  /** @deprecated Use tags prop instead. Kept for backward compatibility. */
  modality?: "text" | "audio" | "synthetic";
  status?: "passed" | "failed" | "pending" | "warning";
  scenarioStatus?: "ready" | "draft";
  intent?: string;
  personaMatchScore?: number;
  personaTraits?: string[];
  tags?: string[];
  onClick?: () => void;
  onEdit?: () => void;
  onDelete?: () => void;
}

export function TestCaseCard({
  title,
  description,
  turns,
  duration,
  modality,
  status,
  scenarioStatus,
  intent,
  personaMatchScore,
  personaTraits,
  tags,
  onClick,
  onEdit,
  onDelete,
}: TestCaseCardProps) {
  const hasActions = onEdit || onDelete;
  // Show legacy metadata section if any deprecated props are provided
  const showLegacyMetadata =
    turns !== undefined || duration !== undefined || modality !== undefined;

  return (
    <Card
      className={cn(
        "group cursor-pointer border border-border bg-card p-4 transition-colors hover:bg-secondary/30",
        onClick && "cursor-pointer"
      )}
      onClick={onClick}
    >
      {/* Header Section */}
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          {/* Title Row */}
          <div className="flex items-center gap-2">
            <span className="truncate font-medium">{title}</span>
            {status && (
              <StatusBadge status={status} size="sm" showIcon={false}>
                {status.charAt(0).toUpperCase() + status.slice(1)}
              </StatusBadge>
            )}
            {scenarioStatus && <TestScenarioStatusBadge status={scenarioStatus} />}
          </div>
          {/* Description */}
          <p className="mt-1 line-clamp-2 text-sm text-muted-foreground">{description}</p>

          {/* Intent Tag and Persona Match Score */}
          {(intent || personaMatchScore !== undefined) && (
            <div className="mt-2 flex flex-wrap items-center gap-2">
              {intent && (
                <Badge variant="secondary" className="text-xs">
                  <Target className="mr-1 h-3 w-3" />
                  {intent}
                </Badge>
              )}
              {personaMatchScore !== undefined && (
                <Badge className={cn("text-xs", getMatchScoreColor(personaMatchScore))}>
                  <User className="mr-1 h-3 w-3" />
                  {Math.round(personaMatchScore * 100)}% match
                </Badge>
              )}
            </div>
          )}
        </div>

        {/* Actions Menu and Chevron */}
        <div className="flex items-center gap-1">
          {hasActions && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0"
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                  }}
                >
                  <MoreHorizontal className="h-4 w-4" />
                  <span className="sr-only">Open menu</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                {onEdit && (
                  <DropdownMenuItem
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      onEdit();
                    }}
                  >
                    <Pencil className="mr-2 h-4 w-4" />
                    Edit
                  </DropdownMenuItem>
                )}
                {onDelete && (
                  <DropdownMenuItem
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      onDelete();
                    }}
                    className="text-destructive focus:text-destructive"
                  >
                    <Trash2 className="mr-2 h-4 w-4" />
                    Delete
                  </DropdownMenuItem>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          )}
          {/* Chevron indicator on hover */}
          <ChevronRight className="h-5 w-5 flex-shrink-0 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
        </div>
      </div>

      {/* Legacy Metadata Section (deprecated, for backward compatibility) */}
      {showLegacyMetadata && (
        <div className="mt-3 flex items-center gap-4 text-sm text-muted-foreground">
          {turns !== undefined && (
            <div className="flex items-center gap-1.5">
              <MessageSquare className="h-4 w-4" />
              <span>{turns} turns</span>
            </div>
          )}
          {duration !== undefined && (
            <div className="flex items-center gap-1.5">
              <Clock className="h-4 w-4" />
              <span>{duration}</span>
            </div>
          )}
          {modality !== undefined && (
            <Badge variant="outline" className="text-xs">
              {modality.charAt(0).toUpperCase() + modality.slice(1)}
            </Badge>
          )}
        </div>
      )}

      {/* Persona Traits Section */}
      {personaTraits && personaTraits.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {personaTraits.map((trait) => (
            <Badge key={trait} variant="outline" className="text-xs">
              {trait}
            </Badge>
          ))}
        </div>
      )}

      {/* Tags Section */}
      {tags && tags.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {tags.map((tag) => (
            <Badge key={tag} variant="secondary" className="text-xs">
              {tag}
            </Badge>
          ))}
        </div>
      )}
    </Card>
  );
}
