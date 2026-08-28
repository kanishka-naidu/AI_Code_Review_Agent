'use client'

import { useEffect, useState } from 'react'
import { LayoutWrapper } from '@/components/layout-wrapper'
import { Moon, Sun, Code2, Shield, BookOpen, Zap, Bot, FileText, CheckCircle2 } from 'lucide-react'
import { useTheme } from 'next-themes'
import { useSettings } from '@/context/settings-context'

export default function SettingsPage() {
  const { theme, setTheme } = useTheme()
  const {
    fontSize,
    setFontSize,
    wordWrap,
    setWordWrap,
    lineNumbers,
    setLineNumbers,
  } = useSettings()
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) return null

  const currentFeatures = [
    { icon: Code2, label: 'Python & Java Code Analysis', description: 'Upload or paste code for automated analysis' },
    { icon: Shield, label: 'Security Vulnerability Detection', description: 'Detects injection, hardcoded secrets, unsafe eval, and more' },
    { icon: Zap, label: 'Code Quality Assessment', description: 'Scores code quality and maintainability' },
    { icon: BookOpen, label: 'OWASP Recommendations', description: 'Maps findings to OWASP Top 10 references' },
    { icon: Bot, label: 'AI Assistant', description: 'Ask questions and get corrected code with explanations' },
    { icon: FileText, label: 'PDF Report Generation', description: 'Download a professional 3-page analysis report' },
    { icon: CheckCircle2, label: 'Analysis History', description: 'View and revisit previous analysis runs' },
  ]

  return (
    <LayoutWrapper>
      <div className="mx-auto max-w-3xl px-6 py-12">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground">Settings</h1>
          <p className="mt-2 text-muted-foreground">Manage your preferences</p>
        </div>

        <div className="space-y-6">
          {/* Appearance Section */}
          <div className="rounded-lg border border-border bg-card p-6 hover:border-primary/30 transition-all duration-200">
            <h2 className="text-lg font-semibold text-foreground mb-4">Appearance</h2>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 rounded-lg border border-border/50 bg-background/50">
                <div className="flex items-center gap-3">
                  {theme === 'dark' ? (
                    <Moon className="h-5 w-5 text-primary" />
                  ) : (
                    <Sun className="h-5 w-5 text-primary" />
                  )}
                  <div>
                    <p className="font-medium text-foreground">
                      {theme === 'dark' ? 'Dark' : 'Light'} Theme
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {theme === 'dark' ? 'Dark mode is active' : 'Light mode is active'}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
                  className={`relative inline-flex h-8 w-14 items-center rounded-full transition-all duration-200 ${
                    theme === 'dark' ? 'bg-primary' : 'bg-muted'
                  }`}
                >
                  <span
                    className={`inline-block h-7 w-7 transform rounded-full bg-white transition-transform duration-200 ${
                      theme === 'dark' ? 'translate-x-6' : 'translate-x-0.5'
                    }`}
                  />
                </button>
              </div>
            </div>
          </div>

          {/* Editor Preferences */}
          <div className="rounded-lg border border-border bg-card p-6 hover:border-primary/30 transition-all duration-200">
            <h2 className="text-lg font-semibold text-foreground mb-4">Editor Preferences</h2>
            
            <div className="space-y-4">
              <div>
                <p className="text-sm font-medium text-foreground mb-3">Font Size</p>
                <div className="flex gap-3">
                  {(['small', 'medium', 'large'] as const).map((size) => (
                    <button
                      key={size}
                      onClick={() => setFontSize(size)}
                      className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                        fontSize === size
                          ? 'bg-primary text-primary-foreground'
                          : 'border border-border bg-background hover:border-primary/50'
                      }`}
                    >
                      {size.charAt(0).toUpperCase() + size.slice(1)}
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex items-center justify-between p-4 rounded-lg border border-border/50 bg-background/50">
                <div>
                  <p className="font-medium text-foreground">Word Wrap</p>
                  <p className="text-xs text-muted-foreground">Enable line wrapping in code editor</p>
                </div>
                <button
                  onClick={() => setWordWrap(!wordWrap)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-all duration-200 ${
                    wordWrap ? 'bg-primary' : 'bg-muted'
                  }`}
                >
                  <span
                    className={`inline-block h-5 w-5 transform rounded-full bg-white transition-transform duration-200 ${
                      wordWrap ? 'translate-x-5' : 'translate-x-0.5'
                    }`}
                  />
                </button>
              </div>

              <div className="flex items-center justify-between p-4 rounded-lg border border-border/50 bg-background/50">
                <div>
                  <p className="font-medium text-foreground">Line Numbers</p>
                  <p className="text-xs text-muted-foreground">Show line numbers in code editor</p>
                </div>
                <button
                  onClick={() => setLineNumbers(!lineNumbers)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-all duration-200 ${
                    lineNumbers ? 'bg-primary' : 'bg-muted'
                  }`}
                >
                  <span
                    className={`inline-block h-5 w-5 transform rounded-full bg-white transition-transform duration-200 ${
                      lineNumbers ? 'translate-x-5' : 'translate-x-0.5'
                    }`}
                  />
                </button>
              </div>
            </div>
          </div>

          {/* About Section */}
          <div className="rounded-lg border border-border bg-card p-6 hover:border-primary/30 transition-all duration-200">
            <div className="space-y-4">
              <div>
                <p className="text-sm font-medium text-foreground">About</p>
                <p className="mt-1 text-sm text-muted-foreground">
                  Development of Smart Code Inspection Platform with Vulnerability Detection System
                </p>
              </div>

              <div>
                <p className="text-sm font-medium text-foreground">Version</p>
                <p className="mt-1 text-sm text-muted-foreground">
                  1.0
                </p>
              </div>

              <div>
                <p className="text-sm font-medium text-foreground mb-2">Supported Languages</p>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>Python</li>
                  <li>Java</li>
                </ul>
              </div>

              <div>
                <p className="text-sm font-medium text-foreground mb-2">Technologies</p>
                <ul className="text-sm text-muted-foreground space-y-1">
                  <li>FastAPI</li>
                  <li>React</li>
                  <li>Tailwind CSS</li>
                  <li>Google Gemini</li>
                  <li>LangChain</li>
                  <li>ChromaDB</li>
                  <li>OWASP RAG</li>
                </ul>
              </div>

              {/* Current Features */}
              <div>
                <p className="text-sm font-medium text-foreground mb-3">Current Features</p>
                <div className="space-y-2">
                  {currentFeatures.map((feature, idx) => {
                    const Icon = feature.icon
                    return (
                      <div key={idx} className="flex items-start gap-3 rounded-lg border border-border/50 bg-background/50 p-3">
                        <div className="rounded-lg bg-primary/10 p-1.5 flex-shrink-0">
                          <Icon className="h-4 w-4 text-primary" />
                        </div>
                        <div>
                          <p className="text-sm font-medium text-foreground">{feature.label}</p>
                          <p className="text-xs text-muted-foreground">{feature.description}</p>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </LayoutWrapper>
  )
}
