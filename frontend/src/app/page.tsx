'use client'
import { ChatArea } from '@/components/chat/ChatArea'
import WorkspacePanel from '@/components/workspace/WorkspacePanel'
import ResizeDivider from '@/components/workspace/ResizeDivider'
import { Suspense, useEffect } from 'react'
import { useStore } from '@/store'
import { useQueryState } from 'nuqs'

function HomeContent() {
  const setMode = useStore((state) => state.setMode)
  const [, setAgentId] = useQueryState('agent')
  
  // Auto-select TED agent on load
  useEffect(() => {
    setMode('agent')
    setAgentId('ted-agent')
  }, [setMode, setAgentId])

  return (
    <div className="flex h-screen bg-background/80">
      <WorkspacePanel />
      <ResizeDivider />
      <ChatArea />
    </div>
  )
}

export default function Home() {
  return (
    <Suspense>
      <HomeContent />
    </Suspense>
  )
}


