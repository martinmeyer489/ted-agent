'use client'

import { useCallback } from 'react'
import { useStore } from '@/store'
import * as XLSX from 'xlsx'
import TableView from './TableView'

export default function WorkspacePanel() {
  const table = useStore((s) => s.workspaceTable)
  const setTable = useStore((s) => s.setWorkspaceTable)
  const width = useStore((s) => s.workspaceWidth)

  const handleExport = useCallback(() => {
    if (!table) return
    const headerRow = table.columns.map((c) => c.label)
    const dataRows = table.rows.map((row) =>
      table.columns.map((col) => row[col.key] ?? '')
    )
    const ws = XLSX.utils.aoa_to_sheet([headerRow, ...dataRows])
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, 'Results')
    XLSX.writeFile(wb, `${table.title.replace(/[^a-zA-Z0-9_-]/g, '_')}.xlsx`)
  }, [table])

  return (
    <div
      className="flex flex-col h-full bg-[#0d0d0f] border-r border-gray-700/60"
      style={{ width: `${width}%`, minWidth: 300 }}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700/60 bg-[#141418] flex-shrink-0">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-blue-400 text-sm">📊</span>
          <h2 className="text-sm font-semibold text-primary truncate">
            {table ? table.title : 'Workspace'}
          </h2>
        </div>
        <div className="flex items-center gap-1 flex-shrink-0">
          {table && (
            <>
              <button
                onClick={handleExport}
                className="text-muted hover:text-primary text-xs px-2 py-1 rounded hover:bg-gray-700 transition-colors"
                title="Export to Excel"
              >
                ⬇ .xlsx
              </button>
              <button
                onClick={() => setTable(null)}
                className="text-muted hover:text-primary text-xs px-2 py-1 rounded hover:bg-gray-700 transition-colors"
                title="Clear table"
              >
                ✕
              </button>
            </>
          )}
        </div>
      </div>

      {/* Content */}
      {table ? (
        <div className="flex flex-col flex-1 overflow-hidden">
          <div className="px-4 py-2 text-xs text-muted/70 border-b border-gray-700/40 bg-[#111115] flex-shrink-0">
            {table.rows.length} row{table.rows.length !== 1 ? 's' : ''} · {table.columns.length} column{table.columns.length !== 1 ? 's' : ''}
          </div>
          <TableView table={table} />
        </div>
      ) : (
        <div className="flex-1 flex flex-col items-center justify-center text-muted/50 text-sm px-8 text-center gap-3">
          <span className="text-3xl opacity-30">📊</span>
          <p>No table yet</p>
          <p className="text-xs text-muted/30">Search for tenders to populate this workspace</p>
        </div>
      )}
    </div>
  )
}
