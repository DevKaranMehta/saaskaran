'use client'

interface DashboardPreviewProps {
  extensions: string[]
}

const EXTENSION_ICONS: Record<string, string> = {
  contacts: '👥', crm: '📊', invoicing: '💳', helpdesk: '🎧',
  appointments: '📅', roles: '🔑', courses: '📚', tasks: '✅',
}

export default function DashboardPreview({ extensions }: DashboardPreviewProps) {
  return (
    <div className="flex-1 bg-slate-950 overflow-hidden flex flex-col">
      {/* Fake browser chrome */}
      <div className="h-8 bg-slate-800 flex items-center px-3 gap-2 border-b border-slate-700">
        <div className="flex gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-slate-600" />
          <div className="w-2.5 h-2.5 rounded-full bg-slate-600" />
          <div className="w-2.5 h-2.5 rounded-full bg-slate-600" />
        </div>
        <div className="flex-1 mx-3 bg-slate-700 rounded-md h-5 flex items-center px-2">
          <span className="text-xs text-slate-400">your-saas.factory.app</span>
        </div>
      </div>

      {/* Preview content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Mini sidebar */}
        <div className="w-36 bg-slate-900 border-r border-slate-800 flex flex-col">
          <div className="p-3 border-b border-slate-800">
            <div className="text-xs font-bold text-white">My SaaS</div>
            <div className="text-[10px] text-slate-500">workspace</div>
          </div>
          <nav className="p-2 space-y-0.5 flex-1">
            <div className="flex items-center gap-2 px-2 py-1.5 rounded bg-indigo-600 text-white text-xs">
              <span>⊞</span> Dashboard
            </div>
            {extensions.map((ext) => (
              <div key={ext} className="flex items-center gap-2 px-2 py-1.5 rounded text-slate-400 text-xs hover:bg-slate-800 hover:text-white transition cursor-pointer">
                <span>{EXTENSION_ICONS[ext] || '⬡'}</span>
                <span className="capitalize">{ext}</span>
              </div>
            ))}
            {extensions.length === 0 && (
              <div className="px-2 py-4 text-[10px] text-slate-600 text-center">
                Extensions will<br/>appear here
              </div>
            )}
          </nav>
        </div>

        {/* Main area */}
        <div className="flex-1 p-4 overflow-y-auto bg-slate-950">
          {extensions.length === 0 ? (
            <div className="h-full flex items-center justify-center">
              <div className="text-center">
                <div className="text-4xl mb-3">✦</div>
                <p className="text-sm text-slate-500 font-medium">Your SaaS preview</p>
                <p className="text-xs text-slate-600 mt-1">Chat with AI to add features →</p>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Stats row */}
              <div className="grid grid-cols-2 gap-3">
                {extensions.slice(0, 4).map((ext) => (
                  <div key={ext} className="bg-slate-800 rounded-lg p-3 border border-slate-700">
                    <div className="text-lg mb-1">{EXTENSION_ICONS[ext] || '⬡'}</div>
                    <div className="text-xs font-semibold text-white capitalize">{ext}</div>
                    <div className="text-[10px] text-slate-500">Active</div>
                  </div>
                ))}
              </div>

              {/* Activity feed */}
              <div className="bg-slate-800 rounded-lg p-3 border border-slate-700">
                <div className="text-xs font-semibold text-white mb-2">Recent Activity</div>
                {extensions.map((ext) => (
                  <div key={ext} className="flex items-center gap-2 py-1.5 border-b border-slate-700 last:border-0">
                    <div className="w-4 h-4 rounded bg-indigo-600/20 flex items-center justify-center text-[8px]">
                      {EXTENSION_ICONS[ext] || '⬡'}
                    </div>
                    <span className="text-[10px] text-slate-400 capitalize">{ext} extension activated</span>
                    <span className="ml-auto text-[9px] text-slate-600">now</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
