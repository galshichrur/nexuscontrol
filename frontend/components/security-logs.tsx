"use client"

import { useState, useEffect } from "react"
import { Shield, AlertTriangle, Info, CheckCircle } from "lucide-react"

const API_BASE_URL = ""

type LogEntry = {
  timestamp: string
  type: "security" | "server" | "agent"
  event_type: string
  message: string
  agent_id?: string
  details?: any
}

export function SecurityLogs() {
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchLogs()
    const interval = setInterval(fetchLogs, 5000) // Refresh every 5 seconds
    return () => clearInterval(interval)
  }, [])

  const fetchLogs = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/logs?limit=20`)
      if (response.ok) {
        const data = await response.json()
        setLogs(data)
      }
    } catch (error) {
      console.error("Failed to fetch logs:", error)
    } finally {
      setLoading(false)
    }
  }

  const getLogIcon = (type: string, eventType: string) => {
    if (type === "security") {
      return <Shield className="h-3 w-3 text-red-500" />
    } else if (type === "server") {
      if (eventType.includes("start")) {
        return <CheckCircle className="h-3 w-3 text-green-500" />
      } else if (eventType.includes("stop")) {
        return <AlertTriangle className="h-3 w-3 text-yellow-500" />
      }
      return <Info className="h-3 w-3 text-blue-500" />
    } else if (type === "agent") {
      return <Info className="h-3 w-3 text-purple-500" />
    }
    return <Info className="h-3 w-3 text-gray-500" />
  }

  const getLogColor = (type: string, eventType: string) => {
    if (type === "security") {
      return "bg-red-500"
    } else if (type === "server") {
      if (eventType.includes("start")) {
        return "bg-green-500"
      } else if (eventType.includes("stop")) {
        return "bg-yellow-500"
      }
      return "bg-blue-500"
    } else if (type === "agent") {
      return "bg-purple-500"
    }
    return "bg-gray-500"
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
      </div>
    )
  }

  if (logs.length === 0) {
    return (
      <div className="flex items-center justify-center py-8">
        <p className="text-muted-foreground">No logs available</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {logs.slice(0, 10).map((log, index) => (
        <div key={index} className="flex items-start space-x-3">
          <div className={`h-2 w-2 mt-1.5 rounded-full ${getLogColor(log.type, log.event_type)}`} />
          <div className="flex-1 min-w-0">
            <div className="flex items-center space-x-2">
              {getLogIcon(log.type, log.event_type)}
              <p className="text-sm font-medium truncate">{log.message}</p>
            </div>
            <p className="text-xs text-muted-foreground">
              {new Date(log.timestamp).toLocaleString()}
              {log.agent_id && ` • Agent: ${log.agent_id}`}
            </p>
          </div>
        </div>
      ))}
    </div>
  )
} 