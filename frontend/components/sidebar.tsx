'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  LayoutDashboard,
  Upload,
  Code,
  BarChart3,
  Clock,
  Settings,
  ChevronLeft,
  ChevronRight,
  Bot,
} from 'lucide-react'

const menuItems = [
  { icon: LayoutDashboard, label: 'Dashboard', href: '/' },
  { icon: Upload, label: 'Upload Code', href: '/upload' },
  { icon: Code, label: 'Paste Code', href: '/paste' },
  { icon: BarChart3, label: 'Reports', href: '/reports' },
  { icon: Clock, label: 'History', href: '/history' },
  { icon: Bot, label: 'AI Assistant', href: '/assistant' },
  { icon: Settings, label: 'Settings', href: '/settings' },
]

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false)
  const pathname = usePathname()

  return (
    <div
      className={`flex flex-col border-r border-border bg-sidebar transition-all duration-300 ${
        collapsed ? 'w-20' : 'w-56'
      }`}
    >
      {/* Logo */}
      <div className="flex items-center justify-between gap-3 border-b border-sidebar-border px-4 py-6">
        {!collapsed && (
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
              <Code className="h-5 w-5 text-primary-foreground" />
            </div>
            <span className="font-semibold text-sidebar-foreground">CodeReview</span>
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="ml-auto inline-flex h-8 w-8 items-center justify-center rounded-md hover:bg-sidebar-accent transition-all duration-200 hover:shadow-sm"
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4 text-sidebar-foreground" />
          ) : (
            <ChevronLeft className="h-4 w-4 text-sidebar-foreground" />
          )}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4">
        {menuItems.map((item) => {
          const Icon = item.icon
          const isActive = pathname === item.href
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-all duration-200 ${
                isActive
                  ? 'bg-sidebar-accent text-sidebar-primary border border-sidebar-accent'
                  : 'text-sidebar-foreground hover:bg-sidebar-accent/50 hover:border-l-2 hover:border-l-sidebar-primary hover:shadow-sm hover:-translate-y-0.5'
              }`}
            >
              <Icon className="h-5 w-5 flex-shrink-0" />
              {!collapsed && <span>{item.label}</span>}
            </Link>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="border-t border-sidebar-border p-4">
        {!collapsed && <p className="text-xs text-sidebar-foreground/60">v1.0.0</p>}
      </div>
    </div>
  )
}
