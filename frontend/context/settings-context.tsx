'use client'

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'

interface SettingsContextType {
  fontSize: 'small' | 'medium' | 'large'
  wordWrap: boolean
  lineNumbers: boolean
  setFontSize: (size: 'small' | 'medium' | 'large') => void
  setWordWrap: (value: boolean) => void
  setLineNumbers: (value: boolean) => void
}

const SettingsContext = createContext<SettingsContextType | undefined>(undefined)

const DEFAULT_SETTINGS: SettingsContextType = {
  fontSize: 'medium',
  wordWrap: true,
  lineNumbers: true,
  setFontSize: () => {},
  setWordWrap: () => {},
  setLineNumbers: () => {},
}

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [fontSize, setFontSize] = useState<'small' | 'medium' | 'large'>('medium')
  const [wordWrap, setWordWrap] = useState(true)
  const [lineNumbers, setLineNumbers] = useState(true)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    const savedFontSize = (localStorage.getItem('fontSize') || 'medium') as 'small' | 'medium' | 'large'
    const savedWordWrap = localStorage.getItem('wordWrap') !== 'false'
    const savedLineNumbers = localStorage.getItem('lineNumbers') !== 'false'

    setFontSize(savedFontSize)
    setWordWrap(savedWordWrap)
    setLineNumbers(savedLineNumbers)
  }, [])

  const handleSetFontSize = (size: 'small' | 'medium' | 'large') => {
    setFontSize(size)
    localStorage.setItem('fontSize', size)
    document.documentElement.style.fontSize = size === 'small' ? '13px' : size === 'large' ? '16px' : '14px'
  }

  const handleSetWordWrap = (value: boolean) => {
    setWordWrap(value)
    localStorage.setItem('wordWrap', String(value))
  }

  const handleSetLineNumbers = (value: boolean) => {
    setLineNumbers(value)
    localStorage.setItem('lineNumbers', String(value))
  }

  const value: SettingsContextType = {
    fontSize,
    wordWrap,
    lineNumbers,
    setFontSize: handleSetFontSize,
    setWordWrap: handleSetWordWrap,
    setLineNumbers: handleSetLineNumbers,
  }

  return (
    <SettingsContext.Provider value={value}>
      {children}
    </SettingsContext.Provider>
  )
}

export function useSettings() {
  const context = useContext(SettingsContext)
  if (context === undefined) {
    throw new Error('useSettings must be used within a SettingsProvider')
  }
  return context
}
