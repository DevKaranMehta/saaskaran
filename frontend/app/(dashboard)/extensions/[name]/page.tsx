'use client'

import Link from 'next/link'
import { useState, useEffect } from 'react'
import TodoListPage from '@/components/extensions/TodoListPage'
import KanbanBoardPage from '@/components/extensions/KanbanBoardPage'
import FormBuilderPage from '@/components/extensions/FormBuilderPage'
import LiveChatPage from '@/components/extensions/LiveChatPage'
import GenericExtensionPage from '@/components/extensions/GenericExtensionPage'

// Hardcoded components for extensions with custom UIs
const EXTENSION_PAGES: Record<string, React.ComponentType> = {
  todo_list: TodoListPage,
  kanban_board: KanbanBoardPage,
  form_builder: FormBuilderPage,
  live_chat: LiveChatPage,
}

function DynamicOrFallback({ name }: { name: string }) {
  const [hasSpec, setHasSpec] = useState<boolean | null>(null)

  useEffect(() => {
    const token = localStorage.getItem('token')
    fetch(`/api/v1/extensions/${name}/ui-spec`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    }).then(r => setHasSpec(r.ok)).catch(() => setHasSpec(false))
  }, [name])

  if (hasSpec === null) return <div className="p-8 text-slate-500 text-sm">Loading…</div>

  if (hasSpec) return <GenericExtensionPage extensionName={name} />

  // True fallback — no spec, no custom component
  return (
    <div className="flex flex-col items-center justify-center h-full text-center p-8">
      <div className="text-5xl mb-4">⬡</div>
      <h2 className="text-xl font-semibold text-white mb-2 capitalize">{name.replace(/_/g, ' ')}</h2>
      <p className="text-slate-400 mb-6 max-w-md">
        This extension has a backend API but no UI page yet. Go to the{' '}
        <Link href="/ai" className="text-indigo-400 hover:text-indigo-300">AI Builder</Link>
        , select this extension in the dropdown, and ask it to add a UI.
      </p>
      <div className="bg-slate-800 rounded-xl p-4 text-left text-sm font-mono text-slate-300 max-w-lg w-full mb-6">
        <p className="text-slate-500 mb-2"># Base API path</p>
        <p className="text-indigo-400">GET /api/v1/{name.replace(/_/g, '-')}/...</p>
      </div>
      <Link href="/extensions" className="text-sm text-slate-500 hover:text-white transition">
        ← Back to Extensions
      </Link>
    </div>
  )
}

export default function ExtensionPage({ params }: { params: { name: string } }) {
  const { name } = params
  const PageComponent = EXTENSION_PAGES[name]

  if (PageComponent) return <PageComponent />

  return <DynamicOrFallback name={name} />
}
