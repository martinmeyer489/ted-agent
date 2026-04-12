export interface TableColumn {
  key: string
  label: string
}

export type RowValue = string | number | boolean | null | undefined
export type TableRow = Record<string, RowValue>

export interface WorkspaceTable {
  id: string
  title: string
  columns: TableColumn[]
  rows: TableRow[]
}
