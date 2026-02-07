import { Badge } from "@/components/primitives/badge";
import { Loader2, CheckCircle2, XCircle, Clock, AlertCircle } from "lucide-react";
import type { ConnectionStatus } from "@/lib/types";

interface AgentStatusBadgeProps {
  connectionStatus: ConnectionStatus;
  isActive: boolean;
  showActiveStatus?: boolean;
}

const statusConfig: Record<
  ConnectionStatus,
  {
    label: string;
    variant: "default" | "secondary" | "destructive" | "outline";
    icon: React.ReactNode;
  }
> = {
  verified: {
    label: "Verified",
    variant: "default",
    icon: <CheckCircle2 className="h-3 w-3" />,
  },
  pending: {
    label: "Pending",
    variant: "secondary",
    icon: <Clock className="h-3 w-3" />,
  },
  saved: {
    label: "Saved",
    variant: "secondary",
    icon: <Clock className="h-3 w-3" />,
  },
  connecting: {
    label: "Verifying...",
    variant: "outline",
    icon: <Loader2 className="h-3 w-3 animate-spin" />,
  },
  failed: {
    label: "Failed",
    variant: "destructive",
    icon: <XCircle className="h-3 w-3" />,
  },
};

export function AgentStatusBadge({
  connectionStatus,
  isActive,
  showActiveStatus = true,
}: AgentStatusBadgeProps) {
  const config = statusConfig[connectionStatus] || statusConfig.pending;

  return (
    <div className="flex items-center gap-2">
      <Badge variant={config.variant} className="flex items-center gap-1">
        {config.icon}
        {config.label}
      </Badge>
      {showActiveStatus && (
        <Badge variant={isActive ? "outline" : "secondary"} className="text-xs">
          {isActive ? "Active" : "Inactive"}
        </Badge>
      )}
    </div>
  );
}
