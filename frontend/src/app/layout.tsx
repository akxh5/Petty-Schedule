import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import Navigation from '@/components/Navigation'

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' })

export const metadata: Metadata = {
  title: 'Faculty Duty Scheduler',
  description: 'Constraint-based fair duty rostering system for professors',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} font-sans min-h-screen flex flex-col md:flex-row bg-background`}>
        <Navigation />
        <main className="flex-1 p-4 sm:p-6 md:p-10 lg:p-12 overflow-y-auto w-full max-w-[100vw]">
          {children}
        </main>
      </body>
    </html>
  )
}
