'use client'

import Image from 'next/image'
import { useStore } from '@/store'

export default function Header() {
  const userLocation = useStore((s) => s.userLocation)
  
  return (
    <header className="w-full bg-white border-b border-gray-200 shadow-sm">
      <div className="flex items-center justify-between px-6 py-4">
        <div className="flex items-center gap-4">
          {/* EU Logo */}
          <div className="relative h-12 w-16">
            <Image
              src="/images/eu-logo.png"
              alt="European Union"
              fill
              className="object-contain"
              priority
            />
          </div>
          <div className="border-l border-gray-300 h-10" />
          <div className="flex flex-col">
            <h1 className="text-xl font-semibold text-gray-900">TED Search Assistant</h1>
            <p className="text-xs text-gray-500">Tenders Electronic Daily</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          {userLocation && (
            <div className="flex items-center gap-2 text-xs text-gray-600 bg-gray-50 px-3 py-1.5 rounded-lg border border-gray-200">
              <span>📍</span>
              <span>{userLocation.city}, {userLocation.country}</span>
            </div>
          )}
          <span className="text-xs text-gray-400 uppercase tracking-wide">Powered by AI</span>
        </div>
      </div>
    </header>
  )
}
