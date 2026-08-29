from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from typing import Optional
from app.core.config import get_settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add common security headers to responses.

    CSP policy, HSTS, and other headers are configurable via Settings.
    The middleware will relax CSP for documentation routes when the application
    is running in debug mode to allow loading external Swagger UI assets (https:).
    Additional per-directive sources can be configured via environment.
    """

    DOCS_PATHS = ("/docs", "/redoc", "/openapi.json", "/swagger")

    def __init__(self, app, csp_policy: Optional[str] = None, hsts_seconds: int | None = None):
        super().__init__(app)
        settings = get_settings()
        self._base_csp = csp_policy or getattr(settings, "csp_policy", "")
        self._hsts = int(hsts_seconds or getattr(settings, "hsts_seconds", 0))
        self._settings = settings

    def _merge_directives(self, base: str, directive: str, additions: str) -> str:
        """Merge additions into a given directive within base CSP string.

        If directive not present, append it. Additions is a comma/space-separated string
        of tokens (like https://cdn.jsdelivr.net or 'unsafe-inline'). Returns the new CSP string.
        """
        if not additions:
            return base
        tokens = " ".join(tok for tok in (part.strip() for part in additions.split(",") if part.strip()))
        if directive in base:
            # naive insert: find directive and append tokens before the semicolon
            parts = []
            for part in base.split(";"):
                if part.strip().startswith(directive):
                    part = part.strip() + " " + tokens
                parts.append(part.strip())
            return "; ".join(p for p in parts if p)
        # append directive
        suffix = f"{directive} {tokens};"
        return base.strip() + (" " if base and not base.endswith(";") else "") + suffix

    def _csp_for_request(self, request: Request) -> str:
        base = self._base_csp or ""
        # Merge settings-based additional sources
        base = self._merge_directives(base, "script-src", getattr(self._settings, "csp_additional_script_src", ""))
        base = self._merge_directives(base, "style-src", getattr(self._settings, "csp_additional_style_src", ""))
        base = self._merge_directives(base, "img-src", getattr(self._settings, "csp_additional_img_src", ""))

        path = request.url.path
        if any(path.startswith(p) for p in self.DOCS_PATHS):
            base = self._merge_directives(base, "script-src", "https://cdn.jsdelivr.net")
            base = self._merge_directives(base, "style-src", "https://cdn.jsdelivr.net")
            base = self._merge_directives(base, "img-src", "https://cdn.jsdelivr.net data:")
        return base

    async def dispatch(self, request: Request, call_next):
        resp: Response = await call_next(request)
        csp = self._csp_for_request(request)
        if csp:
            resp.headers.setdefault("Content-Security-Policy", csp)
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Referrer-Policy", "no-referrer")
        if self._hsts and request.url.scheme == "https":
            resp.headers.setdefault("Strict-Transport-Security", f"max-age={self._hsts}; includeSubDomains; preload")
        return resp
