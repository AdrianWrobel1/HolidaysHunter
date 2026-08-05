"""Quality Assurance and Debug API router."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session
from app.services.qa_service import debug_offer_by_id, get_latest_qa_report, run_qa_audit

router = APIRouter(prefix="", tags=["debug-qa"])


@router.get("/debug/qa")
@router.get("/api/debug/qa")
async def get_qa_report_endpoint(
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Return the latest aggregate Quality Assurance import report.

    Contains validation counts, invalid offer error breakdown, automated filter test results,
    and lineage breakdown for invalid offers.
    """
    report = get_latest_qa_report()
    # If no report run yet, run audit on current DB state
    if report.get("summary", {}).get("total_imported", 0) == 0:
        report = await run_qa_audit(session)
    return report


@router.post("/debug/qa/run")
@router.post("/api/debug/qa/run")
async def run_qa_report_endpoint(
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Trigger an on-demand QA audit on current database offers."""
    report = await run_qa_audit(session)
    return {
        "status": "success",
        "message": "QA audit completed successfully.",
        "report": report,
    }


@router.get("/debug/offer/{identifier}")
@router.get("/api/debug/offer/{identifier}")
async def debug_single_offer_endpoint(
    identifier: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Debug a single offer by database UUID or provider external_id (e.g. TUI-PL-2026-001).

    Returns full 4-stage pipeline lineage:
    1. Raw API Payload
    2. NormalizedOffer Schema Representation
    3. DB Record Entity State
    4. Line-by-line Filter Results (PASS / FAIL explanations for every filter query).
    """
    result = await debug_offer_by_id(session, identifier)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
