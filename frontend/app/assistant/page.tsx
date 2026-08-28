'use client'

import { useState, useRef, useEffect, useCallback, useMemo } from 'react'
import { LayoutWrapper } from '@/components/layout-wrapper'
import { Send, Trash2, Bot, User, Loader2, Plus, MessageSquare, ChevronLeft, ChevronRight } from 'lucide-react'
import ReactMarkdown from 'react-markdown'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

interface Conversation {
  id: string
  title: string
  messages: Message[]
  createdAt: string
  updatedAt: string
  backendConversationId?: string | null
}

const STORAGE_KEY = 'assistantConversations'
const ACTIVE_KEY = 'assistantActiveConversation'

function getInitialMessage(): Message {
  return {
    id: 'welcome-' + Date.now(),
    role: 'assistant',
    content: `Hello! I'm your AI code security assistant. I can help you understand security issues, explain vulnerabilities, suggest fixes, and answer questions about your code analysis. How can I assist you today?`,
    timestamp: new Date().toISOString(),
  }
}

function generateTitle(firstMessage: string): string {
  const cleaned = firstMessage.trim().replace(/\s+/g, ' ')
  if (cleaned.length <= 48) return cleaned || 'New Chat'
  return cleaned.slice(0, 48).trimEnd() + '…'
}

function loadConversations(): Conversation[] {
  if (typeof window === 'undefined') return []
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (!stored) return []
    return JSON.parse(stored)
  } catch {
    return []
  }
}

function loadActiveId(): string | null {
  if (typeof window === 'undefined') return null
  try {
    return localStorage.getItem(ACTIVE_KEY)
  } catch {
    return null
  }
}

function saveState(
  conversations: Conversation[],
  messages: Message[],
  activeConversationId: string | null
) {
  if (typeof window === 'undefined') return
  try {
    if (activeConversationId) {
      const synced = conversations.map((c) =>
        c.id === activeConversationId
          ? { ...c, messages, updatedAt: new Date().toISOString() }
          : c
      )
      localStorage.setItem(STORAGE_KEY, JSON.stringify(synced))
      localStorage.setItem(ACTIVE_KEY, activeConversationId)
    }
  } catch {
    // Ignore storage errors (e.g. private mode)
  }
}

export default function AssistantPage() {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [historyCollapsed, setHistoryCollapsed] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const initializedRef = useRef(false)
  const activeConversationIdRef = useRef<string | null>(null)
  const messagesRef = useRef<Message[]>([])
  const stateRef = useRef({ conversations, messages, activeConversationId })

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  // Initial load from localStorage (client-only)
  useEffect(() => {
    if (initializedRef.current) return
    initializedRef.current = true

    const storedConversations = loadConversations()
    setConversations(storedConversations)

    const activeId = loadActiveId()

    if (activeId) {
      const found = storedConversations.find((c) => c.id === activeId)
      if (found) {
        setActiveConversationId(activeId)
        setMessages(found.messages)
        return
      }
    }

    // No existing conversation: create a fresh one
    const fresh: Conversation = {
      id: 'conv-' + Date.now(),
      title: 'New Chat',
      messages: [getInitialMessage()],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    }
    const next = [...storedConversations, fresh]
    setConversations(next)
    setActiveConversationId(fresh.id)
    setMessages(fresh.messages)
  }, [])

  // Keep refs synced with state
  useEffect(() => {
    activeConversationIdRef.current = activeConversationId
  }, [activeConversationId])

  useEffect(() => {
    messagesRef.current = messages
  }, [messages])

  // Keep a ref with the latest state so we can save it on unmount/pagehide
  useEffect(() => {
    stateRef.current = { conversations, messages, activeConversationId }
  }, [conversations, messages, activeConversationId])

  // Save state on unmount (navigating away) and on pagehide (refresh/close)
  useEffect(() => {
    const handlePageHide = () => {
      const { conversations, messages, activeConversationId } = stateRef.current
      saveState(conversations, messages, activeConversationId)
    }
    window.addEventListener('pagehide', handlePageHide)
    return () => {
      window.removeEventListener('pagehide', handlePageHide)
      // Save on unmount (SPA navigation away from this page)
      const { conversations, messages, activeConversationId } = stateRef.current
      saveState(conversations, messages, activeConversationId)
    }
  }, [])

  // Keep the conversations state in sync with the active conversation's messages.
  // This ensures the in-memory conversations list always reflects the latest
  // messages, so switching chats or navigating away/back restores the correct
  // history instead of a stale snapshot.
  useEffect(() => {
    if (!initializedRef.current) return
    if (!activeConversationId) return
    setConversations((prev) =>
      prev.map((c) =>
        c.id === activeConversationId
          ? { ...c, messages, updatedAt: new Date().toISOString() }
          : c
      )
    )
  }, [messages, activeConversationId])

  // Persist conversations to localStorage whenever they change
  useEffect(() => {
    if (!initializedRef.current) return
    if (!activeConversationId) return

    const current = conversations.find((c) => c.id === activeConversationId)
    if (!current) return

    const synced = conversations.map((c) =>
      c.id === activeConversationId ? { ...c, messages, updatedAt: new Date().toISOString() } : c
    )
    localStorage.setItem(STORAGE_KEY, JSON.stringify(synced))
  }, [messages, conversations, activeConversationId])

  // Persist active conversation id
  useEffect(() => {
    if (!initializedRef.current) return
    if (activeConversationId) {
      localStorage.setItem(ACTIVE_KEY, activeConversationId)
    }
  }, [activeConversationId])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    // Capture the target conversation ID at send time to prevent
    // race conditions when switching chats while a request is in flight.
    const targetConversationId = activeConversationIdRef.current
    if (!targetConversationId) return

    const userMessage: Message = {
      id: 'msg-' + Date.now(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date().toISOString(),
    }

    const updatedMessages = [...messagesRef.current, userMessage]
    setMessages(updatedMessages)
    setInput('')
    setIsLoading(true)

    // Update conversation title based on first user message
    const isFirstUserMessage = !messages.some((m) => m.role === 'user')
    if (isFirstUserMessage) {
      const title = generateTitle(userMessage.content)
      setConversations((prev) =>
        prev.map((c) => (c.id === activeConversationId ? { ...c, title } : c))
      )
    }

    // Only commit assistant responses to the correct conversation.
    // Defined at this scope so both try and catch blocks can use it.
    const commitMessage = (newMsg: Message) => {
      if (activeConversationIdRef.current === targetConversationId) {
        setMessages((prev) => [...prev, newMsg])
      } else {
        setConversations((prev) =>
          prev.map((c) =>
            c.id === targetConversationId
              ? { ...c, messages: [...c.messages, newMsg], updatedAt: new Date().toISOString() }
              : c
          )
        )
      }
    }

    try {
      const latestReport = localStorage.getItem('latestReport')
      const reportContext = latestReport ? JSON.parse(latestReport) : null

      // Use the conversation's backend conversation_id if we have one
      const activeConv = conversations.find((c) => c.id === activeConversationId)

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/assistant`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage.content,
          report_context: reportContext,
          conversation_id: activeConv?.backendConversationId || null,
          assistant_detail_level: 'concise',
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to get response from assistant')
      }

      const data = await response.json()

      // If backend returned a conversation_id, persist it on the frontend conversation
      if (data.conversation_id && activeConv) {
        setConversations((prev) =>
          prev.map((c) =>
            c.id === activeConversationId ? { ...c, backendConversationId: data.conversation_id } : c
          )
        )
      }

      const assistantMessage: Message = {
        id: 'msg-' + (Date.now() + 1),
        role: 'assistant',
        content: data.answer,
        timestamp: new Date().toISOString(),
      }

      commitMessage(assistantMessage)
    } catch (error) {
      console.error('Error calling assistant:', error)

      const errorMessage: Message = {
        id: 'msg-' + (Date.now() + 1),
        role: 'assistant',
        content:
          "I'm having trouble connecting to the server. Please make sure the backend is running and try again.",
        timestamp: new Date().toISOString(),
      }

      commitMessage(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  const handleNewChat = useCallback(() => {
    const fresh: Conversation = {
      id: 'conv-' + Date.now(),
      title: 'New Chat',
      messages: [getInitialMessage()],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    }

    setConversations((prev) => [...prev, fresh])
    setActiveConversationId(fresh.id)
    setMessages(fresh.messages)
    setInput('')
  }, [])

  const handleSelectConversation = useCallback(
    (id: string) => {
      const found = conversations.find((c) => c.id === id)
      if (!found) return
      setActiveConversationId(id)
      setMessages(found.messages)
      setInput('')
    },
    [conversations]
  )

  const handleDeleteConversation = useCallback(
    (id: string) => {
      const remaining = conversations.filter((c) => c.id !== id)
      setConversations(remaining)

      if (id === activeConversationId) {
        if (remaining.length > 0) {
          const next = remaining[remaining.length - 1]
          setActiveConversationId(next.id)
          setMessages(next.messages)
        } else {
          const fresh: Conversation = {
            id: 'conv-' + Date.now(),
            title: 'New Chat',
            messages: [getInitialMessage()],
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
          }
          setConversations([fresh])
          setActiveConversationId(fresh.id)
          setMessages(fresh.messages)
        }
      }
    },
    [conversations, activeConversationId]
  )

  const handleClearChat = useCallback(() => {
    const greeting = getInitialMessage()
    setMessages([greeting])
    setConversations((prev) =>
      prev.map((c) =>
        c.id === activeConversationId ? { ...c, messages: [greeting], title: 'New Chat' } : c
      )
    )
  }, [activeConversationId])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <LayoutWrapper>
      <div className="flex h-[calc(100dvh-56px)] min-h-0">
        {/* Internal Chat History Sidebar */}
        <div
          className={`flex flex-col border-r border-border bg-card transition-all duration-300 ${
            historyCollapsed ? 'w-12' : 'w-64'
          }`}
        >
          <div className="p-3">
            {!historyCollapsed ? (
              <button
                onClick={handleNewChat}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
              >
                <Plus className="h-4 w-4" />
                New Chat
              </button>
            ) : (
              <button
                onClick={handleNewChat}
                className="flex w-full items-center justify-center rounded-lg bg-primary p-2 text-primary-foreground hover:bg-primary/90 transition-colors"
                title="New Chat"
              >
                <Plus className="h-4 w-4" />
              </button>
            )}
          </div>

          {!historyCollapsed && (
            <div className="flex-1 overflow-y-auto px-3 pb-3 space-y-1">
              {conversations.length === 0 && (
                <p className="text-sm text-muted-foreground px-3 py-4">
                  No conversations yet.
                </p>
              )}

              {conversations.map((conv) => (
                <div
                  key={conv.id}
                  className={`group relative rounded-lg border transition-colors cursor-pointer ${
                    conv.id === activeConversationId
                      ? 'bg-primary/10 border-primary/30'
                      : 'border-transparent hover:bg-background/50'
                  }`}
                  onClick={() => handleSelectConversation(conv.id)}
                >
                  <div className="flex items-center gap-2 px-3 py-2.5">
                    <MessageSquare className="h-4 w-4 flex-shrink-0 text-muted-foreground" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-foreground truncate">{conv.title}</p>
                      <p className="text-xs text-muted-foreground truncate">
                        {conv.messages.length} messages
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDeleteConversation(conv.id)
                    }}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded hover:bg-red-500/10 text-muted-foreground hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                    title="Delete conversation"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              ))}
            </div>
          )}

          <div className="border-t border-border p-2">
            <button
              onClick={() => setHistoryCollapsed(!historyCollapsed)}
              className="flex w-full items-center justify-center rounded-lg p-2 text-muted-foreground hover:bg-background/50 transition-colors"
            >
              {historyCollapsed ? (
                <ChevronRight className="h-4 w-4" />
              ) : (
                <ChevronLeft className="h-4 w-4" />
              )}
            </button>
          </div>
        </div>

        {/* Main Chat Area */}
        <div className="flex flex-col flex-1 min-w-0">
          {/* Header */}
          <div className="border-b border-border bg-card px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="rounded-lg bg-primary/10 p-2">
                  <Bot className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <h1 className="text-xl font-semibold text-foreground">AI Assistant</h1>
                  <p className="text-sm text-muted-foreground">
                    Get help with code security, vulnerabilities, and best practices
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => {
                    if (confirm('Clear all assistant conversations? This cannot be undone.')) {
                      localStorage.removeItem('assistantConversations')
                      localStorage.removeItem('assistantActiveConversation')
                      const fresh: Conversation = {
                        id: 'conv-' + Date.now(),
                        title: 'New Chat',
                        messages: [getInitialMessage()],
                        createdAt: new Date().toISOString(),
                        updatedAt: new Date().toISOString(),
                      }
                      setConversations([fresh])
                      setActiveConversationId(fresh.id)
                      setMessages(fresh.messages)
                    }
                  }}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg border border-border hover:bg-background transition-colors text-sm text-foreground"
                >
                  <Trash2 className="h-4 w-4" />
                  Clear All
                </button>
                <button
                  onClick={handleClearChat}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg border border-border hover:bg-background transition-colors text-sm text-foreground"
                >
                  <Trash2 className="h-4 w-4" />
                  Clear Chat
                </button>
              </div>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-auto p-6 space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-3 ${
                  message.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                {message.role === 'assistant' && (
                  <div className="rounded-lg bg-primary/10 p-2 flex-shrink-0">
                    <Bot className="h-5 w-5 text-primary" />
                  </div>
                )}
                <div
                  className={`max-w-2xl rounded-lg px-4 py-3 overflow-hidden ${
                    message.role === 'user'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-card border border-border'
                  }`}
                >
                  {message.role === 'assistant' ? (
                    <div className="text-sm leading-relaxed prose prose-sm dark:prose-invert max-w-none prose-pre:bg-background prose-pre:border prose-pre:border-border prose-pre:rounded-lg prose-pre:p-4 prose-code:bg-background prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:before:content-none prose-code:after:content-none whitespace-pre-wrap">
                      <ReactMarkdown>{message.content}</ReactMarkdown>
                    </div>
                  ) : (
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">
                      {message.content}
                    </p>
                  )}
                  <p className="text-xs mt-2 opacity-70">
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </p>
                </div>
                {message.role === 'user' && (
                  <div className="rounded-lg bg-primary/20 p-2 flex-shrink-0">
                    <User className="h-5 w-5 text-primary-foreground" />
                  </div>
                )}
              </div>
            ))}
            {isLoading && (
              <div className="flex gap-3 justify-start">
                <div className="rounded-lg bg-primary/10 p-2 flex-shrink-0">
                  <Bot className="h-5 w-5 text-primary" />
                </div>
                <div className="rounded-lg bg-card border border-border px-4 py-3">
                  <Loader2 className="h-5 w-5 text-muted-foreground animate-spin" />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="border-t border-border bg-card p-4">
            <div className="flex gap-3">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about security issues, code quality, or request explanations..."
                className="flex-1 rounded-lg border border-border bg-background px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground resize-none focus:outline-none focus:ring-2 focus:ring-primary/50"
                rows={3}
                disabled={isLoading}
              />
              <button
                onClick={handleSend}
                disabled={!input.trim() || isLoading}
                className="self-end px-6 py-3 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
              >
                {isLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
                Send
              </button>
            </div>
          </div>
        </div>
      </div>
    </LayoutWrapper>
  )
}