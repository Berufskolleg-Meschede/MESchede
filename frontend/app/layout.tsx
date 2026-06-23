import type { Metadata } from 'next'
import { Geist, Geist_Mono, Barlow_Condensed } from 'next/font/google'
import './globals.css'
import { Sidebar } from '@/components/sidebar'

const geistSans = Geist({ variable: '--font-geist-sans', subsets: ['latin'] })
const geistMono = Geist_Mono({ variable: '--font-geist-mono', subsets: ['latin'] })
const barlowCondensed = Barlow_Condensed({
  variable: '--font-barlow-condensed',
  subsets: ['latin'],
  weight: ['600', '700'],
})

export const metadata: Metadata = {
  title: 'MESchede MES',
  description: 'Manufacturing Execution System — Berufskolleg Meschede',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="de"
      className={`dark ${geistSans.variable} ${geistMono.variable} ${barlowCondensed.variable}`}
    >
      <body className="antialiased">
        <div className="flex h-screen bg-background">
          <Sidebar />
          <main className="flex-1 overflow-auto">{children}</main>
        </div>
      </body>
    </html>
  )
}
