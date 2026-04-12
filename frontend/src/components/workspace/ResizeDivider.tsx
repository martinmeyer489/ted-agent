'use client'

import { useCallback, useEffect, useRef } from 'react'
import { useStore } from '@/store'

export default function ResizeDivider() {
  const setWorkspaceWidth = useStore((s) => s.setWorkspaceWidth)
  const isDragging = useRef(false)

  const onMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    isDragging.current = true
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
  }, [])

  useEffect(() => {
    const onMouseMove = (e: MouseEvent) => {
      if (!isDragging.current) return
      const pct = (e.clientX / window.innerWidth) * 100
      const clamped = Math.min(60, Math.max(20, pct))
      setWorkspaceWidth(clamped)
    }
    const onMouseUp = () => {
      isDragging.current = false
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }
    window.addEventListener('mousemove', onMouseMove)
    window.addEventListener('mouseup', onMouseUp)
    return () => {
      window.removeEventListener('mousemove', onMouseMove)
      window.removeEventListener('mouseup', onMouseUp)
    }
  }, [setWorkspaceWidth])

  return (
    <div
      onMouseDown={onMouseDown}
      className="w-[3px] cursor-col-resize bg-gray-700/40 hover:bg-blue-500/60 active:bg-blue-500 transition-colors flex-shrink-0"
    />
  )
}
