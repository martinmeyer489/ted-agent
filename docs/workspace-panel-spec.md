# Workspace Panel — Feature Specification

## Overview

A **resizable left-side panel** showing a single data table. The table is created when the agent searches for tenders and can be modified by prompting the agent (e.g., "remove French tenders", "sort by date"). The table data is automatically included as context in every prompt so the agent can reference and edit it.

---

## 1. Table Data Model

```typescript
interface WorkspaceTable {
  id: string                       // uuid, set on creation
  title: string                    // e.g. "Software tenders in Germany"
  columns: TableColumn[]
  rows: Record<string, any>[]
}

interface TableColumn {
  key: string                      // e.g. "noticeId"
  label: string                    // e.g. "Publication Number"
}
```

---

## 2. How It Works

### Creating the table

1. User asks: *"Find software tenders in Germany"*
2. `search_ted_tenders` tool runs, returns JSON: `{ "text": "markdown...", "table": { id, title, columns, rows } }`
3. Route handler extracts `table` from tool content, attaches it to the `ToolCallCompleted` SSE event.
4. Frontend sees `ToolCallCompleted` with a `table` field → stores it in Zustand → panel opens.

### Editing the table — filtering/sorting rows

1. User asks: *"Remove all tenders from France"*
2. Frontend prepends workspace context (table data + table ID) to the message automatically.
3. Agent calls `update_workspace_table(table_id, title, columns_json, rows_json)`.
4. Same flow: tool returns JSON with `table`, route attaches it to `ToolCallCompleted`, frontend replaces the table.

### Adding columns — enriching with details

1. User asks: *"Get the deadline and estimated value for all tenders"*
2. Agent sees the table in context, calls `get_ted_notice_details(notice_id)` for each row.
3. Agent extracts the new fields from the detail responses.
4. Agent calls `update_workspace_table(table_id, title, new_columns_json, updated_rows_json)` with:
   - **Existing columns** + new columns (e.g., `deadline`, `estimatedValue`)
   - **Existing rows** with new fields populated
5. Frontend replaces the table with the enriched version.

### Replacing the table

A new search simply overwrites the current table (new ID).

### Example workflow

**Initial search:**
```
User: Find software tenders in Germany
Agent: [calls search_ted_tenders] → creates table with 7 columns (index, title, buyer, country, published, noticeId, link)
```

**Add details:**
```
User: Get the deadline and estimated value for all tenders
Agent: [sees 10 rows in table context]
       [calls get_ted_notice_details(notice_id) for each row]
       [extracts deadline, estimatedValue from results]
       [calls update_workspace_table with 9 columns (original 7 + deadline + estimatedValue), 10 updated rows]
Frontend: Table now shows 9 columns
```

**Filter:**
```
User: Remove tenders with no deadline
Agent: [filters rows where deadline is not null]
       [calls update_workspace_table with 9 columns, 6 rows]
Frontend: Table now shows 6 rows
```

---

## 3. SSE: Extended `ToolCallCompleted`

No new event types. Optional `table` field on existing event:

```json
{
  "event": "ToolCallCompleted",
  "tool": { "tool_name": "search_ted_tenders", "content": "markdown...", ... },
  "table": {
    "id": "abc-123",
    "title": "Software tenders in Germany",
    "columns": [
      { "key": "index", "label": "#" },
      { "key": "title", "label": "Title" },
      { "key": "buyer", "label": "Buyer" },
      { "key": "country", "label": "Country" },
      { "key": "published", "label": "Published" },
      { "key": "noticeId", "label": "Publication Number" },
      { "key": "link", "label": "TED Link" }
    ],
    "rows": [{ "index": 1, "title": "IT consulting...", ... }]
  },
  "session_id": "...",
  "run_id": "...",
  "created_at": 1712750400
}
```

Frontend logic: if `table` is present, call `setWorkspaceTable(table)`.

---

## 4. Auto-Context

Before every message, the frontend prepends the table data:

```
[WORKSPACE TABLE]
Table ID: "abc-123" | Title: "Software tenders in Germany" | 10 rows
To modify this table, use the update_workspace_table tool with the table ID.
You can filter/remove rows, add new columns with enriched data, or re-order columns.

| # | Title | Buyer | Country | Published | Publication Number |
|---|-------|-------|---------|-----------|-------------------|
| 1 | IT consulting... | Bundesmin... | DEU | 2026-04-08 | 247404-2026 |
...
[END WORKSPACE TABLE]

User: Get the deadline and estimated value for all tenders
```

Limit: max 500 rows. If exceeded, truncate with a note.

---

## 5. UI Layout

```
┌───────────────────────────────────────────────────┐
│ ┌─────────────────┐ ↔ ┌────────────────────────┐ │
│ │  WORKSPACE       │   │      CHAT AREA         │ │
│ │                  │   │                         │ │
│ │  Title bar       │   │  Messages...            │ │
│ │  ┌─────────────┐ │   │                         │ │
│ │  │ Data table  │ │   │                         │ │
│ │  │             │ │   │  ┌───────────────────┐  │ │
│ │  │             │ │   │  │ Chat Input        │  │ │
│ │  └─────────────┘ │   │  └───────────────────┘  │ │
│ └─────────────────┘   └────────────────────────┘ │
└───────────────────────────────────────────────────┘
```

- Default 40% width, min 300px, max 60%
- Draggable divider to resize
- Collapsible (toggle button on chat side when hidden)
- Auto-opens when table data arrives
- Empty state: "No table yet — search for tenders to populate"

### Table features

- Sortable columns (click header)
- Scrollable (both axes)
- Row hover highlight
- Links rendered as clickable `<a>` tags
- **Dynamic columns**: table re-renders when columns are added/removed
- Close button (clears table, collapses panel)

---

## 6. State (Zustand)

```typescript
// Added to existing store
workspaceTable: WorkspaceTable | null
setWorkspaceTable: (table: WorkspaceTable | null) => void
isWorkspaceOpen: boolean
setIsWorkspaceOpen: (open: boolean) => void
workspaceWidth: number  // persisted
setWorkspaceWidth: (w: number) => void
```

Persisted to `localStorage`: `workspaceTable`, `workspaceWidth`, `isWorkspaceOpen`.

---

## 7. Backend Changes

### 7.1 `search_ted_tenders` — return JSON with `text` + `table`

```python
return json.dumps({
    "text": result_text,
    "table": {
        "id": str(uuid.uuid4()),
        "title": f"{query} — {len(notices)} results",
        "columns": [
            {"key": "index", "label": "#"},
            {"key": "title", "label": "Title"},
            {"key": "buyer", "label": "Buyer"},
            {"key": "country", "label": "Country"},
            {"key": "published", "label": "Published"},
            {"key": "noticeId", "label": "Publication Number"},
            {"key": "link", "label": "TED Link"},
        ],
        "rows": rows_list,
    }
})
```

### 7.2 New tool: `update_workspace_table`

```python
@tool
def update_workspace_table(table_id, title, columns_json, rows_json) -> str:
    """
    Update a workspace table. Use this to:
    - Filter or remove rows
    - Add new columns with enriched data (e.g., deadline, estimated value from notice details)
    - Re-order or rename columns
    
    Args:
        table_id: The table ID from workspace context
        title: Updated title (can be same as before)
        columns_json: JSON array of all columns (existing + new), e.g. '[{"key":"title","label":"Title"},{"key":"deadline","label":"Deadline"}]'
        rows_json: JSON array of all rows with all fields populated
    
    To add columns: call get_ted_notice_details for each notice, extract the new fields, then call this tool with the combined column list and updated rows.
    """
    columns = json.loads(columns_json)
    rows = json.loads(rows_json)
    return json.dumps({
        "text": f"Updated table '{title}' ({len(rows)} rows, {len(columns)} columns).",
        "table": {"id": table_id, "title": title, "columns": columns, "rows": rows}
    })
```

### 7.3 `agentos.py` — extract `table` from tool content

In `ToolCallCompleted` handler: try to parse tool content as JSON. If it has a `table` key, pull it out, put `text` back as `content`, attach `table` to the event payload.

---

## 8. Files

### New
| File | Purpose |
|---|---|
| `frontend/agent-ui/src/components/workspace/WorkspacePanel.tsx` | Panel with header, table, empty state |
| `frontend/agent-ui/src/components/workspace/TableView.tsx` | Sortable data table |
| `frontend/agent-ui/src/components/workspace/ResizeDivider.tsx` | Drag handle |
| `frontend/agent-ui/src/types/workspace.ts` | `WorkspaceTable`, `TableColumn` types |

### Modified
| File | Changes |
|---|---|
| `store.ts` | Add `workspaceTable`, `isWorkspaceOpen`, `workspaceWidth` |
| `page.tsx` | Flex layout: WorkspacePanel + ChatArea |
| `useAIStreamHandler.tsx` | Extract `table` from `ToolCallCompleted` → `setWorkspaceTable()` |
| `useAIResponseStream.tsx` | Prepend workspace context to outgoing messages |
| `tools.py` | `search_ted_tenders` returns JSON; new `update_workspace_table` |
| `agentos.py` | Extract `table` from tool content into event payload |
| `ted_agent.py` | Register `update_workspace_table` tool |
