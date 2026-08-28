'use client'

import { useState } from 'react'
import { LayoutWrapper } from '@/components/layout-wrapper'
import { InputPanel } from '@/components/input-panel'
import { AnalysisSummaryCard } from '@/components/analysis-summary-card'
import { HumanFriendlyFinding, generateHumanFriendlyExplanation } from '@/components/human-friendly-finding'

export default function UploadPage() {
  const [analyzed, setAnalyzed] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [findings, setFindings] = useState<any[]>([])
  const [reportData, setReportData] = useState<any>(null)

  const handleAnalyze = async (code: string, language: string) => {
  setIsLoading(true);

    try {
      const selectedLanguage =
        language === "Auto Detect"
          ? code.includes("public class") || code.includes("class ")
            ? "java"
            : "python"
          : language.toLowerCase();

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          language: selectedLanguage,
          code: code,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || "Analysis failed");
      }

      const data = await response.json();
      const report = data.report;

      // Save latest report
      localStorage.setItem("latestReport", JSON.stringify(report));

      // Save history
      const history = JSON.parse(localStorage.getItem("analysisHistory") || "[]");

      history.unshift({
        id: report.report_id,
        timestamp: report.timestamp,
        language: report.language,
        summary: report.summary,
        findings: report.findings,
        quality_score: report.quality_score,
        security_score: report.security_score,
        pr_summary: report.pr_summary,
    });

localStorage.setItem("analysisHistory", JSON.stringify(history));
      setAnalyzed(true);
      setReportData(report);

      setFindings(
        (report.findings || []).map((item: any) => ({
            title: item.title,
            severity: item.severity,
            description: item.description,
            suggestedFix: item.remediation,
            owasp: item.owasp_reference,
            line: item.location,
            originalFinding: item,
        }))
    );
    } catch (err) {
      console.error(err);
      alert("Cannot connect to backend.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <LayoutWrapper>
      <div className="mx-auto max-w-6xl px-6 py-8">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-foreground">Upload Code</h1>
          <p className="mt-2 text-muted-foreground">
            Upload your Python or Java file for security analysis
          </p>
        </div>

        {!analyzed ? (
          <InputPanel
            onAnalyze={handleAnalyze}
            isLoading={isLoading}
          />
        ) : (
          <div className="space-y-8">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold text-foreground">Analysis Complete</h2>
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
                className="rounded-lg border border-border bg-card px-4 py-2 text-sm font-medium text-foreground hover:bg-card/80 transition-colors"
              >
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

            {reportData?.pr_summary && (
              <div className="rounded-xl border border-border bg-card p-6">
                <h3 className="text-xl font-semibold text-foreground mb-4">
                  PR Summary
                </h3>
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
                <h3 className="text-xl font-semibold text-foreground">Security Findings</h3>
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
                        owasp: finding.owasp || 'N/A'
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
