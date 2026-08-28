'use client'

import { ReactNode } from 'react'
import { Sidebar } from './sidebar'
import { Navbar } from './navbar'

interface LayoutWrapperProps {
  children: ReactNode
}

export function LayoutWrapper({ children }: LayoutWrapperProps) {
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Navbar />
        <main className="flex-1 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  )
}
