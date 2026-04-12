export interface TableColumn {
  key: string
  label: string
}

export interface WorkspaceTable {
  id: string
  title: string
  columns: TableColumn[]
  rows: Record<string, string | number | boolean | null | undefined>[]
}
