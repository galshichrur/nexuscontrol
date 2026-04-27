import { Server, Clock } from "lucide-react"
import { Badge } from "@/components/ui/badge"

type ServerStatus = "running" | "stopped" | "starting" | "stopping" | "unknown"

type ServerStatusIndicatorProps = {
  status: ServerStatus
  info: {
    is_running: boolean
    port: number
    host: string
  } | null
}

export function ServerStatusIndicator({ status, info }: ServerStatusIndicatorProps) {
  if (status !== "running" || !info) {
    return null
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Server className="h-4 w-4 text-primary" />
          <span className="text-sm font-medium">C2 Server</span>
        </div>
        <Badge
          variant={status === "running" ? "default" : status === "stopped" ? "destructive" : "secondary"}
          className="px-2 py-0"
        >
          {status === "running" && "Running"}
          {status === "stopped" && "Stopped"}
          {status === "starting" && "Starting..."}
          {status === "stopping" && "Stopping..."}
          {status === "unknown" && "Unknown"}
        </Badge>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className="text-xs text-muted-foreground">Host:</span>
        </div>
        <span className="text-xs font-medium">
          {info.host}:{info.port}
        </span>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Clock className="h-3 w-3 text-muted-foreground" />
          <span className="text-xs text-muted-foreground">Status:</span>
        </div>
        <span className="text-xs font-medium">{info.is_running ? "Running" : "Stopped"}</span>
      </div>
    </div>
  )
}
