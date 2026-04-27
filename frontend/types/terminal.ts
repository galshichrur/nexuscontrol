export type TerminalEntry = {
  id: string
  type: "command" | "output" | "error"
  content: string
  timestamp: Date
}
