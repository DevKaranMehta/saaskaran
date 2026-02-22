'use client'

import AiChat from '@/components/ai-chat/AiChat'

export default function AiBuilderPage() {
  return (
    <div className="flex flex-col h-full overflow-hidden">
      <div className="h-12 flex items-center px-4 border-b border-slate-800 bg-slate-900 gap-3 flex-shrink-0">
        <div className="w-6 h-6 rounded-md bg-gradient-to-br from-indigo-500 to-cyan-500 flex items-center justify-center text-white text-xs font-bold">AI</div>
        <span className="text-sm font-semibold text-white">AI Extension Builder</span>
        <span className="text-xs text-slate-400 ml-auto">Powered by Claude</span>
      </div>
      <AiChat />
    </div>
  )
}
