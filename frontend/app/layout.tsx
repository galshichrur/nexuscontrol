import type React from "react"
import "@/app/globals.css"
import { Toaster } from "@/components/ui/toaster"

export const metadata = {
  title: "NexusControl",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        {children}
        <Toaster />
      </body>
    </html>
  )
}
