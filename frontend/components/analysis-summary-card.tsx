'use client'

import { Shield, Code2, AlertTriangle, CheckCircle } from 'lucide-react'

interface AnalysisSummaryCardProps {
  qualityScore: number
  securityScore: number
  findingsCount: number
  language: string
  severityDistribution?: {
    critical?: number
    high?: number
    medium?: number
    low?: number
    info?: number
  }
}

export function AnalysisSummaryCard({
  qualityScore,
  securityScore,
  findingsCount,
  language,
  severityDistribution,
}: AnalysisSummaryCardProps) {
  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-500'
    if (score >= 60) return 'text-yellow-500'
    return 'text-red-500'
  }

  const getScoreLabel = (score: number) => {
    if (score >= 80) return 'Excellent'
    if (score >= 60) return 'Good'
    if (score >= 40) return 'Fair'
    return 'Poor'
  }

  const critical = severityDistribution?.critical ?? 0
  const high = severityDistribution?.high ?? 0
  const medium = severityDistribution?.medium ?? 0
  const low = severityDistribution?.low ?? 0
  const info = severityDistribution?.info ?? 0

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {/* Language Card */}
      <div className="rounded-xl border border-border bg-card p-6 hover:border-primary/30 transition-all duration-200">
        <div className="flex items-center gap-3 mb-4">
          <div className="rounded-lg bg-primary/10 p-2">
            <Code2 className="h-5 w-5 text-primary" />
          </div>
          <p className="text-sm font-medium text-muted-foreground">Language</p>
        </div>
        <p className="text-2xl font-bold text-foreground capitalize">{language}</p>
      </div>

      {/* Quality Score Card */}
      <div className="rounded-xl border border-border bg-card p-6 hover:border-primary/30 transition-all duration-200">
        <div className="flex items-center gap-3 mb-4">
          <div className="rounded-lg bg-green-500/10 p-2">
            <CheckCircle className="h-5 w-5 text-green-500" />
          </div>
          <p className="text-sm font-medium text-muted-foreground">Quality Score</p>
        </div>
        <div className="flex items-baseline gap-2">
          <p className={`text-2xl font-bold ${getScoreColor(qualityScore)}`}>
            {qualityScore}
          </p>
          <span className="text-sm text-muted-foreground">/100</span>
        </div>
        <p className={`text-xs font-medium mt-1 ${getScoreColor(qualityScore)}`}>
          {getScoreLabel(qualityScore)}
        </p>
      </div>

      {/* Security Score Card */}
      <div className="rounded-xl border border-border bg-card p-6 hover:border-primary/30 transition-all duration-200">
        <div className="flex items-center gap-3 mb-4">
          <div className="rounded-lg bg-red-500/10 p-2">
            <Shield className="h-5 w-5 text-red-500" />
          </div>
          <p className="text-sm font-medium text-muted-foreground">Security Score</p>
        </div>
        <div className="flex items-baseline gap-2">
          <p className={`text-2xl font-bold ${getScoreColor(securityScore)}`}>
            {securityScore}
          </p>
          <span className="text-sm text-muted-foreground">/100</span>
        </div>
        <p className={`text-xs font-medium mt-1 ${getScoreColor(securityScore)}`}>
          {getScoreLabel(securityScore)}
        </p>
      </div>

      {/* Findings Count Card */}
      <div className="rounded-xl border border-border bg-card p-6 hover:border-primary/30 transition-all duration-200">
        <div className="flex items-center gap-3 mb-4">
          <div className="rounded-lg bg-yellow-500/10 p-2">
            <AlertTriangle className="h-5 w-5 text-yellow-500" />
          </div>
          <p className="text-sm font-medium text-muted-foreground">Total Findings</p>
        </div>
        <p className="text-2xl font-bold text-foreground">{findingsCount}</p>
        <div className="flex flex-wrap gap-2 mt-2">
          {critical > 0 && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-red-600/10 text-red-600">
              {critical} CRITICAL
            </span>
          )}
          {high > 0 && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-red-500/10 text-red-500">
              {high} HIGH
            </span>
          )}
          {medium > 0 && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-yellow-500/10 text-yellow-500">
              {medium} MEDIUM
            </span>
          )}
          {low > 0 && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-500">
              {low} LOW
            </span>
          )}
          {info > 0 && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-500/10 text-slate-500">
              {info} INFO
            </span>
          )}
        </div>
      </div>
    </div>
  )
}