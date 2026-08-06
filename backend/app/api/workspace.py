"""Research Workspace FastAPI endpoints."""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session
from app.research_workspace import (
    BatchItemsRequest,
    DuplicateCheckResponse,
    ItemCreate,
    ItemUpdate,
    MultiOfferCompareReport,
    MultiOfferCompareRequest,
    SessionCreate,
    SessionResponse,
    WorkspaceItemResponse,
    add_item_to_workspace,
    batch_delete_items,
    batch_move_items,
    check_duplicate_offer,
    compare_multi_offers,
    compute_change_detection,
    create_session,
    delete_workspace_item,
    execute_item_analysis,
    get_or_create_default_session,
    list_sessions,
    list_workspace_items,
    update_workspace_item,
)
from app.research_workspace.schemas import ChangeDetectionReport
from app.research_workspace.service import DuplicateOfferException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/workspace", tags=["Research Workspace"])


@router.get("/sessions", response_model=list[SessionResponse])
async def list_sessions_endpoint(
    session: AsyncSession = Depends(get_session),
) -> list[SessionResponse]:
    """Get all active research sessions."""
    await get_or_create_default_session(session)
    return await list_sessions(session)


@router.post("/sessions", response_model=SessionResponse)
async def create_session_endpoint(
    payload: SessionCreate,
    session: AsyncSession = Depends(get_session),
) -> SessionResponse:
    """Create a new research session."""
    return await create_session(session, payload)


@router.get("/items", response_model=list[WorkspaceItemResponse])
async def list_workspace_items_endpoint(
    session_id: str = Query(...),
    session: AsyncSession = Depends(get_session),
) -> list[WorkspaceItemResponse]:
    """Fetch all workspace items for a given session."""
    return await list_workspace_items(session, session_id)


@router.post("/items/check-duplicate", response_model=DuplicateCheckResponse)
async def check_duplicate_endpoint(
    url: str = Query(...),
    session_id: str = Query(...),
    session: AsyncSession = Depends(get_session),
) -> DuplicateCheckResponse:
    """Check if an offer URL already exists in workspace."""
    return await check_duplicate_offer(session, url, session_id)


@router.post("/items", response_model=WorkspaceItemResponse)
async def add_item_endpoint(
    payload: ItemCreate,
    session: AsyncSession = Depends(get_session),
):
    """Add an offer URL to a research workspace session and run initial analysis."""
    if not payload.offer_url or not payload.offer_url.strip():
        raise HTTPException(status_code=400, detail="Nie podano adresu URL oferty.")
    try:
        return await add_item_to_workspace(session, payload)
    except DuplicateOfferException as exc:
        return JSONResponse(
            status_code=409,
            content=exc.duplicate_info.model_dump(mode="json"),
        )
    except Exception as exc:
        logger.exception("Failed to add workspace item: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.patch("/items/{item_id}", response_model=WorkspaceItemResponse)
async def update_item_endpoint(
    item_id: str,
    payload: ItemUpdate,
    session: AsyncSession = Depends(get_session),
) -> WorkspaceItemResponse:
    """Update workspace item properties (tags, notes, is_pinned)."""
    try:
        return await update_workspace_item(session, item_id, payload)
    except Exception as exc:
        logger.exception("Failed to update item %s: %s", item_id, exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.delete("/items/{item_id}")
async def delete_item_endpoint(
    item_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Delete a workspace item."""
    await delete_workspace_item(session, item_id)
    return {"status": "success", "message": "Oferta została usunięta z workspace."}


@router.post("/items/batch-delete")
async def batch_delete_items_endpoint(
    payload: BatchItemsRequest,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Delete multiple workspace items in batch."""
    count = await batch_delete_items(session, payload.item_ids)
    return {"status": "success", "count": count, "message": f"Usunięto {count} ofert."}


@router.post("/items/batch-move")
async def batch_move_items_endpoint(
    payload: BatchItemsRequest,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Move multiple workspace items to another session."""
    if not payload.target_session_id:
        raise HTTPException(status_code=400, detail="Nie wskazano sesji docelowej.")
    count = await batch_move_items(session, payload.item_ids, payload.target_session_id)
    return {"status": "success", "count": count, "message": f"Przeniesiono {count} ofert."}


@router.post("/items/{item_id}/analyze", response_model=WorkspaceItemResponse)
async def reanalyze_item_endpoint(
    item_id: str,
    session: AsyncSession = Depends(get_session),
) -> WorkspaceItemResponse:
    """Re-run analysis for a workspace item and store in history."""
    try:
        return await execute_item_analysis(session, item_id)
    except Exception as exc:
        logger.exception("Failed to reanalyze item %s: %s", item_id, exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/items/{item_id}/change-detection", response_model=ChangeDetectionReport)
async def change_detection_endpoint(
    item_id: str,
    session: AsyncSession = Depends(get_session),
) -> ChangeDetectionReport:
    """Compute change detection deltas between historical analysis runs."""
    return await compute_change_detection(session, item_id)


@router.post("/compare", response_model=MultiOfferCompareReport)
async def compare_multi_offers_endpoint(
    payload: MultiOfferCompareRequest,
    session: AsyncSession = Depends(get_session),
) -> MultiOfferCompareReport:
    """Perform side-by-side comparison for 2 to 6 workspace items."""
    if len(payload.item_ids) < 2 or len(payload.item_ids) > 6:
        raise HTTPException(
            status_code=400,
            detail="Porównanie wymaga wyboru od 2 do 6 ofert jednocześnie.",
        )
    try:
        return await compare_multi_offers(session, payload.item_ids)
    except Exception as exc:
        logger.exception("Failed to compare items %s: %s", payload.item_ids, exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
