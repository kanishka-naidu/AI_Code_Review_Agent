/**
 * Shared helper for downloading the PDF report from the backend.
 * Used by the manual "Download PDF" button and the "Auto Download Report" setting.
 *
 * Sends the complete report data directly to the backend via POST,
 * avoiding server-side storage dependencies (works on Render FREE plan).
 */

export async function downloadReportPDF(report: any): Promise<boolean> {
  if (!report) {
    return false
  }

  try {
    // Send report data directly to the backend via POST
    // This avoids the need for server-side storage (Render FREE plan compatible)
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/report/pdf`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(report),
    })

    if (!response.ok) {
      throw new Error('Failed to generate PDF')
    }

    const blob = await response.blob()
    const url = URL.createObjectURL(blob)

    const a = document.createElement('a')
    a.href = url
    a.download = `analysis-report-${report.report_id || 'unknown'}.pdf`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)

    URL.revokeObjectURL(url)
    return true
  } catch (error) {
    console.error('Error downloading PDF:', error)
    return false
  }
}