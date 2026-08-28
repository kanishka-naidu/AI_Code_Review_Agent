from enum import Enum


class Severity(str, Enum):
    """Canonical severity levels.

    Internal values remain lowercase so existing classification, scoring, and
    filtering logic is preserved. Display labels (used by the UI, PDF, and
    reports) are consistently uppercase: CRITICAL, HIGH, MEDIUM, LOW.
    """

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @property
    def label(self) -> str:
        """Return the canonical display label for this severity."""
        return self.value.upper()

    @classmethod
    def from_label(cls, value: str) -> "Severity":
        """Map a display label (e.g. 'CRITICAL') or internal value to Severity."""
        if not value:
            return cls.INFO
        return cls(value.lower())


# Canonical display labels used across the UI, PDF, and API responses.
SEVERITY_LABELS = {
    Severity.CRITICAL: "CRITICAL",
    Severity.HIGH: "HIGH",
    Severity.MEDIUM: "MEDIUM",
    Severity.LOW: "LOW",
    Severity.INFO: "INFO",
}


def severity_label(severity: Severity | str | None) -> str:
    """Return the canonical uppercase display label for a severity value."""
    if severity is None:
        return "LOW"
    if isinstance(severity, Severity):
        return SEVERITY_LABELS.get(severity, severity.value.upper())
    try:
        return SEVERITY_LABELS.get(Severity(severity.lower()), severity.upper())
    except (ValueError, AttributeError):
        return str(severity).upper()