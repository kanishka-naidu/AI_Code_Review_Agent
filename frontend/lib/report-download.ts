/**
 * Shared helper for downloading the PDF report from the backend.
 * Used by the manual "Download PDF" button and the "Auto Download Report" setting.
 */

export async function downloadReportPDF(report: any): Promise<boolean> {
  if (!report || !report.report_id) {
    return false
  }

  try {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/report/${report.report_id}/pdf`)

    if (!response.ok) {
      throw new Error('Failed to generate PDF')
    }

    const blob = await response.blob()
    const url = URL.createObjectURL(blob)

    const a = document.createElement('a')
    a.href = url
    a.download = `analysis-report-${report.report_id}.pdf`
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