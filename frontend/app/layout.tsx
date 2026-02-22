import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'SaaS Factory — Build any SaaS with AI',
  description: 'Pick a template, activate extensions, let AI build your features. Production-ready SaaS in minutes.',
  openGraph: {
    title: 'SaaS Factory',
    description: 'Build production-ready SaaS products with AI',
    url: 'https://factory.supportbox.cloud',
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>{children}</body>
    </html>
  )
}
