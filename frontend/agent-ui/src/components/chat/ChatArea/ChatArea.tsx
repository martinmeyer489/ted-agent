'use client'

import ChatInput from './ChatInput'
import MessageArea from './MessageArea'

const ChatArea = () => {
  return (
    <main className="relative flex flex-grow flex-col bg-background w-full">
      {/* Header */}
      <div className="sticky top-0 z-10 border-b border-border bg-background/95 backdrop-blur px-6 py-4">
        <h1 className="text-xl font-bold text-primary">🔍 TED Tender Search Agent</h1>
        <p className="text-sm text-muted">AI-powered EU tender discovery</p>
      </div>
      
      <MessageArea />
      
      <div className="sticky bottom-0 px-6 pb-4">
        <ChatInput />
      </div>
    </main>
  )
}

export default ChatArea
