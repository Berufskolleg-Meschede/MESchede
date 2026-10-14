import type { Metadata } from 'next'
import './globals.css'
import { Sidebar } from '@/components/sidebar'
import { OrderPreviewNotice } from '@/components/order-preview-notice'

export const metadata: Metadata = {
  title: 'MESchede MES',
  description: 'Manufacturing Execution System — Berufskolleg Meschede',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const preview = process.env.NODE_ENV === 'development' && process.env.MES_PREVIEW_MODE === 'true'
  return (
    <html
      lang="de"
      className="dark"
    >
      <body className="antialiased">
        <div className="flex min-h-screen flex-col bg-background md:h-screen md:flex-row">
          <Sidebar />
          <main className="min-w-0 flex-1 md:overflow-auto">{preview && <OrderPreviewNotice />}{children}</main>
        </div>
      </body>
    </html>
  )
}
