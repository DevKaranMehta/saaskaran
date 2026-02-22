'use client'

import { useEffect, useLayoutEffect, useRef, useState, useCallback } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import CodeBlock from './CodeBlock'

// ── Message types ────────────────────────────────────────────────

interface TextMessage {
  role: 'user' | 'assistant'
  content: string
  isStreaming?: boolean
}

interface StatusMessage {
  role: 'status'
  content: string
}

interface ThinkingMessage {
  role: 'thinking'
  content: string
  collapsed?: boolean
}

interface ToolMessage {
  role: 'tool'
  tool: string
  input: string
  output?: string
}

type Message = TextMessage | StatusMessage | ThinkingMessage | ToolMessage

interface AiChatProps {
  onExtensionInstalled?: (name: string) => void
}

interface ExtensionInfo {
  name: string
  active: boolean
}

// ── Storage helpers (per-mode history) ──────────────────────────

const SELECTED_EXT_KEY = 'ai_selected_ext_v1'
const HISTORY_KEY_PREFIX = 'ai_chat_v3__'
const PAGE_SIZE = 20  // messages shown per page

const WELCOME_MSG: TextMessage = {
  role: 'assistant',
  content: "👋 Hi! I'm your AI extension builder. Tell me what feature you want to add to your SaaS — I'll ask a few questions and then generate the complete code.\n\nWhat would you like to build?",
}

const STARTER_PROMPTS = [
  'Build me a task management system',
  'I need a customer portal with tickets',
  'Create an invoicing and billing module',
  'I want a blog with categories and tags',
  'Build an appointment booking system',
]

function getHistoryKey(ext: string) {
  return `${HISTORY_KEY_PREFIX}${ext || 'new'}`
}

function loadHistoryFor(ext: string): Message[] {
  if (typeof window === 'undefined') return ext ? [] : [WELCOME_MSG]
  try {
    const raw = localStorage.getItem(getHistoryKey(ext))
    if (raw) {
      const parsed = JSON.parse(raw) as Message[]
      return parsed.length ? parsed : (ext ? [] : [WELCOME_MSG])
    }
  } catch {}
  return ext ? [] : [WELCOME_MSG]
}

function saveHistory(ext: string, messages: Message[]) {
  const toSave = messages.filter(m => {
    if (m.role === 'assistant') return !(m as TextMessage).isStreaming
    return true
  })
  localStorage.setItem(getHistoryKey(ext), JSON.stringify(toSave))
}

function loadPersistedExt(): string {
  if (typeof window === 'undefined') return ''
  return localStorage.getItem(SELECTED_EXT_KEY) || ''
}

function getWsUrl() {
  if (typeof window === 'undefined') return 'ws://localhost:8000'
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${proto}//${window.location.host}`
}

// ── Sub-components ───────────────────────────────────────────────

function StatusLine({ content }: { content: string }) {
  return (
    <div className="flex items-center gap-2 py-1 px-3 text-xs text-slate-500 font-mono">
      <span className="w-1 h-1 rounded-full bg-slate-600 flex-shrink-0" />
      {content}
    </div>
  )
}

function ThinkingBlock({ content }: { content: string }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="my-1 rounded-lg border border-slate-700/50 overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-2 px-3 py-2 text-xs text-slate-500 hover:text-slate-400 bg-slate-900/50 transition text-left"
      >
        <span className="text-indigo-500/70">💭</span>
        <span className="flex-1 font-mono">Thinking{open ? '' : '...'}</span>
        <span className="text-slate-600">{open ? '▲' : '▼'}</span>
      </button>
      {open && (
        <div className="px-3 py-2 text-xs text-slate-500 font-mono whitespace-pre-wrap border-t border-slate-700/50 bg-slate-900/30 max-h-48 overflow-y-auto leading-relaxed">
          {content}
        </div>
      )}
    </div>
  )
}

function ToolBlock({ tool, input, output }: { tool: string; input: string; output?: string }) {
  const [open, setOpen] = useState(false)
  const icons: Record<string, string> = {
    Bash: '⚡', Read: '📄', Write: '📝', Edit: '✏️',
    Glob: '🔍', Grep: '🔎', Task: '🤖', WebFetch: '🌐', WebSearch: '🌐',
  }
  const icon = icons[tool] || '🔧'

  const isFileWrite = tool === 'Write' && input.includes('extensions/')
  const isDone = output?.startsWith('✅')

  return (
    <div className={`my-1 rounded-lg overflow-hidden ${
      isFileWrite
        ? 'border border-indigo-500/30 bg-indigo-950/30'
        : 'border border-slate-700/40'
    }`}>
      <button
        onClick={() => setOpen(!open)}
        className={`w-full flex items-center gap-2 px-3 py-2 text-xs transition text-left ${
          isFileWrite
            ? 'bg-indigo-900/20 hover:bg-indigo-900/40'
            : 'bg-slate-800/60 hover:bg-slate-800'
        }`}
      >
        <span>{icon}</span>
        <span className={`font-mono font-medium ${isFileWrite ? 'text-indigo-300' : 'text-slate-400'}`}>
          {isFileWrite ? input : tool}
        </span>
        {!isFileWrite && <span className="text-slate-600 truncate flex-1">{input}</span>}
        {isDone && <span className="text-green-400 flex-shrink-0 ml-auto text-xs">{output}</span>}
        {output && !isDone && <span className="text-slate-600 flex-shrink-0">{open ? '▲' : '▼'}</span>}
      </button>
      {open && output && !isDone && (
        <div className="px-3 py-2 text-xs font-mono text-slate-500 border-t border-slate-700/40 bg-slate-900/40 whitespace-pre-wrap max-h-32 overflow-y-auto">
          {output}
        </div>
      )}
    </div>
  )
}

function AssistantMessage({ content, isStreaming }: { content: string; isStreaming?: boolean }) {
  return (
    <div className={`prose prose-invert prose-sm max-w-none text-slate-100 ${isStreaming ? 'ai-cursor' : ''}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          code({ className, children }) {
            const match = /language-(\w+)/.exec(className || '')
            const lang = match ? match[1] : ''
            const isBlock = String(children).includes('\n')
            if (isBlock) return <CodeBlock language={lang} code={String(children)} />
            return <code className="bg-slate-700 px-1.5 py-0.5 rounded text-xs font-mono">{children}</code>
          },
          p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
          ul: ({ children }) => <ul className="list-disc list-inside space-y-1 mb-2">{children}</ul>,
          ol: ({ children }) => <ol className="list-decimal list-inside space-y-1 mb-2">{children}</ol>,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}

// ── Main component ───────────────────────────────────────────────

export default function AiChat({ onExtensionInstalled }: AiChatProps) {
  // Initialise from persisted selection so refresh restores correct mode + history
  const [selectedExt, setSelectedExt] = useState<string>(loadPersistedExt)
  const [messages, setMessages] = useState<Message[]>(() => loadHistoryFor(loadPersistedExt()))

  const [input, setInput] = useState('')
  const [isConnected, setIsConnected] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)
  const [extensions, setExtensions] = useState<ExtensionInfo[]>([])

  // Pagination: show the last PAGE_SIZE messages; scroll to top loads more
  const [displayedCount, setDisplayedCount] = useState(PAGE_SIZE)
  const [isSaving, setIsSaving] = useState(false)
  // Track whether we just loaded more messages (to restore scroll pos)
  const loadingMoreRef = useRef(false)
  const prevScrollHeightRef = useRef(0)

  const wsRef = useRef<WebSocket | null>(null)
  const scrollContainerRef = useRef<HTMLDivElement>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // ── Persist history for the CURRENT mode ──────────────────────
  useEffect(() => {
    saveHistory(selectedExt, messages)
  }, [messages, selectedExt])

  // ── Auto-scroll to bottom on new messages (not when loading older) ──
  useEffect(() => {
    if (!loadingMoreRef.current) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages])

  // ── Restore scroll position after loading older messages ──────
  useLayoutEffect(() => {
    if (loadingMoreRef.current && scrollContainerRef.current) {
      const el = scrollContainerRef.current
      el.scrollTop = el.scrollHeight - prevScrollHeightRef.current
      loadingMoreRef.current = false
    }
  }, [displayedCount])

  // ── Switch mode (create new / existing extension) ──────────────
  const switchMode = useCallback((newExt: string) => {
    localStorage.setItem(SELECTED_EXT_KEY, newExt)
    setSelectedExt(newExt)
    setMessages(loadHistoryFor(newExt))
    setDisplayedCount(PAGE_SIZE)
    // Scroll to bottom after the mode switch renders
    setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'auto' }), 50)
  }, [])

  // ── Clear chat for the current mode ───────────────────────────
  const clearChat = () => {
    localStorage.removeItem(getHistoryKey(selectedExt))
    setMessages(selectedExt ? [] : [WELCOME_MSG])
    setDisplayedCount(PAGE_SIZE)
  }

  // ── Detect extension name from chat history ────────────────────
  function detectExtensionName(msgs: Message[]): string {
    for (const msg of [...msgs].reverse()) {
      // Check status messages: "✅ Extension 'name' registered!"
      if (msg.role === 'status') {
        const m = (msg as StatusMessage).content.match(/Extension '([^']+)' registered/)
        if (m) return m[1]
      }
      // Check assistant messages: "✅ Extension **name** generated"
      if (msg.role === 'assistant') {
        const m = (msg as TextMessage).content?.match(/✅ Extension \*\*([^*]+)\*\*/)
        if (m) return m[1]
      }
    }
    return selectedExt || ''
  }

  // ── Save current session and start fresh ──────────────────────
  const startNewExtension = async () => {
    const userMsgs = messages.filter(m => m.role === 'user' || m.role === 'assistant')
    if (userMsgs.length === 0) {
      // Nothing to save — just reset
      switchMode('')
      return
    }

    setIsSaving(true)
    const extName = detectExtensionName(messages)
    const token = localStorage.getItem('token')

    try {
      await fetch('/api/v1/ai/save-session', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          messages: userMsgs.map(m => ({ role: (m as TextMessage).role, content: (m as TextMessage).content })),
          extension_name: extName,
        }),
      })
    } catch {
      // Don't block the user if save fails
    }

    setIsSaving(false)
    // Switch to create-new mode with a fresh chat
    localStorage.setItem(SELECTED_EXT_KEY, '')
    setSelectedExt('')
    localStorage.removeItem(getHistoryKey(''))
    setMessages([WELCOME_MSG])
    setDisplayedCount(PAGE_SIZE)
    setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'auto' }), 50)
  }

  // ── Scroll handler: load more messages when user scrolls to top ──
  const handleScroll = useCallback(() => {
    const el = scrollContainerRef.current
    if (!el || loadingMoreRef.current) return
    if (el.scrollTop <= 60 && displayedCount < messages.length) {
      prevScrollHeightRef.current = el.scrollHeight
      loadingMoreRef.current = true
      setDisplayedCount(prev => Math.min(prev + PAGE_SIZE, messages.length))
    }
  }, [displayedCount, messages.length])

  // ── Fetch available extensions for the selector ────────────────
  useEffect(() => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null
    fetch('/api/v1/extensions/', {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
      .then(r => r.json())
      .then(d => {
        const exts: ExtensionInfo[] = (d.extensions || [])
          .filter((e: ExtensionInfo) => e.name !== 'ai_generator')
        setExtensions(exts)
      })
      .catch(() => {})
  }, [])

  // ── WebSocket connection ───────────────────────────────────────
  useEffect(() => {
    function connect() {
      const token = localStorage.getItem('token')
      const ws = new WebSocket(
        `${getWsUrl()}/api/v1/ai/ws/generate${token ? `?token=${token}` : ''}`
      )

      ws.onopen = () => setIsConnected(true)
      ws.onclose = () => {
        setIsConnected(false)
        setTimeout(connect, 3000)
      }

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data)

        // Reset the inactivity timeout on every server message
        ;(ws as WebSocket & { _resetTimeout?: () => void })._resetTimeout?.()

        if (data.type === 'status') {
          setMessages(prev => [...prev, { role: 'status', content: data.content } as StatusMessage])

        } else if (data.type === 'thinking') {
          setMessages(prev => [...prev, { role: 'thinking', content: data.content } as ThinkingMessage])

        } else if (data.type === 'tool_use') {
          setMessages(prev => [...prev, {
            role: 'tool',
            tool: data.tool,
            input: data.input || '',
          } as ToolMessage])

        } else if (data.type === 'tool_result') {
          setMessages(prev => {
            const last = prev[prev.length - 1]
            if (last?.role === 'tool' && (last as ToolMessage).tool === data.tool) {
              return [...prev.slice(0, -1), { ...last, output: data.output }]
            }
            return prev
          })

        } else if (data.type === 'token') {
          setMessages(prev => {
            const last = prev[prev.length - 1]
            if (last?.role === 'assistant' && (last as TextMessage).isStreaming) {
              return [
                ...prev.slice(0, -1),
                { ...last, content: (last as TextMessage).content + data.content },
              ]
            }
            return [...prev, { role: 'assistant', content: data.content, isStreaming: true } as TextMessage]
          })

        } else if (data.type === 'done') {
          if (timeoutRef.current) { clearTimeout(timeoutRef.current); timeoutRef.current = null }
          setMessages(prev => {
            const last = prev[prev.length - 1]
            if (last?.role === 'assistant' && (last as TextMessage).isStreaming) {
              return [...prev.slice(0, -1), { ...last, isStreaming: false }]
            }
            return prev
          })
          setIsGenerating(false)

        } else if (data.type === 'cancelled') {
          if (timeoutRef.current) { clearTimeout(timeoutRef.current); timeoutRef.current = null }
          setIsGenerating(false)

        } else if (data.type === 'error') {
          if (timeoutRef.current) { clearTimeout(timeoutRef.current); timeoutRef.current = null }
          setMessages(prev => [
            ...prev,
            { role: 'assistant', content: `❌ ${data.message}` } as TextMessage,
          ])
          setIsGenerating(false)
        }
      }

      wsRef.current = ws
    }

    connect()
    return () => wsRef.current?.close()
  }, [])

  // ── Send a message ─────────────────────────────────────────────
  const send = useCallback((text: string) => {
    if (!text.trim() || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return

    const userMessage: TextMessage = { role: 'user', content: text }
    // Use full messages array (not just displayed slice) for history
    const allMessages = messages
      .filter((m): m is TextMessage => m.role === 'user' || m.role === 'assistant')
      .map(({ role, content }) => ({ role, content }))

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsGenerating(true)

    // Inactivity timeout: reset on every server message, fires if silent for 3 min
    const resetInactivityTimeout = () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current)
      timeoutRef.current = setTimeout(() => {
        setIsGenerating(false)
        timeoutRef.current = null
        setMessages(prev => [
          ...prev,
          { role: 'assistant', content: '⏱️ No response for 15 minutes. Please try again.' } as TextMessage,
        ])
      }, 900_000)
    }
    resetInactivityTimeout()
    ;(wsRef.current as WebSocket & { _resetTimeout?: () => void })._resetTimeout = resetInactivityTimeout

    wsRef.current.send(JSON.stringify({
      messages: [...allMessages, { role: 'user', content: text }],
      template: 'blank',
      active_extensions: [],
      selected_extension: selectedExt || null,
    }))
  }, [messages, selectedExt])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send(input)
    }
  }

  // ── Derived display state ──────────────────────────────────────
  const displayedMessages = messages.slice(-Math.min(displayedCount, messages.length))
  const hasOlderMessages = displayedCount < messages.length
  const userMessageCount = messages.filter(m => m.role === 'user').length
  // Offset for stable keys (absolute index in messages array)
  const keyOffset = messages.length - displayedMessages.length

  return (
    <div className="flex flex-col h-full bg-slate-950">
      {/* Connection status bar */}
      <div className={`flex items-center gap-2 px-4 py-1.5 text-xs border-b border-slate-800 ${isConnected ? 'text-green-400' : 'text-amber-400'}`}>
        <div className={`w-1.5 h-1.5 rounded-full ${isConnected ? 'bg-green-400' : 'bg-amber-400 animate-pulse'}`} />
        <span className="flex-1">{isConnected ? 'Connected · Claude Sonnet (subscription)' : 'Reconnecting...'}</span>
        <div className="flex items-center gap-3 ml-auto">
          <button
            onClick={startNewExtension}
            disabled={isGenerating || isSaving}
            title="Save current session and start a fresh new extension"
            className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-indigo-600/20 border border-indigo-500/40 text-indigo-300 hover:bg-indigo-600/40 transition disabled:opacity-40 disabled:cursor-not-allowed text-xs font-medium"
          >
            {isSaving ? (
              <>
                <span className="animate-spin">⟳</span>
                <span>Saving...</span>
              </>
            ) : (
              <>
                <span>✦</span>
                <span>New Extension</span>
              </>
            )}
          </button>
          <button
            onClick={clearChat}
            disabled={isGenerating}
            title={`Clear ${selectedExt ? selectedExt.replace(/_/g, ' ') : 'new extension'} chat history`}
            className="text-slate-600 hover:text-slate-400 transition disabled:opacity-40 disabled:cursor-not-allowed"
          >
            🗑
          </button>
        </div>
      </div>

      {/* Messages */}
      <div
        ref={scrollContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto p-4 space-y-1"
      >
        {/* Load-more indicator at top */}
        {hasOlderMessages && (
          <div className="flex items-center justify-center gap-2 py-2 text-xs text-slate-600 select-none">
            <span>↑</span>
            <span>Scroll up to load earlier messages ({messages.length - displayedCount} more)</span>
          </div>
        )}

        {displayedMessages.map((msg, i) => {
          const key = keyOffset + i  // stable absolute index

          if (msg.role === 'status') {
            return <StatusLine key={key} content={(msg as StatusMessage).content} />
          }
          if (msg.role === 'thinking') {
            return <ThinkingBlock key={key} content={(msg as ThinkingMessage).content} />
          }
          if (msg.role === 'tool') {
            const t = msg as ToolMessage
            return <ToolBlock key={key} tool={t.tool} input={t.input} output={t.output} />
          }

          const textMsg = msg as TextMessage
          return (
            <div key={key} className={`flex gap-3 ${textMsg.role === 'user' ? 'justify-end' : 'justify-start'} py-1`}>
              {textMsg.role === 'assistant' && (
                <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-indigo-500 to-cyan-500 flex items-center justify-center text-white text-xs font-bold flex-shrink-0 mt-0.5">AI</div>
              )}
              <div
                className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed
                  ${textMsg.role === 'user'
                    ? 'bg-indigo-600 text-white rounded-tr-sm'
                    : 'bg-slate-800/80 text-slate-100 rounded-tl-sm'
                  }`}
              >
                {textMsg.role === 'assistant'
                  ? <AssistantMessage content={textMsg.content} isStreaming={textMsg.isStreaming} />
                  : textMsg.content
                }
              </div>
              {textMsg.role === 'user' && (
                <div className="w-7 h-7 rounded-lg bg-slate-700 flex items-center justify-center text-slate-300 text-xs font-bold flex-shrink-0 mt-0.5">You</div>
              )}
            </div>
          )
        })}

        {/* Generating indicator — always visible while waiting, even when status messages show */}
        {isGenerating && !(messages[messages.length - 1]?.role === 'assistant' && (messages[messages.length - 1] as TextMessage).isStreaming) && (
          <div className="flex gap-3 py-1">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-indigo-500 to-cyan-500 flex items-center justify-center text-white text-xs font-bold">AI</div>
            <div className="bg-slate-800/80 rounded-2xl rounded-tl-sm px-4 py-3">
              <div className="flex gap-1">
                {[0, 150, 300].map(delay => (
                  <div key={delay} className="w-1.5 h-1.5 rounded-full bg-slate-500 animate-bounce" style={{ animationDelay: `${delay}ms` }} />
                ))}
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Starter prompts — only for create-new mode with no messages yet */}
      {userMessageCount === 0 && !selectedExt && (
        <div className="px-4 pb-2">
          <p className="text-xs text-slate-600 mb-2">Try asking:</p>
          <div className="flex flex-wrap gap-2">
            {STARTER_PROMPTS.map(prompt => (
              <button
                key={prompt}
                onClick={() => send(prompt)}
                className="text-xs px-3 py-1.5 rounded-full bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-white transition border border-slate-700"
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input area */}
      <div className="border-t border-slate-800">
        {/* Generating bar */}
        {isGenerating && (
          <div className="px-4 pt-2 pb-1 flex items-center gap-2">
            <div className="flex gap-1 flex-shrink-0">
              {[0, 150, 300].map(d => (
                <div key={d} className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-bounce" style={{ animationDelay: `${d}ms` }} />
              ))}
            </div>
            <span className="text-xs text-slate-500">AI is responding… send a new message to interrupt</span>
          </div>
        )}

        {/* Mode selector */}
        <div className="px-4 pt-2 pb-1 flex items-center gap-2">
          <span className="text-xs text-slate-500 flex-shrink-0">Mode:</span>
          <select
            value={selectedExt}
            onChange={e => switchMode(e.target.value)}
            className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500 transition cursor-pointer"
          >
            <option value="">✦ Create new extension</option>
            {extensions.length > 0 && (
              <optgroup label="Modify existing extension">
                {extensions.map(ext => (
                  <option key={ext.name} value={ext.name}>
                    ✏ {ext.name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                    {ext.active ? ' (active)' : ''}
                  </option>
                ))}
              </optgroup>
            )}
          </select>
          {selectedExt && (
            <span className="text-xs text-amber-400 flex-shrink-0 flex items-center gap-1">
              <span>✏</span>
              <span>Editing</span>
            </span>
          )}
        </div>

        <div className="p-4 pt-2 flex gap-3 items-end">
          <textarea
            ref={inputRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              isGenerating
                ? 'Send a new message to interrupt AI...'
                : selectedExt
                  ? `Describe changes for "${selectedExt.replace(/_/g, ' ')}"... (Enter to send)`
                  : 'Describe what you want to build... (Enter to send)'
            }
            disabled={!isConnected}
            rows={2}
            className="flex-1 bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 resize-none focus:outline-none focus:border-indigo-500 transition disabled:opacity-50"
          />
          <button
            onClick={() => send(input)}
            disabled={!input.trim() || !isConnected}
            className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center text-white hover:bg-indigo-700 transition disabled:opacity-40 disabled:cursor-not-allowed flex-shrink-0"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
        <p className="text-xs text-slate-600 px-4 pb-3 -mt-1">Shift+Enter for new line · Enter to send</p>
      </div>
    </div>
  )
}
