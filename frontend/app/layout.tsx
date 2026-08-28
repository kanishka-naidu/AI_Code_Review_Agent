import { Analytics } from '@vercel/analytics/next'
import type { Metadata, Viewport } from 'next'
import './globals.css'
import { ThemeProvider } from '@/components/theme-provider'
import { SettingsProvider } from '@/context/settings-context'

export const metadata: Metadata = {
  title: 'Smart Code Inspection Platform',
  description: 'Development of Smart Code Inspection Platform with Vulnerability Detection System',
  generator: 'v0.app',
  icons: {
    icon: [
      {
        url: '/icon.svg',
        type: 'image/svg+xml',
      },
    ],
    apple: '/apple-icon.png',
  },
}

export const viewport: Viewport = {
  colorScheme: 'dark light',
  themeColor: [
    { media: '(prefers-color-scheme: dark)', color: '#09090b' },
    { media: '(prefers-color-scheme: light)', color: '#f8fafc' },
  ],
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="antialiased bg-background text-foreground">
        <ThemeProvider>
          <SettingsProvider>
            {children}
          </SettingsProvider>
        </ThemeProvider>
        {process.env.NODE_ENV === 'production' && <Analytics />}
      </body>
    </html>
  )
}
