'use client'

import { Moon, Sun } from 'lucide-react'
import { useTheme } from 'next-themes'
import { useEffect, useState } from 'react'

export function Navbar() {
  const { theme, setTheme } = useTheme()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    return (
      <header className="sticky top-0 z-40 border-b border-border bg-background/80 backdrop-blur-sm">
        <div className="flex h-14 items-center justify-between px-6">
          <div className="flex items-center gap-8">
            <div className="text-sm font-medium text-foreground">Project • Analysis</div>
          </div>
          <div className="flex items-center gap-4">
            <div className="inline-flex h-8 w-8 items-center justify-center rounded-lg hover:bg-card transition-colors text-muted-foreground hover:text-foreground" />
            <button className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-primary/20 text-primary hover:bg-primary/30 transition-colors font-semibold">
              U
            </button>
          </div>
        </div>
      </header>
    )
  }

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/80 backdrop-blur-sm">
      <div className="flex h-14 items-center justify-between px-6">
        {/* Left */}
        <div className="flex items-center gap-8">
          <div className="text-sm font-medium text-foreground">Project • Analysis</div>
        </div>

        {/* Right */}
        <div className="flex items-center gap-4">
          <button
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            className="inline-flex h-8 w-8 items-center justify-center rounded-lg hover:bg-card transition-colors text-muted-foreground hover:text-foreground"
            aria-label="Toggle theme"
          >
            {theme === 'dark' ? (
              <Sun className="h-4 w-4" />
            ) : (
              <Moon className="h-4 w-4" />
            )}
          </button>
          <button className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-primary/20 text-primary hover:bg-primary/30 transition-colors font-semibold">
            U
          </button>
        </div>
      </div>
    </header>
  )
}
