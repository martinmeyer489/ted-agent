'use client'

import useAIChatStreamHandler from '@/hooks/useAIStreamHandler'
import { useStore } from '@/store'

const exampleQueries = [
  'Find active software development tenders in Germany published this month',
  'Search for open IT consulting contract notices in France with CPV code 72000000',
  'Show me active construction project tenders in Spain and Portugal',
  'Find awarded contracts for cloud services in the Netherlands',
  'Search for open healthcare IT tenders in Scandinavia',
]

const ChatBlankState = () => {
  const { handleStreamResponse } = useAIChatStreamHandler()
  const isStreaming = useStore((s) => s.isStreaming)

  const handleClick = (query: string) => {
    if (isStreaming) return
    handleStreamResponse(query)
  }

  return (
    <div className="flex h-full items-center justify-center px-4">
      <div className="text-center max-w-2xl">
        <h2 className="text-2xl font-bold text-primary mb-3">
          Welcome to TED Bot! 🎯
        </h2>
        <p className="text-muted mb-6">
          Ask me anything about EU tender opportunities from the TED database
        </p>
        
        <div className="space-y-2 text-sm">
          <p className="text-muted/80 mb-3">Try these example searches:</p>
          {exampleQueries.map((query) => (
            <button
              key={query}
              onClick={() => handleClick(query)}
              disabled={isStreaming}
              className="w-full bg-accent/50 rounded-lg px-4 py-3 text-left text-gray-300 hover:bg-accent/80 hover:text-primary transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {query}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

export default ChatBlankState

