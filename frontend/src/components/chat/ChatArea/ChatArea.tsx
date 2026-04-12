'use client'

import Image from 'next/image'
import { useStore } from '@/store'
import ChatInput from './ChatInput'
import MessageArea from './MessageArea'

const ChatArea = () => {
  const userLocation = useStore((s) => s.userLocation)
  
  return (
    <main className="relative flex flex-grow flex-col bg-white w-full">
      {/* Header */}
      <div className="sticky top-0 z-10 border-b border-gray-200 bg-white backdrop-blur px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* EU Logo */}
            <div className="relative h-10 w-14">
              <Image
                src="/images/eu-logo.png"
                alt="European Union"
                fill
                className="object-contain"
                priority
              />
            </div>
            <div className="flex flex-col">
              <h1 className="text-xl font-bold text-gray-900">🔍 TED Tender Search</h1>
              <p className="text-sm text-gray-600">Search EU tenders & analyze procurement data</p>
            </div>
          </div>
          {userLocation && (
            <div className="flex items-center gap-2 text-xs text-gray-600 bg-gray-50 px-3 py-1.5 rounded-lg border border-gray-200">
              <span>📍</span>
              <span>{userLocation.city}, {userLocation.country}</span>
            </div>
          )}
        </div>
      </div>
      
      <MessageArea />
      
      <div className="sticky bottom-0 px-6 pb-4">
        <ChatInput />
      </div>
    </main>
  )
}

export default ChatArea
