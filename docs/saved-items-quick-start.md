# Saved Items Feature - Quick Start Guide

## For Users

### How to Save Tenders

1. **Search for tenders** using the chat interface
2. **View results** in the workspace table on the right
3. **Click the ☆ (star)** button on any tender row you want to save
4. The star becomes **★ (filled)** and the item is saved to your browser

### How to View Saved Items

1. **Click "Saved Items"** button in the left sidebar (shows count badge)
2. Switch between **Tenders** and **Buyers** tabs
3. **Export to Excel** using the download button
4. **Remove items** individually or clear all

### Saving Buyers

Currently, buyers can be saved from search results. Future feature: save from buyer profile analysis.

---

## For Developers

### Current Implementation Status

✅ **Completed:**
- Local storage persistence (Zustand + localStorage)
- Star button UI in table view
- Saved items page with tabs
- Export to Excel functionality
- Badge counter in sidebar
- Support for both tenders and buyers
- Comprehensive documentation

❌ **Not Yet Implemented:**
- Database storage
- Cross-device sync
- Agent tools to save items via chat
- Email notifications
- Sharing/collaboration
- Notes and tags

### Code Structure

```
frontend/src/
├── store.ts                          # State management
│   ├── savedTenders: TableRow[]
│   ├── savedBuyers: TableRow[]
│   ├── toggleSavedTender()
│   ├── toggleSavedBuyer()
│   └── ... (clear, remove methods)
│
├── app/saved/page.tsx               # Saved items view
│
├── components/
│   ├── chat/Sidebar/
│   │   └── SavedItemsButton.tsx     # Navigation button
│   └── workspace/
│       └── TableView.tsx            # Star buttons
│
└── types/workspace.ts               # TableRow interface
```

### API Surface

**Store Methods:**
```typescript
// Tenders
toggleSavedTender(row: TableRow): void     // Toggle save/unsave
removeSavedTender(index: number): void     // Remove by index
clearSavedTenders(): void                   // Clear all

// Buyers
toggleSavedBuyer(row: TableRow): void
removeSavedBuyer(index: number): void
clearSavedBuyers(): void

// State
savedTenders: TableRow[]                   // Array of saved tender rows
savedBuyers: TableRow[]                    // Array of saved buyer rows
```

**Storage Key:**
- `endpoint-storage` in localStorage
- Persisted fields include: `savedTenders`, `savedBuyers`, `workspaceTable`, etc.

### Adding Save Capability to New Tables

To make any table saveable:

```typescript
// 1. In your table component
import { useStore } from '@/store'

const savedItems = useStore((s) => s.savedTenders)
const toggleSaved = useStore((s) => s.toggleSavedTender)

const isSaved = (row: TableRow) =>
  savedItems.some((item) => JSON.stringify(item) === JSON.stringify(row))

// 2. Add star button in your table
<button onClick={() => toggleSaved(row)}>
  {isSaved(row) ? '★' : '☆'}
</button>
```

### Testing Locally

```bash
# Frontend
cd frontend
pnpm dev

# Navigate to http://localhost:3000
# Search for tenders
# Click stars to save
# Click "Saved Items" in sidebar
# Verify persistence by refreshing page
```

### Migrating to Database (Future)

See `docs/saved-items-feature.md` for complete migration guide including:
- SQL schema for Supabase
- Backend API endpoints
- Agent tools for programmatic saving
- Authentication & RLS policies
- Data migration script

**Estimated effort:** 2-3 days

---

## User Stories

### Story 1: Save Interesting Tenders
**As a** procurement professional  
**I want to** save interesting tenders while browsing  
**So that** I can review them later without searching again  

**Acceptance Criteria:**
- ✅ Can save/unsave tenders with one click
- ✅ Saved tenders persist after closing browser
- ✅ Can view all saved tenders in one place
- ✅ Can export saved tenders to Excel

### Story 2: Track Key Buyers
**As a** business development manager  
**I want to** save buyer profiles I'm targeting  
**So that** I can quickly access their procurement patterns  

**Acceptance Criteria:**
- ✅ Can save buyer information
- ✅ Saved buyers visible in dedicated tab
- ✅ Can export buyer list

### Story 3: Backup Saved Items
**As a** cautious user  
**I want to** export my saved items  
**So that** I don't lose data if I clear my browser  

**Acceptance Criteria:**
- ✅ One-click export to Excel
- ✅ Includes all saved data
- ✅ Filename includes date

---

## FAQ

**Q: Where is my data stored?**  
A: Locally in your browser's localStorage. It never leaves your device.

**Q: Will I lose my saved items if I clear browser data?**  
A: Yes. Use the Export button to backup your data first.

**Q: Can I access saved items on my phone?**  
A: Not yet. Each browser/device has its own storage. Database sync coming in future version.

**Q: How many items can I save?**  
A: Unlimited (subject to browser localStorage limits, typically ~10 MB).

**Q: Can I add notes to saved items?**  
A: Not in the current version. This will be added with database implementation.

**Q: Can I share my saved list with colleagues?**  
A: Not yet. Sharing requires the database version.

**Q: Can I get notified about deadlines for saved tenders?**  
A: Not currently. Email notifications will be added with database version.

---

## Troubleshooting

**Problem: Saved items disappeared**  
- Check if browser data was cleared
- Check if localStorage is enabled
- Look for "endpoint-storage" key in DevTools → Application → Local Storage

**Problem: Can't export to Excel**  
- Make sure you have saved items
- Check browser console for errors
- Try a different browser

**Problem: Star button doesn't work**  
- Check if JavaScript is enabled
- Clear cache and reload
- Check browser console for errors

**Problem: Saved count badge is wrong**  
- Close and reopen the browser
- Check DevTools console for errors
- File a bug report with console logs

---

## Roadmap

### v1.0 (Current) - Local Storage
- ✅ Save/unsave tenders and buyers
- ✅ View saved items
- ✅ Export to Excel
- ✅ Persist across sessions

### v1.1 (Next) - Enhanced UX
- ⏳ Agent commands: "save this tender"
- ⏳ Bulk actions (save all, unsave all)
- ⏳ Search within saved items
- ⏳ Sort and filter saved items

### v2.0 (Future) - Database & Sync
- ⏳ Cloud storage with Supabase
- ⏳ Cross-device sync
- ⏳ User authentication
- ⏳ Email notifications for deadlines
- ⏳ Notes and tags on saved items
- ⏳ Shared lists and collaboration

---

## Contributing

To extend this feature:

1. **Add new save types** (e.g., saved searches):
   - Add state to `store.ts`
   - Create toggle/remove/clear methods
   - Add to persistence config
   - Add UI in saved page

2. **Add metadata** (notes, tags):
   - Extend `TableRow` type or create new type
   - Update toggle methods to include metadata
   - Update saved page UI

3. **Implement database storage**:
   - Follow migration guide in `docs/saved-items-feature.md`
   - Create Supabase tables
   - Add API endpoints
   - Update frontend to use API

---

**Last Updated:** April 2026  
**Version:** 1.0  
**Status:** Production Ready (Local Storage)
