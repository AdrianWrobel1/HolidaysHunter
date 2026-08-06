"""Admin endpoints for Offer Analyzer and system diagnostics."""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session
from app.offer_analyzer.models import OfferAnalyzeRequest, OfferAnalysisReport
from app.offer_analyzer.service import analyze_offer_url

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Admin Offer Analyzer"])


@router.post("/analyze-offer", response_model=OfferAnalysisReport)
async def analyze_offer_endpoint(
    payload: OfferAnalyzeRequest,
    session: AsyncSession = Depends(get_session),
) -> OfferAnalysisReport:
    """Analyze travel offer from URL using Universal Analysis Framework.

    Body:
        { "url": "https://www.itaka.pl/wczasy/..." }

    Returns comprehensive OfferAnalysisReport with statistical metrics,
    similarity breakdown, Deal Score (0-100), deterministic recommendation,
    and pre-binned chart visualization data.
    """
    if not payload.url or not payload.url.strip():
        raise HTTPException(status_code=400, detail="Nie podano poprawnego adresu URL oferty.")

    try:
        report = await analyze_offer_url(payload.url.strip(), session=session)
        return report
    except Exception as exc:
        logger.exception("Error analyzing offer URL '%s': %s", payload.url, exc)
        raise HTTPException(
            status_code=500,
            detail=f"Wystąpił błąd podczas analizy oferty: {str(exc)}",
        ) from exc
