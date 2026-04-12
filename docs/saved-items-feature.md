# Saved Items Feature - Implementation & Migration Guide

## Overview

The TED Bot now supports saving tenders and buyers locally in the browser. This document covers:
1. ✅ Current implementation (local storage)
2. 🔄 Future migration path to database
3. 🛠️ How to extend functionality

---

## Current Implementation: Local Browser Storage

### Architecture

**Frontend (Local Storage)**
```
User Action → Zustand Store → localStorage (persisted) → UI Update
```

**Components:**
- `store.ts`: State management with persistence
  - `savedTenders: TableRow[]`
  - `savedBuyers: TableRow[]`
  - Methods: `toggleSavedTender`, `toggleSavedBuyer`, `removeSaved*`, `clearSaved*`
  
- `TableView.tsx`: Star buttons (★/☆) for saving from search results
- `SavedItemsButton.tsx`: Sidebar navigation with badge count
- `app/saved/page.tsx`: Dedicated view for browsing saved items

### User Flows

**Saving a Tender:**
1. User searches for tenders → results appear in workspace table
2. User clicks ☆ (empty star) on a tender row
3. Star becomes ★ (filled), row saved to localStorage
4. Badge count updates in sidebar

**Viewing Saved Items:**
1. User clicks "Saved Items" button in sidebar
2. Navigates to `/saved` page
3. Can view/export/remove saved tenders and buyers

**Data Persistence:**
- Uses Zustand's `persist` middleware
- Storage key: `endpoint-storage`
- Survives page refreshes and browser restarts
- Limited to single browser/device

### Limitations & When to Migrate

**Migrate to database when you need:**

| Feature | Local Storage | Database |
|---------|---------------|----------|
| Cross-device sync | ❌ | ✅ |
| Sharing saved lists | ❌ | ✅ |
| Email notifications | ❌ | ✅ |
| Team collaboration | ❌ | ✅ |
| Notes & tags | Limited | ✅ |
| Backup/restore | Manual export | Automatic |
| Search saved items | Client-side only | Server-side |

---

## Migration Path: Database Implementation

### Phase 1: Database Schema

Add tables to your Supabase database:

```sql
-- Saved tenders table
CREATE TABLE saved_tenders (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  
  -- TED tender data
  notice_id TEXT NOT NULL,
  title TEXT,
  buyer_name TEXT,
  buyer_country TEXT,
  publication_date DATE,
  deadline_date DATE,
  cpv_code TEXT,
  estimated_value NUMERIC,
  
  -- Metadata stored as JSONB for flexibility
  metadata JSONB,
  
  -- User annotations
  notes TEXT,
  tags TEXT[],
  
  -- Timestamps
  saved_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  
  -- Prevent duplicates per user
  UNIQUE(user_id, notice_id)
);

-- Saved buyers table
CREATE TABLE saved_buyers (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  
  -- Buyer information
  buyer_name TEXT NOT NULL,
  buyer_city TEXT,
  buyer_country TEXT,
  
  -- Analytics
  total_tenders INTEGER,
  total_value NUMERIC,
  top_cpv_codes TEXT[],
  
  -- User annotations
  notes TEXT,
  tags TEXT[],
  
  -- Metadata
  metadata JSONB,
  
  -- Timestamps
  saved_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  
  UNIQUE(user_id, buyer_name, buyer_country)
);

-- Create indexes for performance
CREATE INDEX idx_saved_tenders_user ON saved_tenders(user_id);
CREATE INDEX idx_saved_tenders_notice ON saved_tenders(notice_id);
CREATE INDEX idx_saved_buyers_user ON saved_buyers(user_id);
CREATE INDEX idx_saved_buyers_name ON saved_buyers(buyer_name);

-- Enable Row Level Security (RLS)
ALTER TABLE saved_tenders ENABLE ROW LEVEL SECURITY;
ALTER TABLE saved_buyers ENABLE ROW LEVEL SECURITY;

-- RLS Policies: Users can only access their own saved items
CREATE POLICY "Users can view their own saved tenders"
  ON saved_tenders FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own saved tenders"
  ON saved_tenders FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own saved tenders"
  ON saved_tenders FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own saved tenders"
  ON saved_tenders FOR DELETE
  USING (auth.uid() = user_id);

-- Same for buyers
CREATE POLICY "Users can view their own saved buyers"
  ON saved_buyers FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own saved buyers"
  ON saved_buyers FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own saved buyers"
  ON saved_buyers FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own saved buyers"
  ON saved_buyers FOR DELETE
  USING (auth.uid() = user_id);
```

### Phase 2: Backend API Endpoints

Add REST API routes in `backend/app/api/routes/saved.py`:

```python
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.models.schemas import SavedTender, SavedBuyer
from app.services.supabase_client import get_supabase
from supabase import Client

router = APIRouter(prefix="/saved", tags=["saved"])

@router.get("/tenders", response_model=List[SavedTender])
async def get_saved_tenders(supabase: Client = Depends(get_supabase)):
    """Retrieve all saved tenders for the authenticated user."""
    result = supabase.table("saved_tenders").select("*").execute()
    return result.data

@router.post("/tenders")
async def save_tender(tender: SavedTender, supabase: Client = Depends(get_supabase)):
    """Save a tender."""
    result = supabase.table("saved_tenders").insert(tender.dict()).execute()
    return result.data

@router.delete("/tenders/{tender_id}")
async def delete_tender(tender_id: str, supabase: Client = Depends(get_supabase)):
    """Remove a saved tender."""
    result = supabase.table("saved_tenders").delete().eq("id", tender_id).execute()
    return {"success": True}

@router.patch("/tenders/{tender_id}")
async def update_tender(
    tender_id: str, 
    notes: str = None,
    tags: List[str] = None,
    supabase: Client = Depends(get_supabase)
):
    """Update notes/tags for a saved tender."""
    updates = {}
    if notes is not None:
        updates["notes"] = notes
    if tags is not None:
        updates["tags"] = tags
    
    result = supabase.table("saved_tenders").update(updates).eq("id", tender_id).execute()
    return result.data

# Similar endpoints for buyers...
```

### Phase 3: Agent Tools (Optional)

Add tools to enable the agent to save items on behalf of users:

```python
@tool
def save_tender_for_user(
    notice_id: str,
    title: str,
    buyer_name: str = None,
    notes: str = None,
) -> str:
    """
    Save a tender to the user's saved items.
    
    Use this when the user explicitly asks to save a tender,
    e.g., "save this tender" or "bookmark notice 123456-2024".
    
    Args:
        notice_id: TED notice ID (e.g., "123456-2024")
        title: Tender title
        buyer_name: Optional buyer name
        notes: Optional user notes
    
    Returns:
        Confirmation message
    """
    # Implementation calls backend API
    # POST /saved/tenders
    pass

@tool
def save_buyer_profile(
    buyer_name: str,
    buyer_country: str,
    total_tenders: int = None,
    notes: str = None,
) -> str:
    """
    Save a buyer profile for tracking.
    
    Use when user requests to track/save/bookmark a buyer,
    e.g., "save this buyer for future reference".
    
    Args:
        buyer_name: Buyer organization name
        buyer_country: Country code
        total_tenders: Number of tenders analyzed
        notes: Optional notes
    
    Returns:
        Confirmation message
    """
    pass
```

### Phase 4: Frontend Migration

**Keep local storage as fallback:**
```typescript
// Hybrid approach: try database first, fallback to local
const useSavedTenders = () => {
  const [tenders, setTenders] = useState<SavedTender[]>([])
  const [isOnline, setIsOnline] = useState(true)
  const localTenders = useStore((s) => s.savedTenders)
  
  useEffect(() => {
    if (isOnline) {
      // Fetch from database
      fetch('/api/saved/tenders')
        .then(res => res.json())
        .then(setTenders)
        .catch(() => {
          setIsOnline(false)
          setTenders(localTenders) // Fallback
        })
    } else {
      setTenders(localTenders)
    }
  }, [isOnline])
  
  return { tenders, isOnline }
}
```

### Phase 5: Data Migration Script

Provide users a one-time migration to move local storage to database:

```typescript
// app/saved/migrate/page.tsx
export default function MigratePage() {
  const localTenders = useStore((s) => s.savedTenders)
  const localBuyers = useStore((s) => s.savedBuyers)
  const [status, setStatus] = useState<'idle' | 'migrating' | 'done'>('idle')
  
  const handleMigrate = async () => {
    setStatus('migrating')
    
    // Upload local data to database
    await Promise.all([
      fetch('/api/saved/tenders/bulk', {
        method: 'POST',
        body: JSON.stringify(localTenders)
      }),
      fetch('/api/saved/buyers/bulk', {
        method: 'POST',
        body: JSON.stringify(localBuyers)
      })
    ])
    
    setStatus('done')
  }
  
  return (
    <div>
      <h1>Migrate Saved Items to Cloud</h1>
      <p>Found {localTenders.length} tenders and {localBuyers.length} buyers</p>
      <button onClick={handleMigrate}>Migrate Now</button>
    </div>
  )
}
```

---

## Advanced Features (Database Only)

### Email Notifications for Saved Tenders

```python
# Add a notification preferences table
CREATE TABLE tender_notifications (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES auth.users(id),
  saved_tender_id UUID REFERENCES saved_tenders(id),
  notify_on_deadline BOOLEAN DEFAULT TRUE,
  notify_days_before INTEGER DEFAULT 7,
  last_notified_at TIMESTAMP
);

# Cron job to check deadlines
@scheduler.scheduled_job('cron', hour=9)  # Daily at 9 AM
async def send_deadline_reminders():
    # Query tenders with upcoming deadlines
    # Send email notifications
    pass
```

### Collaboration & Sharing

```python
# Shared saved lists
CREATE TABLE saved_lists (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  owner_id UUID REFERENCES auth.users(id),
  name TEXT NOT NULL,
  description TEXT,
  is_public BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE saved_list_items (
  list_id UUID REFERENCES saved_lists(id),
  tender_id UUID REFERENCES saved_tenders(id),
  added_at TIMESTAMP DEFAULT NOW(),
  PRIMARY KEY (list_id, tender_id)
);

CREATE TABLE list_collaborators (
  list_id UUID REFERENCES saved_lists(id),
  user_id UUID REFERENCES auth.users(id),
  permission TEXT CHECK (permission IN ('view', 'edit', 'admin')),
  PRIMARY KEY (list_id, user_id)
);
```

---

## Decision Framework

### Stick with Local Storage if:
- ✅ Single user application
- ✅ Prototype/MVP phase
- ✅ Privacy is critical (data never leaves device)
- ✅ No need for cross-device sync
- ✅ Budget constraints (avoid database costs)

### Migrate to Database if:
- ✅ Multi-device support needed
- ✅ Team collaboration features
- ✅ Email notifications required
- ✅ Advanced search/filtering on saved items
- ✅ Analytics on user behavior
- ✅ Sharing saved lists publicly

---

## Hybrid Approach (Best of Both Worlds)

**Recommended Architecture:**
1. **Default**: Use local storage (fast, offline-capable)
2. **Optional**: User can enable cloud sync (requires login)
3. **Progressive Enhancement**: Features like sharing only available with cloud

**Benefits:**
- Works offline without authentication
- Users control their data
- Premium features incentivize cloud sync
- Graceful degradation

**Implementation:**
```typescript
const saveStrategy = user?.hasCloudSyncEnabled 
  ? 'database'  // POST to /api/saved/tenders
  : 'local'     // Save to localStorage

if (saveStrategy === 'database') {
  // Also save to local as cache
}
```

---

## Cost Analysis

### Local Storage: $0/month
- No server costs
- No database costs
- Scales to infinity (each user stores their own data)

### Database (Supabase):
- Free tier: Up to 500 MB, 2 GB bandwidth/month
- Pro ($25/mo): 8 GB, 250 GB bandwidth
- Estimate: ~100 KB per saved tender × 1000 users × 10 tenders = ~1 GB

**Recommendation**: Start with local storage, migrate when you have 100+ active users requesting sync features.

---

## Testing Checklist

### Current Implementation (Local Storage)
- [x] Star button toggles save state
- [x] Badge count updates in sidebar
- [x] Saved page displays items correctly
- [x] Export to Excel works
- [x] Data persists after page refresh
- [x] Remove items works
- [x] Clear all works with confirmation

### Future (Database)
- [ ] Authentication required for save
- [ ] Data syncs across devices
- [ ] RLS policies enforce user isolation
- [ ] Migration script moves local → cloud
- [ ] Offline mode with conflict resolution
- [ ] Email notifications for deadlines

---

## Summary

**Current state**: ✅ Fully functional local storage implementation  
**Migration effort**: ~2-3 days for basic database version  
**Recommendation**: Ship current version, collect user feedback, then decide on migration  

The local storage approach is production-ready for:
- Individual users
- MVP validation
- Privacy-focused applications

Migrate to database when you need collaboration, sync, or notifications.
