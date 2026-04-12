'use client'
import { ChatArea } from '@/components/chat/ChatArea'
import Sidebar from '@/components/chat/Sidebar/Sidebar'
import { Suspense, useEffect } from 'react'
import { useStore } from '@/store'

function HomeContent() {
  const setMode = useStore((state) => state.setMode)
  
  // Auto-select TED agent on load
  useEffect(() => {
    setMode('agent')
  }, [setMode])

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar />
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


