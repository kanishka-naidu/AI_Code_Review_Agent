from __future__ import annotations

from fastapi import APIRouter, Response

from app.core.metrics import metrics_export

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("")
async def metrics() -> Response:
    data, content_type = metrics_export()
    return Response(content=data, media_type=content_type)
