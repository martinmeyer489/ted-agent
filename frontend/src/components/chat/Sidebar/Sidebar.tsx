'use client'
import { Button } from '@/components/ui/button'
import UserProfile from '@/components/chat/Sidebar/UserProfile'
import useChatActions from '@/hooks/useChatActions'
import { useStore } from '@/store'
import { motion } from 'framer-motion'
import { useState, useEffect } from 'react'
import Icon from '@/components/ui/icon'
import Sessions from './Sessions'
import SavedItemsButton from './SavedItemsButton'

const NewChatButton = ({
  disabled,
  onClick
}: {
  disabled: boolean
  onClick: () => void
}) => (
  <Button
    onClick={onClick}
    disabled={disabled}
    size="lg"
    className="h-9 w-full rounded-xl bg-primary text-xs font-medium text-background hover:bg-primary/80"
  >
    <Icon type="plus-icon" size="xs" className="text-background" />
    <span className="uppercase">New Chat</span>
  </Button>
)

const Sidebar = ({
  hasEnvToken,
  envToken
}: {
  hasEnvToken?: boolean
  envToken?: string
}) => {
  const [isCollapsed, setIsCollapsed] = useState(false)
  const { clearChat, focusChatInput, initialize } = useChatActions()
  const {
    messages,
    selectedEndpoint,
    isEndpointActive,
    hydrated,
    mode
  } = useStore()
  const [isMounted, setIsMounted] = useState(false)

  useEffect(() => {
    setIsMounted(true)

    if (hydrated) initialize()
  }, [selectedEndpoint, initialize, hydrated, mode])

  const handleNewChat = () => {
    clearChat()
    focusChatInput()
  }

  return (
    <motion.aside
      className="relative flex h-full shrink-0 grow-0 flex-col overflow-hidden bg-white border-r border-gray-200 px-2 py-3 font-dmmono"
      initial={{ width: '16rem' }}
      animate={{ width: isCollapsed ? '2.5rem' : '16rem' }}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
    >
      <motion.button
        onClick={() => setIsCollapsed(!isCollapsed)}
        className="absolute right-2 top-5 z-10 rounded-md bg-gray-100 p-2 shadow-sm transition-colors hover:bg-gray-200"
        aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        type="button"
        whileTap={{ scale: 0.95 }}
      >
        <Icon
          type="sheet"
          size="sm"
          className={`transform transition-transform text-gray-700 hover:text-gray-900 ${isCollapsed ? 'rotate-180' : 'rotate-0'}`}
        />
      </motion.button>
      <motion.div
        className="h-full w-60 space-y-5 bg-white pt-12"
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: isCollapsed ? 0 : 1, x: isCollapsed ? -20 : 0 }}
        transition={{ duration: 0.3, ease: 'easeInOut' }}
        style={{
          pointerEvents: isCollapsed ? 'none' : 'auto'
        }}
      >
        <NewChatButton
          disabled={messages.length === 0}
          onClick={handleNewChat}
        />
        {isMounted && (
          <>
            <SavedItemsButton />
            <UserProfile />
            {isEndpointActive && <Sessions />}
          </>
        )}
      </motion.div>
    </motion.aside>
  )
}

export default Sidebar
