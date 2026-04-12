'use client'

import { useStore } from '@/store'
import { useRouter } from 'next/navigation'

export default function SavedItemsButton() {
  const router = useRouter()
  const savedTenders = useStore((s) => s.savedTenders)
  const savedBuyers = useStore((s) => s.savedBuyers)
  
  const totalSaved = savedTenders.length + savedBuyers.length

  const handleClick = () => {
    router.push('/saved')
  }

  return (
    <button
      onClick={handleClick}
      className="flex w-full items-center justify-between rounded-xl border border-primary/15 bg-accent px-3 py-2 text-xs font-medium uppercase text-muted hover:bg-accent/80 transition-colors"
      title="View saved tenders and buyers"
    >
      <div className="flex items-center gap-2">
        <span className="text-yellow-500">★</span>
        <span>Saved Items</span>
      </div>
      {totalSaved > 0 && (
        <span className="rounded-full bg-primary px-2 py-0.5 text-xs text-background">
          {totalSaved}
        </span>
      )}
    </button>
  )
}
