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
    <div className="flex-1 overflow-x-auto bg-background">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr>
            <th className="sticky top-0 z-10 bg-background px-3 py-2 text-center text-xs font-medium text-muted-foreground uppercase tracking-wide border-b w-10">
              ★
            </th>
            {table.columns.map((col) => (
              <th
                key={col.key}
                onClick={() => handleSort(col.key)}
                className="sticky top-0 z-10 bg-background px-3 py-2 text-left text-xs font-medium text-muted-foreground uppercase tracking-wide border-b cursor-pointer select-none whitespace-nowrap hover:bg-muted/30 transition-colors"
              >
                {col.label}
                <span className="opacity-60">{sortIndicator(col.key)}</span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sortedRows.map((row, ri) => (
            <tr
              key={ri}
              className="hover:bg-muted/50 transition-colors border-b"
            >
              <td className="px-3 py-2 text-center">
                <button
                  onClick={() => toggleSavedTender(row)}
                  className={`text-base transition-colors ${
                    isSaved(row)
                      ? 'text-yellow-400 hover:text-yellow-300'
                      : 'text-muted-foreground/40 hover:text-yellow-400/70'
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
                    className="px-3 py-2 text-sm"
                    title={String(val ?? '')}
                  >
                    {isUrl(val) ? (
                      <a
                        href={val}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary hover:text-primary/80 underline truncate max-w-[200px] inline-block"
                        title={val}
                      >
                        View ↗
                      </a>
                    ) : (
                      <span className="truncate max-w-[200px] inline-block" title={String(val ?? '')}>
                        {String(val ?? '')}
                      </span>
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
