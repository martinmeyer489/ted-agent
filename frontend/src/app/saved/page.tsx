'use client'

import { useEffect, useState } from 'react'
import { useStore } from '@/store'
import { useRouter } from 'next/navigation'
import { TableRow } from '@/types/workspace'
import * as XLSX from 'xlsx'
import { toast } from 'sonner'

type Tab = 'tenders' | 'buyers'

export default function SavedPage() {
  const router = useRouter()
  const [activeTab, setActiveTab] = useState<Tab>('tenders')
  const [mounted, setMounted] = useState(false)
  
  const savedTenders = useStore((s) => s.savedTenders)
  const savedBuyers = useStore((s) => s.savedBuyers)
  const removeSavedTender = useStore((s) => s.removeSavedTender)
  const removeSavedBuyer = useStore((s) => s.removeSavedBuyer)
  const clearSavedTenders = useStore((s) => s.clearSavedTenders)
  const clearSavedBuyers = useStore((s) => s.clearSavedBuyers)

  useEffect(() => {
    setMounted(true)
  }, [])

  const handleExportTenders = () => {
    if (savedTenders.length === 0) {
      toast.error('No saved tenders to export')
      return
    }

    // Get all unique keys from all rows
    const allKeys = Array.from(
      new Set(savedTenders.flatMap((row) => Object.keys(row)))
    )

    const headerRow = allKeys
    const dataRows = savedTenders.map((row) =>
      allKeys.map((key) => row[key] ?? '')
    )

    const ws = XLSX.utils.aoa_to_sheet([headerRow, ...dataRows])
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, 'Saved Tenders')
    XLSX.writeFile(wb, `saved-tenders-${new Date().toISOString().split('T')[0]}.xlsx`)
    toast.success('Exported saved tenders')
  }

  const handleExportBuyers = () => {
    if (savedBuyers.length === 0) {
      toast.error('No saved buyers to export')
      return
    }

    const allKeys = Array.from(
      new Set(savedBuyers.flatMap((row) => Object.keys(row)))
    )

    const headerRow = allKeys
    const dataRows = savedBuyers.map((row) =>
      allKeys.map((key) => row[key] ?? '')
    )

    const ws = XLSX.utils.aoa_to_sheet([headerRow, ...dataRows])
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, 'Saved Buyers')
    XLSX.writeFile(wb, `saved-buyers-${new Date().toISOString().split('T')[0]}.xlsx`)
    toast.success('Exported saved buyers')
  }

  const handleClearAll = () => {
    if (activeTab === 'tenders') {
      if (confirm(`Delete all ${savedTenders.length} saved tenders?`)) {
        clearSavedTenders()
        toast.success('Cleared all saved tenders')
      }
    } else {
      if (confirm(`Delete all ${savedBuyers.length} saved buyers?`)) {
        clearSavedBuyers()
        toast.success('Cleared all saved buyers')
      }
    }
  }

  const handleRemoveItem = (index: number) => {
    if (activeTab === 'tenders') {
      removeSavedTender(index)
      toast.success('Removed tender from saved')
    } else {
      removeSavedBuyer(index)
      toast.success('Removed buyer from saved')
    }
  }

  const renderRow = (row: TableRow, index: number) => {
    const isUrl = (v: unknown): v is string =>
      typeof v === 'string' && (v.startsWith('http://') || v.startsWith('https://'))

    return (
      <div
        key={index}
        className="border border-gray-200 rounded-lg p-4 hover:border-primary/30 hover:bg-gray-50 transition-all"
      >
        <div className="flex items-start justify-between gap-4 mb-3">
          <h3 className="font-semibold text-gray-900 flex-1">
            {row.title || row.buyer || row.noticeId || 'Untitled'}
          </h3>
          <button
            onClick={() => handleRemoveItem(index)}
            className="text-gray-400 hover:text-red-500 transition-colors flex-shrink-0"
            title="Remove from saved"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
          {Object.entries(row).map(([key, value]) => {
            if (key === 'title') return null // Already shown as heading
            
            return (
              <div key={key} className="flex flex-col">
                <span className="text-xs text-gray-500 uppercase font-medium">{key}</span>
                {isUrl(value) ? (
                  <a
                    href={value}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline truncate"
                  >
                    {value}
                  </a>
                ) : (
                  <span className="text-gray-900 break-words">{String(value ?? 'N/A')}</span>
                )}
              </div>
            )
          })}
        </div>
      </div>
    )
  }

  if (!mounted) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-500">Loading...</div>
      </div>
    )
  }

  const currentItems = activeTab === 'tenders' ? savedTenders : savedBuyers
  const currentCount = currentItems.length

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-4">
              <button
                onClick={() => router.push('/')}
                className="text-gray-600 hover:text-gray-900 transition-colors"
                title="Back to chat"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
              </button>
              <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
                <span className="text-yellow-500">★</span>
                Saved Items
              </h1>
            </div>
            
            <div className="flex items-center gap-2">
              {currentCount > 0 && (
                <>
                  <button
                    onClick={activeTab === 'tenders' ? handleExportTenders : handleExportBuyers}
                    className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    ⬇ Export .xlsx
                  </button>
                  <button
                    onClick={handleClearAll}
                    className="px-4 py-2 text-sm font-medium text-red-600 bg-white border border-red-300 rounded-lg hover:bg-red-50 transition-colors"
                  >
                    Clear All
                  </button>
                </>
              )}
            </div>
          </div>

          {/* Tabs */}
          <div className="flex gap-2">
            <button
              onClick={() => setActiveTab('tenders')}
              className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                activeTab === 'tenders'
                  ? 'bg-primary text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Tenders ({savedTenders.length})
            </button>
            <button
              onClick={() => setActiveTab('buyers')}
              className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                activeTab === 'buyers'
                  ? 'bg-primary text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Buyers ({savedBuyers.length})
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {currentCount === 0 ? (
          <div className="bg-white rounded-lg border border-gray-200 p-12 text-center">
            <div className="text-6xl mb-4 opacity-20">
              {activeTab === 'tenders' ? '📋' : '🏢'}
            </div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              No saved {activeTab} yet
            </h2>
            <p className="text-gray-600 mb-6">
              {activeTab === 'tenders'
                ? 'Save tenders by clicking the star (☆) button in search results'
                : 'Save buyers by clicking the star (☆) button in buyer profile results'}
            </p>
            <button
              onClick={() => router.push('/')}
              className="px-6 py-3 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
            >
              Start Searching
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="text-sm text-gray-600 mb-4">
              Showing {currentCount} saved {activeTab}
            </div>
            {currentItems.map((item, index) => renderRow(item, index))}
          </div>
        )}
      </div>

      {/* Info Footer */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm">
          <div className="flex items-start gap-3">
            <span className="text-blue-600 text-xl">ℹ️</span>
            <div className="flex-1">
              <p className="font-medium text-blue-900 mb-1">Local Browser Storage</p>
              <p className="text-blue-700">
                Your saved items are stored locally in your browser. They will persist across sessions,
                but won&apos;t sync to other devices or browsers. To backup your data, use the Export button.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
