'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { LayoutWrapper } from '@/components/layout-wrapper'
import { Clock, Code2, Shield, AlertTriangle, Trash2 } from 'lucide-react'

export default function HistoryPage() {
  const [history, setHistory] = useState<any[]>([])
  const router = useRouter()

  const clearHistory = () => {
    if (!confirm('Are you sure you want to clear all analysis history?')) {
      return
    }

    localStorage.removeItem('analysisHistory')
    setHistory([])
  }

  const viewReport = (item: any) => {
    // Set the report as the latest report and navigate to reports page.
    // History items store the report ID under `id`, but the Reports page
    // requires `report_id` for PDF generation. Map it here so PDF download
    // works for reports opened from History.
    const reportForView = { ...item, report_id: item.report_id || item.id }
    localStorage.setItem('latestReport', JSON.stringify(reportForView))
    router.push('/reports')
  }

  useEffect(() => {
    const stored = localStorage.getItem('analysisHistory')
    if (stored) {
      setHistory(JSON.parse(stored))
    }
  }, [])

  if (history.length === 0) {
    return (
      <LayoutWrapper>
        <div className="mx-auto max-w-4xl px-6 py-12">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-foreground">
              Analysis History
            </h1>
            <p className="mt-2 text-muted-foreground">
              View your previous code analysis runs
            </p>
          </div>

          <div className="rounded-xl border border-border bg-card p-12 text-center">
            <div className="space-y-4">
              <div className="flex justify-center">
                <div className="rounded-lg bg-primary/10 p-3">
                  <Clock className="h-8 w-8 text-primary" />
                </div>
              </div>

              <div>
                <p className="font-medium text-foreground">
                  No previous analyses found.
                </p>

                <p className="mt-2 text-sm text-muted-foreground">
                  Run your first analysis to build history.
                </p>
              </div>

              <Link
                href="/upload"
                className="inline-flex items-center gap-2 rounded-lg bg-primary px-6 py-2.5 font-medium text-primary-foreground hover:bg-primary/90"
              >
                Run Analysis
              </Link>
            </div>
          </div>
        </div>
      </LayoutWrapper>
    )
  }

  return (
    <LayoutWrapper>
      <div className="mx-auto max-w-6xl px-6 py-8">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-foreground">
              Analysis History
            </h1>
            <p className="mt-2 text-muted-foreground">
              Previous code analysis reports
            </p>
          </div>

          <button
            onClick={clearHistory}
            className="flex items-center gap-2 rounded-lg bg-red-600 px-5 py-2.5 text-sm font-medium text-white transition-all duration-200 hover:bg-red-700"
          >
            <Trash2 className="h-4 w-4" />
            Clear History
          </button>
        </div>

        {/* History Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {history.map((item) => {
            const findingsList: any[] = item.findings || []
            const highSeverityCount = findingsList.filter(
              (f: any) => f.severity?.toLowerCase() === "high"
            ).length
            const mediumSeverityCount = findingsList.filter(
              (f: any) => f.severity?.toLowerCase() === "medium"
            ).length
            const lowSeverityCount = findingsList.filter(
              (f: any) => f.severity?.toLowerCase() === "low"
            ).length
            const criticalSeverityCount = findingsList.filter(
              (f: any) => f.severity?.toLowerCase() === "critical"
            ).length

            return (
              <div
                key={item.id}
                className="rounded-xl border border-border bg-card p-6 hover:border-primary/30 transition-all duration-200 cursor-pointer"
                onClick={() => viewReport(item)}
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="rounded-lg bg-primary/10 p-2">
                      <Code2 className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-foreground capitalize">
                        {item.language}
                      </h3>
                      <p className="text-xs text-muted-foreground mt-1">
                        {item.timestamp}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  {/* Scores */}
                  <div className="grid grid-cols-2 gap-3">
                    <div className="bg-background/50 rounded-lg p-3">
                      <div className="flex items-center gap-2 mb-1">
                        <Shield className="h-4 w-4 text-green-500" />
                        <p className="text-xs text-muted-foreground">Quality</p>
                      </div>
                      <p className="text-lg font-bold text-foreground">
                        {item.quality_score || 0}
                      </p>
                    </div>
                    <div className="bg-background/50 rounded-lg p-3">
                      <div className="flex items-center gap-2 mb-1">
                        <AlertTriangle className="h-4 w-4 text-red-500" />
                        <p className="text-xs text-muted-foreground">Security</p>
                      </div>
                      <p className="text-lg font-bold text-foreground">
                        {item.security_score || 0}
                      </p>
                    </div>
                  </div>

                  {/* Findings Count */}
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-muted-foreground">Total Findings</p>
                    <span className="rounded-full bg-primary/10 px-3 py-1 text-sm font-medium text-primary">
                      {item.findings?.length ?? 0}
                    </span>
                  </div>

                  {/* Severity Breakdown */}
                  <div className="flex flex-wrap gap-2">
                    {criticalSeverityCount > 0 && (
                      <span className="text-xs px-2 py-1 rounded-full bg-red-600/10 text-red-600">
                        {criticalSeverityCount} CRITICAL
                      </span>
                    )}
                    <span className="text-xs px-2 py-1 rounded-full bg-red-500/10 text-red-500">
                      {highSeverityCount} HIGH
                    </span>
                    <span className="text-xs px-2 py-1 rounded-full bg-yellow-500/10 text-yellow-500">
                      {mediumSeverityCount} MEDIUM
                    </span>
                    <span className="text-xs px-2 py-1 rounded-full bg-blue-500/10 text-blue-500">
                      {lowSeverityCount} LOW
                    </span>
                  </div>
                </div>

                <div className="mt-4 pt-4 border-t border-border">
                  <p className="text-xs text-primary font-medium">Click to view full report →</p>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </LayoutWrapper>
  )
}