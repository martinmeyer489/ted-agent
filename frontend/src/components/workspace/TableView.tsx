'use client'

import { useState, useMemo, useCallback } from 'react'
import { WorkspaceTable, TableRow } from '@/types/workspace'
import { useStore } from '@/store'

type SortDir = 'asc' | 'desc' | null

export default function TableView({ table }: { table: WorkspaceTable }) {
  const [sortKey, setSortKey] = useState<string | null>(null)
  const [sortDir, setSortDir] = useState<SortDir>(null)
  const savedTenders = useStore((s) => s.savedTenders)
  const toggleSavedTender = useStore((s) => s.toggleSavedTender)

  const isSaved = useCallback(
    (row: TableRow) =>
      savedTenders.some((t) => JSON.stringify(t) === JSON.stringify(row)),
    [savedTenders]
  )

  const handleSort = (key: string) => {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : d === 'desc' ? null : 'asc'))
      if (sortDir === 'desc') setSortKey(null)
    } else {
      setSortKey(key)
      setSortDir('asc')
    }
  }

  const sortedRows = useMemo(() => {
    if (!sortKey || !sortDir) return table.rows
    return [...table.rows].sort((a, b) => {
      const av = a[sortKey] ?? ''
      const bv = b[sortKey] ?? ''
      if (typeof av === 'number' && typeof bv === 'number') {
        return sortDir === 'asc' ? av - bv : bv - av
      }
      const cmp = String(av).localeCompare(String(bv))
      return sortDir === 'asc' ? cmp : -cmp
    })
  }, [table.rows, sortKey, sortDir])

  const sortIndicator = (key: string) => {
    if (sortKey !== key) return ''
    return sortDir === 'asc' ? ' ↑' : sortDir === 'desc' ? ' ↓' : ''
  }

  const isUrl = (v: unknown): v is string =>
    typeof v === 'string' && (v.startsWith('http://') || v.startsWith('https://'))

  return (
    <div className="overflow-auto flex-1 bg-[#0a0a0c]">
      <table className="w-full text-sm border-collapse">
        <thead className="sticky top-0 z-10">
          <tr>
            <th className="bg-[#1a1a22] px-2 py-2.5 text-center text-xs font-semibold text-blue-300/80 uppercase tracking-wider border-b border-gray-600/50 w-10">
              ★
            </th>
            {table.columns.map((col) => (
              <th
                key={col.key}
                onClick={() => handleSort(col.key)}
                className="bg-[#1a1a22] px-3 py-2.5 text-left text-xs font-semibold text-blue-300/80 uppercase tracking-wider border-b border-gray-600/50 cursor-pointer select-none whitespace-nowrap hover:bg-[#22222e] transition-colors"
              >
                {col.label}
                <span className="text-blue-400/60">{sortIndicator(col.key)}</span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sortedRows.map((row, ri) => (
            <tr
              key={ri}
              className="hover:bg-blue-900/10 transition-colors border-b border-gray-800/40 even:bg-white/[0.015]"
            >
              <td className="px-2 py-2 text-center">
                <button
                  onClick={() => toggleSavedTender(row)}
                  className={`text-lg transition-colors ${
                    isSaved(row)
                      ? 'text-yellow-400 hover:text-yellow-300'
                      : 'text-gray-600 hover:text-yellow-400/70'
                  }`}
                  title={isSaved(row) ? 'Remove from saved' : 'Save tender'}
                >
                  {isSaved(row) ? '★' : '☆'}
                </button>
              </td>
              {table.columns.map((col) => {
                const val = row[col.key]
                return (
                  <td
                    key={col.key}
                    className="px-3 py-2 max-w-[300px] truncate text-gray-300"
                    title={String(val ?? '')}
                  >
                    {isUrl(val) ? (
                      <a
                        href={val}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-400 hover:text-blue-300 underline"
                      >
                        View ↗
                      </a>
                    ) : (
                      String(val ?? '')
                    )}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
