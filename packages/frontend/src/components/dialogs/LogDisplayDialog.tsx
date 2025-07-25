import React, { useEffect, useState, useRef } from 'react'
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Environment } from '@/types/Environment'
import { connectToLogStream } from '@/api/environmentApi'

export interface LogDisplayDialogProps {
  environment: Environment
  open: boolean
  onOpenChange: (open: boolean) => void
}

export default function LogDisplayDialog({ environment, open, onOpenChange }: LogDisplayDialogProps) {
  const [logs, setLogs] = useState<string[]>([])
  const [autoScroll, setAutoScroll] = useState(true)
  const [showResumeButton, setShowResumeButton] = useState(false)
  const logContainerRef = useRef<HTMLDivElement>(null)
  const logEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return

    const appendLog = (log: string) => {
      setLogs((prevLogs) => [...prevLogs, log])
    }

    const disconnect = connectToLogStream(environment.id || "", appendLog)

    return () => {
      disconnect()
    }
  }, [open, environment.id])

  // Clear logs when the dialog is closed
  useEffect(() => {
    if (!open) {
      setLogs([])
    }
  }, [open])

  useEffect(() => {
    if (autoScroll) {
      logEndRef.current?.scrollIntoView({ behavior: 'auto' })
    }
  }, [logs, autoScroll])

  const handleScroll = () => {
    if (logContainerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = logContainerRef.current
      const atBottom = scrollHeight - scrollTop - clientHeight <= 10 // Threshold for "at bottom"
      setAutoScroll(atBottom)
      setShowResumeButton(!atBottom)
    }
  }

  const resumeAutoScroll = () => {
    setAutoScroll(true)
    setShowResumeButton(false)
    logEndRef.current?.scrollIntoView({ behavior: 'auto' })
  }

  const handleDialogOpenChange = (open: boolean) => {
    onOpenChange(open)
    if (!open) {
      setLogs([])
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleDialogOpenChange}>
      <DialogContent className="max-h-[80vh] min-w-[70vw] overflow-hidden">
        <DialogHeader>
          <DialogTitle>Environment Logs</DialogTitle>
        </DialogHeader>
        <div
          className="h-[60vh] border bg-black text-gray-300 p-4 overflow-y-auto"
          onScroll={handleScroll}
          ref={logContainerRef}
        >
          <div className="whitespace-pre-wrap">
            {logs.map((log, index) => (
              <div key={index}>{log}</div>
            ))}
            <div ref={logEndRef} />
          </div>
        </div>
        <DialogFooter className="flex justify-between items-center">
          {showResumeButton && (
            <Button onClick={resumeAutoScroll} variant="outline">
              Resume Auto-Scroll
            </Button>
          )}
          <Button onClick={() => onOpenChange(false)}>Close</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
