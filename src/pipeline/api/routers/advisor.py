"""Router REST del historial de recomendaciones del Advisor."""

from __future__ import annotations

from fastapi import APIRouter, Query, Request

from src.pipeline.api.advisor_store import (
    AdvisorHistoryStore,
    AdvisorRecommendationRecordDTO,
)

router = APIRouter(prefix="/api/v1/advisor", tags=["advisor"])


def _store(request: Request) -> AdvisorHistoryStore:
    return request.app.state.advisor_store  # type: ignore[no-any-return]


@router.get(
    "/recommendations",
    response_model=list[AdvisorRecommendationRecordDTO],
)
async def list_recommendations(
    request: Request,
    limit: int = Query(default=50, ge=1, le=200),
) -> list[AdvisorRecommendationRecordDTO]:
    """Lista las recomendaciones más recientes (más nueva primero)."""
    return _store(request).list_recent(limit=limit)
