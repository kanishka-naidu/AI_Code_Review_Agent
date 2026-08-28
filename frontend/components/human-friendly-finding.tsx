'use client'

import { useState } from 'react'
import { ChevronDown, ChevronUp, AlertTriangle, AlertCircle, Info, CheckCircle, MapPin, Tag, ShieldAlert } from 'lucide-react'

interface TechnicalSummary {
  severity: string
  rule: string
  line: number
  owasp?: string
}

interface HumanExplanation {
  problem: string
  whyItMatters: string
  recommendedFix: string
}

interface HumanFriendlyFindingProps {
  title: string
  technicalSummary: TechnicalSummary
  humanExplanation: HumanExplanation
  originalFinding?: any
}

const severityConfig = {
  critical: {
    icon: AlertCircle,
    color: 'text-red-600',
    bgColor: 'bg-red-500/10',
    borderColor: 'border-red-500/30',
    label: 'CRITICAL'
  },
  high: {
    icon: AlertCircle,
    color: 'text-red-500',
    bgColor: 'bg-red-500/10',
    borderColor: 'border-red-500/30',
    label: 'HIGH'
  },
  medium: {
    icon: AlertTriangle,
    color: 'text-yellow-500',
    bgColor: 'bg-yellow-500/10',
    borderColor: 'border-yellow-500/30',
    label: 'MEDIUM'
  },
  low: {
    icon: Info,
    color: 'text-blue-500',
    bgColor: 'bg-blue-500/10',
    borderColor: 'border-blue-500/30',
    label: 'LOW'
  },
  info: {
    icon: Info,
    color: 'text-slate-500',
    bgColor: 'bg-slate-500/10',
    borderColor: 'border-slate-500/30',
    label: 'INFO'
  },
}

function toSeverityLabel(severity: string): string {
  const s = (severity || 'low').toLowerCase()
  const config = severityConfig[s as keyof typeof severityConfig]
  return config ? config.label : s.toUpperCase()
}

function cleanTechnicalText(text: string): string {
  if (!text) return ''
  // Remove markdown formatting
  let cleaned = text
    .replace(/\*\*(.+?)\*\*/g, '$1')
    .replace(/`(.+?)`/g, '$1')
    .replace(/^#{1,6}\s*/gm, '')
    .replace(/^\s*[-*]\s+/gm, '• ')
    .replace(/^\s*\d+\.\s+/gm, '')
    .replace(/\n{3,}/g, '\n\n')
    .trim()
  return cleaned
}

export function generateHumanFriendlyExplanation(finding: any): HumanExplanation {
  const { title, severity, description, remediation } = finding

  // Use the actual description/remediation from the backend where available.
  const problem = cleanTechnicalText(description) || 'This code contains a potential security or quality issue.'
  const recommendedFix = cleanTechnicalText(remediation) || 'Review the code and apply the recommended fix to resolve this issue.'

  const severityLabel = toSeverityLabel(severity || 'low')

  const whyItMatters = `This is a ${severityLabel.toLowerCase()} severity issue. It could affect the security or reliability of your code if left unaddressed.`

  return {
    problem,
    whyItMatters,
    recommendedFix
  }
}

export function HumanFriendlyFinding({
  title,
  technicalSummary,
  humanExplanation,
  originalFinding
}: HumanFriendlyFindingProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const config = severityConfig[technicalSummary.severity.toLowerCase() as keyof typeof severityConfig] || severityConfig.low
  const Icon = config.icon

  return (
    <div className={`rounded-xl border bg-card overflow-hidden transition-all duration-200 ${config.borderColor} hover:shadow-lg`}>
      {/* Header */}
      <div className="p-5 sm:p-6 cursor-pointer" onClick={() => setIsExpanded(!isExpanded)}>
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 mb-4 flex-wrap">
              <div className={`rounded-lg ${config.bgColor} p-2 flex-shrink-0`}>
                <Icon className={`h-5 w-5 ${config.color}`} />
              </div>
              <h3 className="text-base sm:text-lg font-semibold text-foreground break-words">{title}</h3>
              <span className={`px-3 py-1 rounded-full text-xs font-semibold ${config.bgColor} ${config.color}`}>
                {config.label}
              </span>
            </div>

            {/* Technical Summary */}
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-4">
              <div className="bg-background/50 rounded-lg p-3 min-w-0">
                <div className="flex items-center gap-1.5 mb-1">
                  <Tag className="h-3.5 w-3.5 text-muted-foreground flex-shrink-0" />
                  <p className="text-xs text-muted-foreground">Issue</p>
                </div>
                <p className="text-sm font-medium text-foreground break-words line-clamp-2">{technicalSummary.rule}</p>
              </div>
              <div className="bg-background/50 rounded-lg p-3 min-w-0">
                <div className="flex items-center gap-1.5 mb-1">
                  <MapPin className="h-3.5 w-3.5 text-muted-foreground flex-shrink-0" />
                  <p className="text-xs text-muted-foreground">Location</p>
                </div>
                <p className="text-sm font-medium text-foreground break-words">{technicalSummary.line || 'N/A'}</p>
              </div>
              <div className="bg-background/50 rounded-lg p-3 min-w-0">
                <div className="flex items-center gap-1.5 mb-1">
                  <ShieldAlert className="h-3.5 w-3.5 text-muted-foreground flex-shrink-0" />
                  <p className="text-xs text-muted-foreground">Severity</p>
                </div>
                <p className="text-sm font-medium text-foreground break-words">{toSeverityLabel(technicalSummary.severity)}</p>
              </div>
            </div>

            {/* Human Explanation Preview */}
            <div className="space-y-2">
              <div className="flex items-start gap-2">
                <div className={`w-1 h-4 rounded-full mt-1 flex-shrink-0 ${config.color.replace('text-', 'bg-')}`} />
                <div className="min-w-0">
                  <p className="text-sm font-medium text-foreground">Problem</p>
                  <p className="text-sm text-muted-foreground line-clamp-3 break-words">{humanExplanation.problem}</p>
                </div>
              </div>
            </div>
          </div>

          <button className="flex-shrink-0 p-2 hover:bg-background/50 rounded-lg transition-colors" aria-label="Toggle details">
            {isExpanded ? (
              <ChevronUp className="h-5 w-5 text-muted-foreground" />
            ) : (
              <ChevronDown className="h-5 w-5 text-muted-foreground" />
            )}
          </button>
        </div>
      </div>

      {/* Expanded Details */}
      {isExpanded && (
        <div className="border-t border-border bg-background/30 p-5 sm:p-6 space-y-6">
          <div className="space-y-4">
            <div className="flex items-start gap-3">
              <div className={`w-8 h-8 rounded-full ${config.bgColor} flex items-center justify-center flex-shrink-0`}>
                <AlertTriangle className={`h-4 w-4 ${config.color}`} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-foreground mb-1">What is the problem?</p>
                <p className="text-sm text-muted-foreground leading-relaxed break-words">{humanExplanation.problem}</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-full bg-yellow-500/10 flex items-center justify-center flex-shrink-0">
                <Info className="h-4 w-4 text-yellow-500" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-foreground mb-1">Why does it matter?</p>
                <p className="text-sm text-muted-foreground leading-relaxed break-words">{humanExplanation.whyItMatters}</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-full bg-green-500/10 flex items-center justify-center flex-shrink-0">
                <CheckCircle className="h-4 w-4 text-green-500" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-foreground mb-1">What should you do?</p>
                <p className="text-sm text-muted-foreground leading-relaxed break-words">{humanExplanation.recommendedFix}</p>
              </div>
            </div>
          </div>

          {/* Technical Details Section */}
          {originalFinding && (
            <div className="space-y-4">
              <h4 className="text-sm font-semibold text-foreground uppercase tracking-wide">Technical Details</h4>
              <div className="bg-background/50 rounded-lg p-4 space-y-3">
                {originalFinding.description && (
                  <div>
                    <p className="text-xs text-muted-foreground mb-1">Description</p>
                    <p className="text-sm text-foreground break-words">{originalFinding.description}</p>
                  </div>
                )}
                {originalFinding.remediation && (
                  <div>
                    <p className="text-xs text-muted-foreground mb-1">Suggested Fix</p>
                    <pre className="text-sm text-foreground bg-background p-3 rounded border border-border whitespace-pre-wrap break-words">
                      {originalFinding.remediation}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}