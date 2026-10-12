import type { Metadata } from 'next'
import './globals.css'
import { Sidebar } from '@/components/sidebar'

export const metadata: Metadata = {
  title: 'MESchede MES',
  description: 'Manufacturing Execution System — Berufskolleg Meschede',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="de"
      className="dark"
    >
      <body className="antialiased">
        <div className="flex min-h-screen flex-col bg-background md:h-screen md:flex-row">
          <Sidebar />
          <main className="min-w-0 flex-1 md:overflow-auto">{children}</main>
        </div>
      </body>
    </html>
  )
}
