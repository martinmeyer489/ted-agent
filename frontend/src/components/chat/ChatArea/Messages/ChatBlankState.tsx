'use client'

import useAIChatStreamHandler from '@/hooks/useAIStreamHandler'
import { useStore } from '@/store'
import { useGeolocation } from '@/hooks/useGeolocation'
import { useEffect, useState } from 'react'

const getExampleQueries = (location: { country: string; city: string } | null, category?: string) => {
  // Use provided category or default to renewable energy for SSR consistency
  const selectedCategory = category || 'renewable energy'
  
  if (location) {
    const { country, city } = location
    return [
      `🔍 Find software development tenders in ${country}`,
      `🏢 Analyze buyer profile for ${city}`,
      `💰 Show me biggest projects in ${city} by contract value in ${selectedCategory}`,
      `🎯 Search for IT services tenders in ${city} with CPV code 72000000`,
      `📊 What does the City of ${city} typically procure?`,
      `🏗️ Show me construction tenders in ${country}`,
      `🤪 Show me the most useless public tender near ${city}`,
      `💼 Find recent procurement activity in ${city}`,
    ]
  }
  
  // Default queries without location
  return [
    '🔍 Find software development tenders in Germany',
    '🏢 Analyze buyer profile for Munich',
    `💰 Show me biggest projects in Berlin by contract value in ${selectedCategory}`,
    '🎯 Search for IT services tenders with CPV code 72000000',
    '📊 What does the City of Berlin typically procure?',
    '🏗️ Show me construction tenders in Spain and Portugal',
    '🤪 Show me the most useless public tender near Munich',
    '💼 Analyze Stadtwerke München procurement activity',
  ]
}

const ChatBlankState = () => {
  const { handleStreamResponse } = useAIChatStreamHandler()
  const isStreaming = useStore((s) => s.isStreaming)
  const userLocation = useStore((s) => s.userLocation)
  const setUserLocation = useStore((s) => s.setUserLocation)
  
  const { location, permission, isLoading, error, requestLocation, resetPermission } = useGeolocation()
  const [showLocationPrompt, setShowLocationPrompt] = useState(true)
  const [randomCategory, setRandomCategory] = useState<string>('renewable energy')
  const [exampleQueries, setExampleQueries] = useState(() => getExampleQueries(userLocation, 'renewable energy'))

  // Randomize category on client mount to avoid hydration mismatch
  useEffect(() => {
    const categories = [
      'renewable energy',
      'defense',
      'AI and digital services',
      'public transport',
      'healthcare technology',
      'cybersecurity'
    ]
    const selected = categories[Math.floor(Math.random() * categories.length)]
    setRandomCategory(selected)
    setExampleQueries(getExampleQueries(userLocation, selected))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []) // Only run once on mount

  // Update queries when geolocation location changes
  useEffect(() => {
    if (location && location.country && location.city) {
      const newLocation = { country: location.country, city: location.city }
      setUserLocation(newLocation)
      setExampleQueries(getExampleQueries(newLocation, randomCategory))
      setShowLocationPrompt(false)
    }
  }, [location, setUserLocation, randomCategory])

  // Update queries when stored user location is available on mount
  useEffect(() => {
    if (userLocation) {
      setExampleQueries(getExampleQueries(userLocation, randomCategory))
      setShowLocationPrompt(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [randomCategory])

  const handleLocationRequest = async () => {
    await requestLocation()
  }

  const handleLocationDeny = () => {
    setShowLocationPrompt(false)
  }

  const handleLocationReset = () => {
    setUserLocation(null)
    setExampleQueries(getExampleQueries(null, randomCategory))
    setShowLocationPrompt(true)
    resetPermission()
  }

  const handleClick = (query: string) => {
    if (isStreaming) return
    handleStreamResponse(query)
  }

  return (
    <div className="flex h-full items-center justify-center px-4">
      <div className="text-center max-w-2xl">

        {/* AI Disclaimer */}
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mb-6">
          <div className="flex items-start gap-2">
            <span className="text-lg">⚠️</span>
            <p className="text-sm text-amber-800 text-left">
              <strong>AI-Generated Content:</strong> This assistant uses AI to provide answers. 
              Responses may contain inaccuracies or errors. Please verify important information independently.
            </p>
          </div>
        </div>

        {/* Location Permission Prompt */}
        {showLocationPrompt && permission === 'prompt' && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <div className="flex items-start gap-3">
              <span className="text-2xl">📍</span>
              <div className="flex-1 text-left">
                <h3 className="font-semibold text-gray-900 mb-1">
                  Personalize your search
                </h3>
                <p className="text-sm text-gray-600 mb-3">
                  Allow location access to see tenders relevant to your area
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={handleLocationRequest}
                    disabled={isLoading}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors disabled:opacity-50"
                  >
                    {isLoading ? 'Getting location...' : 'Allow Location'}
                  </button>
                  <button
                    onClick={handleLocationDeny}
                    className="bg-gray-100 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors"
                  >
                    No thanks
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Location Status Messages */}
        {permission === 'denied' && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-6 text-sm text-yellow-800">
            Location access denied. Using default example queries.
          </div>
        )}

        {permission === 'granted' && location && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-3 mb-6 flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm text-green-800">
              <span>📍</span>
              <span>Personalized for {location.city}, {location.country}</span>
            </div>
            <button
              onClick={handleLocationReset}
              className="text-xs text-green-700 hover:text-green-900 underline"
            >
              Reset
            </button>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-6 text-sm text-red-800">
            {error}
          </div>
        )}
        
        <div className="space-y-2 text-sm">
          <p className="text-gray-600 mb-3">Try these example queries:</p>
          {exampleQueries.map((query) => (
            <button
              key={query}
              onClick={() => handleClick(query)}
              disabled={isStreaming}
              className="w-full bg-gray-50 rounded-lg px-4 py-3 text-left text-gray-700 hover:bg-gray-100 hover:text-gray-900 transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed border border-gray-200"
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

