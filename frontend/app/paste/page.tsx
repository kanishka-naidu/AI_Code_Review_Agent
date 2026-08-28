'use client'

import { useState } from 'react'
import { LayoutWrapper } from '@/components/layout-wrapper'
import { InputPanel } from '@/components/input-panel'
import { AnalysisSummaryCard } from '@/components/analysis-summary-card'
import { HumanFriendlyFinding, generateHumanFriendlyExplanation } from '@/components/human-friendly-finding'
import { Code2, FileText, ListChecks, BookOpen, Loader2, RotateCcw } from 'lucide-react'

export default function PastePage() {
  const [code, setCode] = useState('')
  const [language, setLanguage] = useState('Auto Detect')
  const [analyzed, setAnalyzed] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [findings, setFindings] = useState<any[]>([])
  const [reportData, setReportData] = useState<any>(null)

  const handleAnalyze = async (codeText: string, lang: string) => {
    setIsLoading(true)

    try {
      const selectedLanguage =
        lang === "Auto Detect"
          ? codeText.includes("public class") || codeText.includes("class ")
            ? "java"
            : "python"
          : lang.toLowerCase()

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          language: selectedLanguage,
          code: codeText,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => null)
        throw new Error(errorData?.detail || 'Analysis failed')
      }

      const data = await response.json()
      const report = data.report

      // Save latest report
      localStorage.setItem("latestReport", JSON.stringify(report))

      // Save history
      const history = JSON.parse(localStorage.getItem("analysisHistory") || "[]")

      history.unshift({
        id: report.report_id,
        timestamp: report.timestamp,
        language: report.language,
        summary: report.summary,
        findings: report.findings,
        quality_score: report.quality_score,
        security_score: report.security_score,
        pr_summary: report.pr_summary,
      })

      localStorage.setItem("analysisHistory", JSON.stringify(history))

      setAnalyzed(true)
      setReportData(report)

      setFindings(
        (report.findings || []).map((item: any) => ({
          title: item.title,
          severity: item.severity,
          description: item.description,
          suggestedFix: item.remediation,
          line: item.location,
          originalFinding: item,
        }))
      )
    } catch (err: any) {
      console.error(err)
      alert(err.message || "Cannot connect to backend.")
    } finally {
      setIsLoading(false)
    }
  }

  const aceOptions = {
    fontSize: 14,
    showGutter: true,
    showPrintMargin: false,
    useWorker: false,
    maxLines: 40,
    minLines: 15,
  }

  return (
    <LayoutWrapper>
      <div className="mx-auto max-w-6xl px-4 sm:px-6 py-8">
        <div className="mb-8">
          <h1 className="text-2xl sm:text-3xl font-bold text-foreground">Paste Code</h1>
          <p className="mt-2 text-muted-foreground">
            Paste your Python or Java code for AI-powered analysis
          </p>
        </div>

        {!analyzed ? (
          <div className="space-y-6">
            <div className="rounded-xl border border-border bg-card p-5 sm:p-6">
              <div className="flex items-center gap-2 mb-5">
                <div className="rounded-lg bg-primary/10 p-2">
                  <Code2 className="h-5 w-5 text-primary" />
                </div>
                <h2 className="text-lg font-semibold text-foreground">Code Input</h2>
              </div>

              <div className="mb-5">
                <label className="block text-sm font-medium text-foreground mb-2">Language</label>
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="w-full sm:w-auto rounded-lg border border-border bg-background px-4 py-2.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 transition-shadow"
                >
                  <option value="Auto Detect">Auto Detect</option>
                  <option value="Python">Python</option>
                  <option value="Java">Java</option>
                </select>
              </div>

              <div className="mb-5">
                <label className="block text-sm font-medium text-foreground mb-2">Code</label>
                <textarea
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  placeholder="Paste your Python or Java code here..."
                  className="w-full min-h-[400px] rounded-lg border border-border bg-background px-4 py-3 font-mono text-sm text-foreground placeholder:text-muted-foreground resize-y focus:outline-none focus:ring-2 focus:ring-primary/50 transition-shadow"
                  spellCheck={false}
                />
              </div>

              <button
                onClick={() => handleAnalyze(code, language)}
                disabled={isLoading || !code.trim()}
                className="flex items-center justify-center gap-2 rounded-lg bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed w-full sm:w-auto"
              >
                {isLoading ? (
                  <span className="flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Analyzing...
                  </span>
                ) : (
                  <>
                    <Code2 className="h-4 w-4" />
                    Analyze Code
                  </>
                )}
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-8">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h2 className="text-xl sm:text-2xl font-bold text-foreground">Analysis Complete</h2>
                <p className="mt-1 text-muted-foreground">
                  Found {findings.length} issue{findings.length !== 1 ? 's' : ''}
                </p>
              </div>
              <button
                onClick={() => {
                  setAnalyzed(false)
                  setFindings([])
                  setReportData(null)
                }}
                className="inline-flex items-center justify-center gap-2 rounded-lg border border-border bg-card px-4 py-2.5 text-sm font-medium text-foreground hover:bg-card/80 transition-colors"
              >
                <RotateCcw className="h-4 w-4" />
                New Analysis
              </button>
            </div>

            {reportData && (
              <AnalysisSummaryCard
                qualityScore={reportData.quality_score || 0}
                securityScore={reportData.security_score || 0}
                findingsCount={findings.length}
                language={reportData.language || 'Unknown'}
                severityDistribution={reportData.severity_distribution}
              />
            )}

            {/* PR Summary */}
            {reportData?.pr_summary && (
              <div className="rounded-xl border border-border bg-card p-5 sm:p-6">
                <div className="flex items-center gap-2 mb-4">
                  <div className="rounded-lg bg-primary/10 p-2">
                    <FileText className="h-5 w-5 text-primary" />
                  </div>
                  <h3 className="text-lg font-semibold text-foreground">
                    PR Summary
                  </h3>
                </div>
                <div className="space-y-2">
                  {reportData.pr_summary.split('\n').filter((line: string) => line.trim()).map((line: string, idx: number) => (
                    <p key={idx} className="text-sm text-muted-foreground leading-relaxed">
                      {line}
                    </p>
                  ))}
                </div>
              </div>
            )}

            {findings.length > 0 ? (
              <div className="space-y-4">
                <div className="flex items-center gap-2">
                  <div className="rounded-lg bg-yellow-500/10 p-2">
                    <ListChecks className="h-5 w-5 text-yellow-500" />
                  </div>
                  <h3 className="text-lg font-semibold text-foreground">Security Findings</h3>
                </div>
                {findings.map((finding, idx) => {
                  const humanExplanation = generateHumanFriendlyExplanation(finding.originalFinding)

                  return (
                    <HumanFriendlyFinding
                      key={idx}
                      title={finding.title}
                      technicalSummary={{
                        severity: finding.severity,
                        rule: finding.title,
                        line: finding.line,
                      }}
                      humanExplanation={humanExplanation}
                      originalFinding={finding.originalFinding}
                    />
                  )
                })}
              </div>
            ) : (
              <div className="rounded-xl border border-border bg-card p-12 text-center">
                <div className="flex justify-center mb-4">
                  <div className="rounded-full bg-green-500/10 p-4">
                    <svg className="h-8 w-8 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                </div>
                <h3 className="text-lg font-semibold text-foreground mb-2">No Issues Found</h3>
                <p className="text-muted-foreground">Your code looks good! No security vulnerabilities were detected.</p>
              </div>
            )}
          </div>
        )}
      </div>
    </LayoutWrapper>
  )
}