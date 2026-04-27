"use client"

import { useState } from "react"
import {
  Server,
  Play,
  Square,
  AlertTriangle,
  Info,
  Globe,
  Cpu,
  Download,
  Upload,
  Clock,
  Users,
  Activity,
  Shield,
  AlertCircle,
  CheckCircle,
  XCircle,
  Lock,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Progress } from "@/components/ui/progress"
import { Table, TableBody, TableCell, TableRow } from "@/components/ui/table"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"

type ServerStatus = "running" | "stopped" | "starting" | "stopping" | "unknown"

type ServerStats = {
  hostname: string
  local_ip: string
  public_ip: string
  mac_address: string
  cpu_usage: number
  memory_usage: number
  network_download_kbps: number
  network_upload_kbps: number
  encryption: boolean
  os_name: string
  os_version: string
  os_architecture: string
  server_time: string
  server_start_time: string
}

type LogEntry = {
  timestamp: string
  event_type: string
  message: string
}

type ServerDashboardProps = {
  serverStatus: ServerStatus
  serverInfo: {
    is_running: boolean
    port: number
    host: string
  } | null
  serverStats: ServerStats | null
  logs: LogEntry[]
  onStartServer: () => void
  onStopServer: () => void
  connectedBots: number
  uptime: string
}

export function ServerDashboard({
  serverStatus,
  serverInfo,
  serverStats,
  logs,
  onStartServer,
  onStopServer,
  connectedBots,
  uptime,
}: ServerDashboardProps) {
  const [isStopDialogOpen, setIsStopDialogOpen] = useState(false)

  const getLogIcon = (eventType: string) => {
    switch (eventType.toLowerCase()) {
      case "error":
        return <XCircle className="h-4 w-4 text-red-500" />
      case "warning":
        return <AlertCircle className="h-4 w-4 text-yellow-500" />
      case "info":
        return <Info className="h-4 w-4 text-blue-500" />
      case "debug":
        return <CheckCircle className="h-4 w-4 text-gray-500" />
      default:
        return <Info className="h-4 w-4 text-gray-500" />
    }
  }

  const getLogBadgeVariant = (eventType: string) => {
    switch (eventType.toLowerCase()) {
      case "error":
        return "destructive"
      case "warning":
        return "secondary"
      case "info":
        return "default"
      case "debug":
        return "outline"
      default:
        return "outline"
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Command Center</h1>
          <p className="text-muted-foreground mt-1">C2 server monitoring and management</p>
        </div>

        {serverStatus === "running" ? (
          <Dialog open={isStopDialogOpen} onOpenChange={setIsStopDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="destructive">
                <Square className="h-4 w-4 mr-2" />
                Stop Server
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Confirm Server Shutdown</DialogTitle>
                <DialogDescription>
                  Are you sure you want to stop the C2 server? All active agent connections will be terminated.
                </DialogDescription>
              </DialogHeader>
              <DialogFooter className="mt-4">
                <Button variant="outline" onClick={() => setIsStopDialogOpen(false)}>
                  Cancel
                </Button>
                <Button
                  variant="destructive"
                  onClick={() => {
                    onStopServer()
                    setIsStopDialogOpen(false)
                  }}
                >
                  Stop Server
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        ) : (
          <Button onClick={onStartServer} disabled={serverStatus === "starting"}>
            <Play className="h-4 w-4 mr-2" />
            {serverStatus === "starting" ? "Starting..." : "Start Server"}
          </Button>
        )}
      </div>

      {/* Server Status Overview */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className={serverStatus === "running" ? "border-green-500/30" : "border-red-500/30"}>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Server Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <Badge variant={serverStatus === "running" ? "default" : "destructive"}>
                {serverStatus === "running" ? "Online" : "Offline"}
              </Badge>
              <Server className={`h-8 w-8 ${serverStatus === "running" ? "text-primary" : "text-destructive"}`} />
            </div>
            {serverStatus === "running" && serverInfo && (
              <p className="text-xs text-muted-foreground mt-2">
                {serverInfo.host}:{serverInfo.port}
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Connected Agents</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="text-2xl font-bold">{connectedBots}</div>
              <Users className="h-8 w-8 text-primary" />
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              {serverStatus === "running" ? "Active connections" : "Server offline"}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Server Uptime</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="text-2xl font-bold">{uptime}</div>
              <Clock className="h-8 w-8 text-primary" />
            </div>
            <p className="text-xs text-muted-foreground mt-2">{serverStatus === "running" ? "Running" : "Offline"}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Network Traffic</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="text-sm space-y-1">
                <div className="flex items-center">
                  <Download className="h-4 w-4 mr-1 text-green-500" />
                  {serverStats?.network_download_kbps || 0} KB/s
                </div>
                <div className="flex items-center">
                  <Upload className="h-4 w-4 mr-1 text-blue-500" />
                  {serverStats?.network_upload_kbps || 0} KB/s
                </div>
              </div>
              <Globe className="h-8 w-8 text-primary" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Resource Usage and Server Information */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Cpu className="h-5 w-5 mr-2" />
              Resource Usage
            </CardTitle>
            <CardDescription>Server resource utilization</CardDescription>
          </CardHeader>
          <CardContent>
            {serverStatus === "running" && serverStats ? (
              <div className="space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">CPU Usage</span>
                    <span className="text-sm font-medium">{serverStats.cpu_usage.toFixed(1)}%</span>
                  </div>
                  <Progress value={serverStats.cpu_usage} className="h-2" />
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Memory Usage</span>
                    <span className="text-sm font-medium">{serverStats.memory_usage.toFixed(1)}%</span>
                  </div>
                  <Progress value={serverStats.memory_usage} className="h-2" />
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Network Download</span>
                    <span className="text-sm font-medium">{serverStats.network_download_kbps} KB/s</span>
                  </div>
                  <Progress value={Math.min(serverStats.network_download_kbps / 10, 100)} className="h-2" />
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Network Upload</span>
                    <span className="text-sm font-medium">{serverStats.network_upload_kbps} KB/s</span>
                  </div>
                  <Progress value={Math.min(serverStats.network_upload_kbps / 10, 100)} className="h-2" />
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center h-32">
                <p className="text-muted-foreground">Server offline</p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Activity className="h-5 w-5 mr-2" />
              Server Information
            </CardTitle>
            <CardDescription>System configuration details</CardDescription>
          </CardHeader>
          <CardContent>
            {serverStatus === "running" && serverStats ? (
              <div className="space-y-4">
                <Alert>
                  <Info className="h-4 w-4" />
                  <AlertTitle>Server Details</AlertTitle>
                  <AlertDescription>
                    <div className="grid grid-cols-2 gap-2 mt-2 text-sm">
                      <div className="font-medium">Hostname:</div>
                      <div>{serverStats.hostname}</div>
                      <div className="font-medium">Local IP:</div>
                      <div>{serverStats.local_ip}</div>
                      <div className="font-medium">Public IP:</div>
                      <div>{serverStats.public_ip}</div>
                      <div className="font-medium">Port:</div>
                      <div>{serverInfo?.port}</div>
                    </div>
                  </AlertDescription>
                </Alert>

                <Table>
                  <TableBody>
                    <TableRow>
                      <TableCell className="py-2 font-medium">Operating System</TableCell>
                      <TableCell className="py-2">
                        {serverStats.os_name} {serverStats.os_version}
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell className="py-2 font-medium">Architecture</TableCell>
                      <TableCell className="py-2">{serverStats.os_architecture}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell className="py-2 font-medium">MAC Address</TableCell>
                      <TableCell className="py-2">{serverStats.mac_address}</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell className="py-2 font-medium">Server Time</TableCell>
                      <TableCell className="py-2">{new Date(serverStats.server_time).toLocaleString()}</TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </div>
            ) : (
              <Alert variant="destructive">
                <AlertTriangle className="h-4 w-4" />
                <AlertTitle>Server Offline</AlertTitle>
                <AlertDescription>Start the server to view information.</AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      </div>

      {/* System Logs */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Shield className="h-5 w-5 mr-2" />
            System Logs
          </CardTitle>
          <CardDescription>Recent system events and security logs</CardDescription>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[400px]">
            {serverStatus === "running" && logs.length > 0 ? (
              <div className="space-y-2">
                {logs.map((log, index) => (
                  <div key={index} className="flex items-start space-x-3 p-3 rounded-lg bg-muted/30 hover:bg-muted/50">
                    <div className="flex-shrink-0 mt-0.5">{getLogIcon(log.event_type)}</div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-1">
                        <Badge variant={getLogBadgeVariant(log.event_type)} className="text-xs">
                          {log.event_type.toUpperCase()}
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          {new Date(log.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                      <p className="text-sm text-foreground">{log.message}</p>
                      <p className="text-xs text-muted-foreground">{new Date(log.timestamp).toLocaleDateString()}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : serverStatus === "running" ? (
              <div className="flex items-center justify-center h-32">
                <p className="text-muted-foreground">No logs available</p>
              </div>
            ) : (
              <div className="flex items-center justify-center h-32">
                <p className="text-muted-foreground">Server offline</p>
              </div>
            )}
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  )
}
