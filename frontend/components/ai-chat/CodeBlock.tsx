'use client'

import { useState } from 'react'
import Editor from '@monaco-editor/react'

interface CodeBlockProps {
  language: string
  code: string
}

export default function CodeBlock({ language, code }: CodeBlockProps) {
  const [copied, setCopied] = useState(false)
  const [showEditor, setShowEditor] = useState(false)

  // Extract filename from language hint (e.g. "python:extensions/auth/routes.py")
  const [lang, filename] = language.includes(':') ? language.split(':') : [language, '']

  const copy = () => {
    navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="my-3 rounded-xl overflow-hidden border border-slate-700 bg-slate-900">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-slate-800 border-b border-slate-700">
        <div className="flex items-center gap-2">
          <span className="text-xs text-indigo-400 font-mono font-semibold">{lang || 'code'}</span>
          {filename && <span className="text-xs text-slate-400 font-mono">{filename}</span>}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowEditor(!showEditor)}
            className="text-xs text-slate-400 hover:text-white transition px-2 py-1 rounded hover:bg-slate-700"
          >
            {showEditor ? 'Simple view' : 'Monaco editor'}
          </button>
          <button
            onClick={copy}
            className="text-xs text-slate-400 hover:text-white transition px-2 py-1 rounded hover:bg-slate-700"
          >
            {copied ? '✓ Copied' : 'Copy'}
          </button>
        </div>
      </div>

      {/* Code */}
      {showEditor ? (
        <Editor
          height="300px"
          language={lang || 'python'}
          value={code.trim()}
          theme="vs-dark"
          options={{
            readOnly: true,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            fontSize: 13,
            fontFamily: 'JetBrains Mono, monospace',
            padding: { top: 12, bottom: 12 },
          }}
        />
      ) : (
        <pre className="p-4 overflow-x-auto text-xs leading-relaxed text-slate-300 rounded-none bg-slate-900">
          <code>{code.trim()}</code>
        </pre>
      )}
    </div>
  )
}
