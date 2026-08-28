"""PDF report generation service using ReportLab.

Produces a clean, professional 2-3 page report that uses the available page
space properly. Sections flow naturally (no forced page breaks that leave
large blank areas) and are filled with useful, human-readable content drawn
from the actual analysis report.

Sections:
  1. Executive Summary
  2. Overall Code Quality & Security Scores
  3. Findings Summary
  4. Severity Breakdown
  5. Detailed Findings
  6. Recommended Remediation / Roadmap
  7. PR Summary
"""
from __future__ import annotations

import io
import re
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ── Shared palette ────────────────────────────────────────────────────────────
_DARK = colors.HexColor("#1e293b")
_MUTED = colors.HexColor("#64748b")
_LIGHT_BG = colors.HexColor("#f1f5f9")
_BORDER = colors.HexColor("#e2e8f0")
_ACCENT = colors.HexColor("#2563eb")


class PDFReportService:
    """Generate a professional, human-readable PDF from an analysis report."""

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _clean_text(value: Any) -> str:
        """Convert a value to clean, single-line text without raw JSON/markdown."""
        if value is None:
            return ""
        text = str(value)
        # Remove markdown formatting that would look odd in a PDF
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
        text = re.sub(r"`(.+?)`", r"\1", text)
        text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"^\s*[-*]\s+", "• ", text, flags=re.MULTILINE)
        text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)
        # Remove markdown-style section markers like "## A04:2021 – Insecure Design"
        text = re.sub(r"#{1,6}\s*[A-Za-z0-9].*", "", text, flags=re.MULTILINE)
        # Remove "---" horizontal rules
        text = re.sub(r"^\s*---+\s*$", "", text, flags=re.MULTILINE)
        # Collapse multiple blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    @staticmethod
    def _clean_title(title: str) -> str:
        """Clean a finding title by removing rule ID prefixes and technical noise."""
        if not title:
            return "Unknown issue"
        cleaned = PDFReportService._clean_text(title)
        # Strip common rule ID prefixes like "B105:", "hardcoded_password_string:", "blacklist:"
        cleaned = re.sub(r"^[A-Za-z0-9_-]+:\s*", "", cleaned)
        # Strip "Possible hardcoded password: 'admin123'" style prefixes
        cleaned = re.sub(r"^Possible\s+", "", cleaned)
        # Clean up double spaces and trailing punctuation
        cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
        cleaned = cleaned.rstrip(".")
        if not cleaned:
            return "Unknown issue"
        return cleaned

    @staticmethod
    def _severity_label(severity: str) -> str:
        s = (severity or "unknown").lower()
        labels = {
            "critical": "CRITICAL",
            "high": "HIGH",
            "medium": "MEDIUM",
            "low": "LOW",
            "info": "INFO",
        }
        return labels.get(s, s.upper())

    @staticmethod
    def _severity_rank(severity: str) -> int:
        order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        return order.get((severity or "low").lower(), 5)

    @staticmethod
    def _score_rating(score: int) -> str:
        if score >= 90:
            return "Excellent"
        if score >= 75:
            return "Good"
        if score >= 60:
            return "Fair"
        if score >= 40:
            return "Poor"
        return "Critical"

    @staticmethod
    def _truncate(text: str, limit: int = 260) -> str:
        """Truncate text to a readable length without cutting mid-word awkwardly."""
        text = text.strip()
        if len(text) <= limit:
            return text
        cut = text[:limit]
        # Try to break at a sentence or space boundary
        for sep in (". ", "! ", "? ", " "):
            idx = cut.rfind(sep)
            if idx > limit * 0.6:
                return cut[: idx + 1].rstrip() + "…"
        return cut.rstrip() + "…"

    @staticmethod
    def _build_executive_summary(report: dict[str, Any]) -> str:
        """Build a concise plain-English executive summary."""
        quality = int(report.get("quality_score", 0) or 0)
        security = int(report.get("security_score", 0) or 0)
        findings = report.get("findings", []) or []
        sev_dist = report.get("severity_distribution") or {}
        if not isinstance(sev_dist, dict):
            sev_dist = {}

        quality_rating = PDFReportService._score_rating(quality).lower()
        security_rating = PDFReportService._score_rating(security).lower()

        critical = int(sev_dist.get("critical", 0) or 0)
        high = int(sev_dist.get("high", 0) or 0)
        medium = int(sev_dist.get("medium", 0) or 0)
        low = int(sev_dist.get("low", 0) or 0)

        parts = [
            f"This report reviews the submitted code and rates its overall quality at "
            f"{quality}/100 ({quality_rating}) and its security at {security}/100 ({security_rating})."
        ]

        if findings:
            parts.append(
                f"A total of {len(findings)} issue(s) were found: "
                f"{critical} CRITICAL, {high} HIGH, {medium} MEDIUM and {low} LOW severity."
            )
            if critical + high > 0:
                parts.append(
                    "The CRITICAL and HIGH severity issues should be fixed before the code is deployed."
                )
            elif medium > 0:
                parts.append(
                    "The MEDIUM severity issues should be addressed before the code is considered production-ready."
                )
            else:
                parts.append(
                    "The remaining issues are minor and can be handled as part of routine maintenance."
                )
        else:
            parts.append("No issues were identified in the code analysis.")

        return " ".join(parts)

    @staticmethod
    def _build_finding_summary(finding: dict[str, Any]) -> str:
        """Build a plain-English summary of a finding."""
        title = PDFReportService._clean_title(finding.get("title") or "Unknown issue")
        description = PDFReportService._clean_text(finding.get("description") or "")
        location = finding.get("location") or "unknown location"
        severity = PDFReportService._severity_label(finding.get("severity", "low"))
        category = finding.get("category") or "code"

        parts = [f"{title}."]
        if description and description.lower() != title.lower():
            parts.append(f" {PDFReportService._truncate(description, 180)}")
        parts.append(f" This issue was found in {category} code at line {location} and is rated {severity} severity.")
        return "".join(parts)

    @staticmethod
    def _build_evidence(finding: dict[str, Any]) -> str:
        """Build a short evidence snippet for a finding."""
        evidence = PDFReportService._clean_text(finding.get("evidence") or "")
        if evidence:
            return PDFReportService._truncate(evidence, 160)
        return ""

    @staticmethod
    def _build_remediation_text(finding: dict[str, Any]) -> str:
        """Build a plain-English remediation explanation for a finding."""
        remediation = PDFReportService._clean_text(finding.get("remediation") or "")
        root_cause = PDFReportService._clean_text(finding.get("root_cause") or "")
        best_practice = PDFReportService._clean_text(finding.get("best_practice") or "")

        parts: list[str] = []
        if root_cause:
            parts.append(f"Why this happens: {PDFReportService._truncate(root_cause, 140)}")
        if remediation:
            parts.append(f"What to do: {PDFReportService._truncate(remediation, 220)}")
        if best_practice:
            parts.append(f"Best practice: {PDFReportService._truncate(best_practice, 140)}")

        if not parts:
            return "Review the code at the reported location and apply the recommended fix to resolve this issue."

        return " ".join(parts)

    @staticmethod
    def _build_roadmap_item(finding: dict[str, Any], index: int) -> str:
        """Build a single remediation roadmap item in plain English."""
        title = PDFReportService._clean_title(finding.get("title") or "Unknown issue")
        severity = PDFReportService._severity_label(finding.get("severity", "low"))
        location = finding.get("location") or "unknown location"
        remediation = PDFReportService._clean_text(finding.get("remediation") or "")
        if remediation:
            return f"{index}. {title} (line {location}, {severity} severity). {PDFReportService._truncate(remediation, 200)}"
        return f"{index}. {title} (line {location}, {severity} severity). Review the code and apply the recommended fix."

    @staticmethod
    def _build_secure_recommendation(rec: str) -> str:
        """Clean a recommendation string for display."""
        clean = PDFReportService._clean_text(rec)
        # Strip leading severity/rule markers like "[High / Security] Rule B605:"
        clean = re.sub(r"^\[[^\]]*\]\s*", "", clean)
        clean = re.sub(r"^Rule\s+[A-Za-z0-9_-]+:\s*", "", clean)
        clean = re.sub(r"^\*\s*Action:\s*", "", clean)
        return clean.strip()

    @staticmethod
    def _build_pr_summary(report: dict[str, Any]) -> str:
        """Build a clean, human-readable PR summary section."""
        pr_summary = report.get("pr_summary") or ""
        if not pr_summary:
            return ""
        # Clean markdown formatting for PDF display
        clean = PDFReportService._clean_text(pr_summary)
        # Convert markdown list markers to bullets
        clean = re.sub(r"^\s*[-*]\s+", "• ", clean, flags=re.MULTILINE)
        return clean

    # ── Main generation ──────────────────────────────────────────────────────

    @staticmethod
    def generate(report: dict[str, Any]) -> bytes:
        """Return PDF bytes for the given report dict (2-3 pages, naturally filled)."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.7 * inch,
            leftMargin=0.7 * inch,
            topMargin=0.6 * inch,
            bottomMargin=0.6 * inch,
            title="Code Analysis Report",
            author="Development of Smart Code Inspection Platform with Vulnerability Detection System",
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "TitleCustom",
            parent=styles["Title"],
            fontSize=20,
            leading=24,
            spaceAfter=4,
            textColor=_DARK,
        )
        subtitle_style = ParagraphStyle(
            "SubtitleCustom",
            parent=styles["Normal"],
            fontSize=10,
            leading=13,
            textColor=_MUTED,
            spaceAfter=10,
        )
        heading_style = ParagraphStyle(
            "HeadingCustom",
            parent=styles["Heading2"],
            fontSize=13,
            leading=17,
            spaceBefore=10,
            spaceAfter=5,
            textColor=_DARK,
        )
        body_style = ParagraphStyle(
            "BodyCustom",
            parent=styles["Normal"],
            fontSize=9.5,
            leading=13,
            alignment=TA_LEFT,
            spaceAfter=5,
        )
        small_style = ParagraphStyle(
            "SmallCustom",
            parent=styles["Normal"],
            fontSize=8.5,
            leading=11,
            textColor=_MUTED,
        )

        story: list[Any] = []

        findings = report.get("findings", []) or []
        sev_dist = report.get("severity_distribution") or {}
        if not isinstance(sev_dist, dict):
            sev_dist = {}

        # Sort findings by severity (most severe first)
        sorted_findings = sorted(
            findings,
            key=lambda fd: PDFReportService._severity_rank(fd.get("severity", "low")),
        )

        # ── Title ────────────────────────────────────────────────────────────
        story.append(Paragraph("Code Analysis Report", title_style))
        story.append(
            Paragraph(
                f"Generated for: {report.get('filename', 'Unknown file')}",
                subtitle_style,
            )
        )

        # ── 1. Executive Summary ─────────────────────────────────────────────
        story.append(
            KeepTogether(
                [
                    Paragraph("1. Executive Summary", heading_style),
                    Paragraph(PDFReportService._build_executive_summary(report), body_style),
                ]
            )
        )

        # ── 2. Overall Code Quality & Security Scores ────────────────────────
        quality = int(report.get("quality_score", 0) or 0)
        security = int(report.get("security_score", 0) or 0)
        score_data = [
            ["Metric", "Score", "Rating"],
            [
                "Code Quality",
                f"{quality}/100",
                PDFReportService._score_rating(quality),
            ],
            [
                "Security",
                f"{security}/100",
                PDFReportService._score_rating(security),
            ],
        ]
        score_table = Table(score_data, colWidths=[2.2 * inch, 1.6 * inch, 2.2 * inch])
        score_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), _LIGHT_BG),
                    ("TEXTCOLOR", (0, 0), (-1, -1), _DARK),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                    ("GRID", (0, 0), (-1, -1), 0.5, _BORDER),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(
            KeepTogether(
                [
                    Paragraph("2. Overall Code Quality & Security Scores", heading_style),
                    score_table,
                ]
            )
        )

        # ── 3. Findings Summary ──────────────────────────────────────────────
        critical = int(sev_dist.get("critical", 0) or 0)
        high = int(sev_dist.get("high", 0) or 0)
        medium = int(sev_dist.get("medium", 0) or 0)
        low = int(sev_dist.get("low", 0) or 0)
        info = int(sev_dist.get("info", 0) or 0)

        if findings:
            findings_summary = (
                f"This analysis identified {len(findings)} issue(s) in total: "
                f"{critical} CRITICAL, {high} HIGH, {medium} MEDIUM, {low} LOW and {info} INFO severity. "
            )
            if critical + high > 0:
                findings_summary += (
                    "The CRITICAL and HIGH severity issues require immediate attention and should be "
                    "resolved before the code is deployed."
                )
            elif medium > 0:
                findings_summary += (
                    "The MEDIUM severity issues should be addressed before the code is considered "
                    "production-ready."
                )
            else:
                findings_summary += (
                    "The remaining issues are minor and can be addressed as part of routine maintenance."
                )
        else:
            findings_summary = "No issues were identified in the code analysis. The code appears to be in good shape."

        story.append(
            KeepTogether(
                [
                    Paragraph("3. Findings Summary", heading_style),
                    Paragraph(findings_summary, body_style),
                ]
            )
        )

        # ── 4. Severity Breakdown ────────────────────────────────────────────
        sev_labels = ["critical", "high", "medium", "low", "info"]
        meanings = {
            "critical": "Must be fixed immediately",
            "high": "Should be fixed before deployment",
            "medium": "Should be fixed soon",
            "low": "Minor issue, fix when convenient",
            "info": "Informational only",
        }
        sev_data = [["Severity", "Count", "Meaning"]]
        for sev in sev_labels:
            count = int(sev_dist.get(sev, 0) or 0)
            if count:
                sev_data.append(
                    [
                        PDFReportService._severity_label(sev),
                        str(count),
                        meanings.get(sev, ""),
                    ]
                )
        if len(sev_data) > 1:
            sev_table = Table(sev_data, colWidths=[1.4 * inch, 0.9 * inch, 3.7 * inch])
            sev_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), _LIGHT_BG),
                        ("TEXTCOLOR", (0, 0), (-1, -1), _DARK),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                        ("GRID", (0, 0), (-1, -1), 0.5, _BORDER),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ]
                )
            )
            story.append(
                KeepTogether(
                    [
                        Paragraph("4. Severity Breakdown", heading_style),
                        sev_table,
                    ]
                )
            )
        else:
            story.append(
                KeepTogether(
                    [
                        Paragraph("4. Severity Breakdown", heading_style),
                        Paragraph("No severity data is available for this report.", body_style),
                    ]
                )
            )

        # ── 5. Detailed Findings ─────────────────────────────────────────────
        story.append(Paragraph("5. Detailed Findings", heading_style))

        if sorted_findings:
            for idx, finding in enumerate(sorted_findings, start=1):
                summary = PDFReportService._build_finding_summary(finding)
                finding_block: list[Any] = [Paragraph(f"{idx}. {summary}", body_style)]
                evidence = PDFReportService._build_evidence(finding)
                if evidence:
                    finding_block.append(
                        Paragraph(
                            f"<font color='#64748b'>Evidence: {evidence}</font>",
                            small_style,
                        )
                    )
                remediation = PDFReportService._build_remediation_text(finding)
                if remediation:
                    finding_block.append(
                        Paragraph(
                            f"<font color='#2563eb'>Remediation: {remediation}</font>",
                            small_style,
                        )
                    )
                finding_block.append(Spacer(1, 3))
                story.append(KeepTogether(finding_block))
        else:
            story.append(
                Paragraph(
                    "No issues were found in the code analysis. The code appears to be in good shape.",
                    body_style,
                )
            )

        # ── 6. Recommended Remediation / Roadmap ─────────────────────────────
        story.append(Paragraph("6. Recommended Remediation / Roadmap", heading_style))

        roadmap = report.get("metadata", {}).get("remediation_roadmap") if isinstance(report.get("metadata"), dict) else None
        if not roadmap and sorted_findings:
            roadmap = []
            for idx, finding in enumerate(sorted_findings, start=1):
                roadmap.append(PDFReportService._build_roadmap_item(finding, idx))
        if roadmap:
            for item in roadmap:
                story.append(Paragraph(item, body_style))
        else:
            story.append(
                Paragraph(
                    "No remediation steps are required at this time.",
                    body_style,
                )
            )

        # ── 7. PR Summary ────────────────────────────────────────────────────
        pr_summary = PDFReportService._build_pr_summary(report)
        if pr_summary:
            story.append(
                KeepTogether(
                    [
                        Paragraph("7. PR Summary", heading_style),
                        Paragraph(pr_summary, body_style),
                    ]
                )
            )

        # ── Footer ───────────────────────────────────────────────────────────
        story.append(Spacer(1, 16))
        story.append(
            Paragraph(
                "Generated by the Development of Smart Code Inspection Platform with Vulnerability Detection System.",
                small_style,
            )
        )

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()