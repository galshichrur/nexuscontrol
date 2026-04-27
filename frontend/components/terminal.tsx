"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { TerminalIcon, Trash2 } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { useToast } from "@/hooks/use-toast"

type TerminalEntry = {
  id: string
  type: "command" | "output" | "error"
  content: string
  timestamp: Date
  cwd?: string
}

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

type TerminalProps = {
  agent: AgentData
  isOnline: boolean
  onSendCommand: (agentId: string, command: string) => Promise<AgentResponse>
  onReconnect: () => void
}

export function Terminal({ agent, isOnline, onSendCommand, onReconnect }: TerminalProps) {
  const [command, setCommand] = useState("")
  const [history, setHistory] = useState<TerminalEntry[]>([])
  const [commandHistory, setCommandHistory] = useState<string[]>([])
  const [historyIndex, setHistoryIndex] = useState(-1)
  const [isExecuting, setIsExecuting] = useState(false)
  const [currentCwd, setCurrentCwd] = useState(agent.cwd)
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const { toast } = useToast()

  // Update current working directory when agent changes
  useEffect(() => {
    setCurrentCwd(agent.cwd)
  }, [agent.cwd])

  // Auto-scroll to bottom when new entries are added
  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollContainer = scrollAreaRef.current.querySelector("[data-radix-scroll-area-viewport]")
      if (scrollContainer) {
        scrollContainer.scrollTop = scrollContainer.scrollHeight
      }
    }
  }, [history])

  // Focus input when component mounts or comes online
  useEffect(() => {
    if (inputRef.current && isOnline) {
      inputRef.current.focus()
    }
  }, [isOnline])

  const executeCommand = async () => {
    if (!command.trim() || isExecuting || !isOnline) return

    // Handle clear command locally
    if (command.trim().toLowerCase() === "clear") {
      setHistory([])
      setCommand("")
      return
    }

    const newCommand: TerminalEntry = {
      id: Date.now().toString(),
      type: "command",
      content: command,
      timestamp: new Date(),
      cwd: currentCwd,
    }

    setHistory((prev) => [...prev, newCommand])
    setCommandHistory((prev) => [command, ...prev.slice(0, 49)])
    setHistoryIndex(-1)

    const currentCommand = command
    setCommand("")
    setIsExecuting(true)

    try {
      const response = await onSendCommand(agent.agent_id, currentCommand)

      if (response.status) {
        const output: TerminalEntry = {
          id: (Date.now() + 1).toString(),
          type: "output",
          content: response.command_response || "",
          timestamp: new Date(),
          cwd: response.cwd || currentCwd,
        }

        setHistory((prev) => [...prev, output])

        if (response.cwd) {
          setCurrentCwd(response.cwd)
        }
      } else {
        const errorOutput: TerminalEntry = {
          id: (Date.now() + 1).toString(),
          type: "error",
          content: response.command_response || "Command failed - agent may be offline",
          timestamp: new Date(),
          cwd: currentCwd,
        }

        setHistory((prev) => [...prev, errorOutput])
      }
    } catch (error) {
      const errorOutput: TerminalEntry = {
        id: (Date.now() + 1).toString(),
        type: "error",
        content: `Error: ${error instanceof Error ? error.message : "Connection failed"}`,
        timestamp: new Date(),
        cwd: currentCwd,
      }

      setHistory((prev) => [...prev, errorOutput])
    } finally {
      setIsExecuting(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      executeCommand()
    } else if (e.key === "ArrowUp") {
      e.preventDefault()
      if (historyIndex < commandHistory.length - 1) {
        const newIndex = historyIndex + 1
        setHistoryIndex(newIndex)
        setCommand(commandHistory[newIndex])
      }
    } else if (e.key === "ArrowDown") {
      e.preventDefault()
      if (historyIndex > 0) {
        const newIndex = historyIndex - 1
        setHistoryIndex(newIndex)
        setCommand(commandHistory[newIndex])
      } else if (historyIndex === 0) {
        setHistoryIndex(-1)
        setCommand("")
      }
    }
  }

  const clearTerminal = () => {
    setHistory([])
  }

  const getPrompt = () => {
    return `${agent.username}@${agent.hostname}:${currentCwd}$`
  }

  const getEntryColor = (type: string) => {
    switch (type) {
      case "command":
        return "text-green-400"
      case "output":
        return "text-gray-100"
      case "error":
        return "text-red-400"
      default:
        return "text-gray-300"
    }
  }

  return (
    <Card className="h-[600px] flex flex-col bg-gray-900 border-gray-700">
      <CardHeader className="pb-2 bg-gray-800 border-b border-gray-700">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center text-gray-100 text-sm font-normal">
            <TerminalIcon className="h-4 w-4 mr-2" />
            {agent.username}@{agent.hostname}
          </CardTitle>
          <Button
            variant="ghost"
            size="sm"
            onClick={clearTerminal}
            className="h-6 w-6 p-0 text-gray-400 hover:text-gray-200 hover:bg-gray-700"
          >
            <Trash2 className="h-3 w-3" />
          </Button>
        </div>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col p-0 bg-gray-900">
        <ScrollArea className="flex-1 p-4" ref={scrollAreaRef}>
          <div className="font-mono text-sm space-y-1">
            {history.map((entry) => (
              <div key={entry.id}>
                {entry.type === "command" && (
                  <div className="flex items-start">
                    <span className="text-green-400 select-none font-bold">{getPrompt()}</span>
                    <span className="text-white ml-1">{entry.content}</span>
                  </div>
                )}
                {(entry.type === "output" || entry.type === "error") && (
                  <div className={`whitespace-pre-wrap ${getEntryColor(entry.type)} leading-relaxed`}>
                    {entry.content}
                  </div>
                )}
              </div>
            ))}
            {isExecuting && (
              <div className="flex items-center space-x-2">
                <div className="animate-spin h-3 w-3 border border-green-400 border-t-transparent rounded-full"></div>
              </div>
            )}
          </div>
        </ScrollArea>

        <div className="border-t border-gray-700 bg-gray-800 p-4">
          <div className="flex items-center font-mono text-sm">
            <span className="text-green-400 select-none font-bold">{getPrompt()}</span>
            <Input
              ref={inputRef}
              value={command}
              onChange={(e) => setCommand(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder=""
              disabled={isExecuting || !isOnline}
              className="bg-transparent border-none text-white ml-1 p-0 h-auto focus-visible:ring-0 focus-visible:ring-offset-0 placeholder-gray-500"
            />
          </div>
          {!isOnline && <div className="mt-2 text-xs text-red-400">Connection lost - commands unavailable</div>}
        </div>
      </CardContent>
    </Card>
  )
}
