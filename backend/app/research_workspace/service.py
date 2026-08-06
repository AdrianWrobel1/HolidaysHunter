"""Service for Research Workspace managing sessions, items, analysis history, change detection, snapshots, and comparison."""

import asyncio
from datetime import datetime, timezone
import json
import logging
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workspace import (
    ResearchSession,
    WorkspaceAnalysisHistory,
    WorkspaceCollection,
    WorkspaceItem,
    WorkspaceSnapshot,
)
from app.offer_analyzer.models import OfferAnalysisReport
from app.offer_analyzer.service import analyze_offer_url
from app.research_workspace.schemas import (
    ChangeDelta,
    ChangeDetectionReport,
    CollectionCreate,
    CollectionResponse,
    ComparisonMatrixRow,
    DuplicateCheckResponse,
    ItemCreate,
    ItemUpdate,
    MultiOfferCompareReport,
    SessionCreate,
    SessionResponse,
    SnapshotResponse,
    WorkspaceItemResponse,
)

logger = logging.getLogger(__name__)


class DuplicateOfferException(Exception):
    def __init__(self, duplicate_info: DuplicateCheckResponse):
        self.duplicate_info = duplicate_info
        super().__init__("Duplicate offer found in workspace.")


async def get_or_create_default_session(session: AsyncSession) -> ResearchSession:
    """Ensure at least one active ResearchSession exists."""
    stmt = select(ResearchSession).where(ResearchSession.is_active.is_(True)).order_by(ResearchSession.created_at.desc())
    res = await session.execute(stmt)
    active = res.scalars().first()
    if active:
        return active

    new_session = ResearchSession(
        name="Główna Sesja Badawcza",
        description="Domyślna sesja do wstępnej analizy i porównywania ofert.",
        is_active=True,
    )
    session.add(new_session)
    await session.commit()
    await session.refresh(new_session)
    return new_session


async def create_session(session: AsyncSession, data: SessionCreate) -> SessionResponse:
    rs = ResearchSession(name=data.name.strip(), description=data.description)
    session.add(rs)
    await session.commit()
    await session.refresh(rs)
    return SessionResponse(
        id=rs.id,
        name=rs.name,
        description=rs.description,
        is_active=rs.is_active,
        created_at=rs.created_at,
        updated_at=rs.updated_at,
        collections_count=0,
        items_count=0,
    )


async def list_sessions(session: AsyncSession) -> list[SessionResponse]:
    stmt = select(ResearchSession).order_by(ResearchSession.created_at.desc())
    res = await session.execute(stmt)
    sessions = res.scalars().all()
    results = []
    for s in sessions:
        results.append(
            SessionResponse(
                id=s.id,
                name=s.name,
                description=s.description,
                is_active=s.is_active,
                created_at=s.created_at,
                updated_at=s.updated_at,
                collections_count=len(s.collections),
                items_count=len(s.items),
            )
        )
    return results


async def list_workspace_items(
    session: AsyncSession, session_id: str
) -> list[WorkspaceItemResponse]:
    """Fetch all workspace items for a given session sorted by pinned status and update time."""
    stmt = (
        select(WorkspaceItem)
        .where(WorkspaceItem.session_id == session_id)
        .order_by(WorkspaceItem.is_pinned.desc(), WorkspaceItem.updated_at.desc())
    )
    res = await session.execute(stmt)
    items = list(res.scalars().all())

    results = []
    for item in items:
        all_reports = _get_reports_from_history(item.analysis_history)
        latest_report = all_reports[0] if all_reports else None
        results.append(_map_item_response(item, latest_report, all_reports))
    return results


async def check_duplicate_offer(
    session: AsyncSession, offer_url: str, current_session_id: str
) -> DuplicateCheckResponse:
    """Check if offer URL exists in current session or another session."""
    clean_url = offer_url.strip()
    stmt = select(WorkspaceItem).where(WorkspaceItem.offer_url == clean_url)
    res = await session.execute(stmt)
    existing = res.scalars().first()

    if not existing:
        return DuplicateCheckResponse(is_duplicate=False)

    s_stmt = select(ResearchSession).where(ResearchSession.id == existing.session_id)
    s_res = await session.execute(s_stmt)
    existing_session = s_res.scalar_one_or_none()

    return DuplicateCheckResponse(
        is_duplicate=True,
        existing_item_id=existing.id,
        existing_session_id=existing.session_id,
        existing_session_name=existing_session.name if existing_session else "Inna sesja",
        is_in_current_session=(existing.session_id == current_session_id),
    )


async def add_item_to_workspace(
    session: AsyncSession, data: ItemCreate
) -> WorkspaceItemResponse:
    clean_url = data.offer_url.strip()

    if not data.force:
        dup = await check_duplicate_offer(session, clean_url, data.session_id)
        if dup.is_duplicate:
            raise DuplicateOfferException(dup)

    item = WorkspaceItem(
        session_id=data.session_id,
        collection_id=data.collection_id,
        offer_url=clean_url,
        tags=data.tags or ["Observe"],
        notes=data.notes or [],
        is_pinned=False,
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)

    # Automatically run initial analysis via Universal Analysis Framework
    report = await analyze_offer_url(item.offer_url, session=session)
    history = WorkspaceAnalysisHistory(
        item_id=item.id,
        analysis_id=report.analysis_id,
        report_data=report.model_dump(mode="json"),
    )
    session.add(history)
    await session.commit()
    await session.refresh(item)

    return _map_item_response(item, report, [report])


async def execute_item_analysis(
    session: AsyncSession, item_id: str
) -> WorkspaceItemResponse:
    stmt = select(WorkspaceItem).where(WorkspaceItem.id == item_id)
    res = await session.execute(stmt)
    item = res.scalar_one_or_none()
    if not item:
        raise ValueError(f"WorkspaceItem '{item_id}' not found.")

    report = await analyze_offer_url(item.offer_url, session=session)
    history = WorkspaceAnalysisHistory(
        item_id=item.id,
        analysis_id=report.analysis_id,
        report_data=report.model_dump(mode="json"),
    )
    session.add(history)
    await session.commit()
    await session.refresh(item)

    all_reports = _get_reports_from_history(item.analysis_history)
    return _map_item_response(item, report, all_reports)


async def update_workspace_item(
    session: AsyncSession, item_id: str, data: ItemUpdate
) -> WorkspaceItemResponse:
    stmt = select(WorkspaceItem).where(WorkspaceItem.id == item_id)
    res = await session.execute(stmt)
    item = res.scalar_one_or_none()
    if not item:
        raise ValueError(f"WorkspaceItem '{item_id}' not found.")

    if data.is_pinned is not None:
        item.is_pinned = data.is_pinned
    if data.collection_id is not None:
        item.collection_id = data.collection_id
    if data.tags is not None:
        item.tags = data.tags
    if data.notes is not None:
        item.notes = data.notes

    await session.commit()
    await session.refresh(item)

    all_reports = _get_reports_from_history(item.analysis_history)
    latest_report = all_reports[0] if all_reports else None
    return _map_item_response(item, latest_report, all_reports)


async def delete_workspace_item(session: AsyncSession, item_id: str) -> None:
    stmt = select(WorkspaceItem).where(WorkspaceItem.id == item_id)
    res = await session.execute(stmt)
    item = res.scalar_one_or_none()
    if item:
        await session.delete(item)
        await session.commit()


async def batch_delete_items(session: AsyncSession, item_ids: list[str]) -> int:
    stmt = select(WorkspaceItem).where(WorkspaceItem.id.in_(item_ids))
    res = await session.execute(stmt)
    items = list(res.scalars().all())
    count = len(items)
    for i in items:
        await session.delete(i)
    await session.commit()
    return count


async def batch_move_items(
    session: AsyncSession, item_ids: list[str], target_session_id: str
) -> int:
    stmt = select(WorkspaceItem).where(WorkspaceItem.id.in_(item_ids))
    res = await session.execute(stmt)
    items = list(res.scalars().all())
    for i in items:
        i.session_id = target_session_id
    await session.commit()
    return len(items)


async def compute_change_detection(
    session: AsyncSession, item_id: str
) -> ChangeDetectionReport:
    stmt = select(WorkspaceItem).where(WorkspaceItem.id == item_id)
    res = await session.execute(stmt)
    item = res.scalar_one_or_none()
    if not item or not item.analysis_history:
        return ChangeDetectionReport(
            item_id=item_id,
            previous_analysis_id=None,
            latest_analysis_id="none",
            compared_at=datetime.now(timezone.utc),
            deltas=[],
            summary="Brak wystarczającej liczby historycznych analiz do porównania zmian.",
        )

    all_reports = _get_reports_from_history(item.analysis_history)
    if len(all_reports) < 2:
        latest = all_reports[0]
        return ChangeDetectionReport(
            item_id=item_id,
            previous_analysis_id=None,
            latest_analysis_id=latest.analysis_id,
            compared_at=datetime.now(timezone.utc),
            deltas=[],
            summary="Pierwsza analiza oferty — zmiana ceny będzie monitorowana przy kolejnych uruchomieniach.",
        )

    latest = all_reports[0]
    previous = all_reports[1]
    deltas = []

    # 1. Price delta
    old_p = float(previous.target_offer.price_per_person)
    new_p = float(latest.target_offer.price_per_person)
    p_diff = new_p - old_p
    if p_diff != 0:
        is_pos = p_diff < 0
        deltas.append(
            ChangeDelta(
                metric="Cena za osobę",
                old_value=f"{old_p:.0f} PLN",
                new_value=f"{new_p:.0f} PLN",
                diff_text=f"{p_diff:+.0f} PLN",
                is_positive=is_pos,
            )
        )

    # 2. Deal Score delta
    old_s = previous.deal_score.total_score
    new_s = latest.deal_score.total_score
    s_diff = new_s - old_s
    if s_diff != 0:
        deltas.append(
            ChangeDelta(
                metric="Deal Score",
                old_value=old_s,
                new_value=new_s,
                diff_text=f"{s_diff:+d} pkt",
                is_positive=s_diff > 0,
            )
        )

    # 3. Market position delta
    old_m = previous.market_position.cheaper_than_pct
    new_m = latest.market_position.cheaper_than_pct
    m_diff = new_m - old_m
    if abs(m_diff) >= 1.0:
        deltas.append(
            ChangeDelta(
                metric="Pozycja rynkowa (tańsza niż)",
                old_value=f"{old_m:.0f}%",
                new_value=f"{new_m:.0f}%",
                diff_text=f"{m_diff:+.0f}%",
                is_positive=m_diff > 0,
            )
        )

    summary = (
        f"Zaktualizowano {len(deltas)} metryk w stosunku do poprzedniego badania z "
        f"{previous.started_at.strftime('%Y-%m-%d %H:%M') if hasattr(previous.started_at, 'strftime') else str(previous.started_at)}."
    )

    return ChangeDetectionReport(
        item_id=item_id,
        previous_analysis_id=previous.analysis_id,
        latest_analysis_id=latest.analysis_id,
        compared_at=datetime.now(timezone.utc),
        deltas=deltas,
        summary=summary,
    )


async def compare_multi_offers(
    session: AsyncSession, item_ids: list[str]
) -> MultiOfferCompareReport:
    """Side-by-side comparison for 2 to 6 workspace items."""
    stmt = select(WorkspaceItem).where(WorkspaceItem.id.in_(item_ids))
    res = await session.execute(stmt)
    items = list(res.scalars().all())

    items_responses = []
    reports = []
    for item in items:
        all_r = _get_reports_from_history(item.analysis_history)
        latest_r = all_r[0] if all_r else None
        if not latest_r:
            latest_r = await analyze_offer_url(item.offer_url, session=session)
            history = WorkspaceAnalysisHistory(
                item_id=item.id,
                analysis_id=latest_r.analysis_id,
                report_data=latest_r.model_dump(mode="json"),
            )
            session.add(history)
            await session.commit()
            await session.refresh(item)
            all_r = [latest_r]

        reports.append(latest_r)
        items_responses.append(_map_item_response(item, latest_r, all_r))

    n = len(reports)
    if n == 0:
        raise ValueError("No items found to compare.")

    # Compute comparison matrix rows & best indices
    deal_scores = [r.deal_score.total_score for r in reports]
    prices_pp = [float(r.target_offer.price_per_person) for r in reports]
    prices_tot = [float(r.target_offer.price_total) for r in reports]
    daily_rates = [float(r.price_efficiency.person_daily_rate) for r in reports]
    stars_list = [float(r.target_offer.hotel_stars or 0) for r in reports]
    quality_scores = [float(r.offer_quality.quality_score) for r in reports]

    best_score_idx = deal_scores.index(max(deal_scores))
    cheapest_idx = prices_pp.index(min(prices_pp))
    highest_std_idx = stars_list.index(max(stars_list))

    # Best value = score / price ratio
    value_ratios = [
        (deal_scores[i] / prices_pp[i]) if prices_pp[i] > 0 else 0
        for i in range(n)
    ]
    best_value_idx = value_ratios.index(max(value_ratios))

    matrix = {
        "deal_score": ComparisonMatrixRow(
            label="Deal Score (0-100)",
            values=deal_scores,
            best_indices=[i for i, s in enumerate(deal_scores) if s == max(deal_scores)],
        ),
        "price_per_person": ComparisonMatrixRow(
            label="Cena za osobę (PLN)",
            values=[f"{p:.0f} PLN" for p in prices_pp],
            best_indices=[i for i, p in enumerate(prices_pp) if p == min(prices_pp)],
        ),
        "price_total": ComparisonMatrixRow(
            label="Cena łączna (PLN)",
            values=[f"{p:.0f} PLN" for p in prices_tot],
            best_indices=[i for i, p in enumerate(prices_tot) if p == min(prices_tot)],
        ),
        "daily_rate": ComparisonMatrixRow(
            label="Stawka dzienna za osobę",
            values=[f"{d:.0f} PLN/dzień" for d in daily_rates],
            best_indices=[i for i, d in enumerate(daily_rates) if d == min(daily_rates)],
        ),
        "hotel": ComparisonMatrixRow(
            label="Hotel i Standard",
            values=[
                f"{r.target_offer.hotel_name} ({r.target_offer.hotel_stars or '3'}★)"
                for r in reports
            ],
            best_indices=[i for i, s in enumerate(stars_list) if s == max(stars_list)],
        ),
        "meal_type": ComparisonMatrixRow(
            label="Wyżywienie",
            values=[r.target_offer.meal_type for r in reports],
            best_indices=[
                i for i, r in enumerate(reports) if "all" in r.target_offer.meal_type.lower()
            ],
        ),
        "departure": ComparisonMatrixRow(
            label="Wylot i Termin",
            values=[
                f"{r.target_offer.departure_city} ({r.target_offer.departure_date}, {r.target_offer.duration_nights}d)"
                for r in reports
            ],
            best_indices=[],
        ),
        "quality_score": ComparisonMatrixRow(
            label="Wskaźnik Jakości Oferty",
            values=[f"{q:.0f}/100" for q in quality_scores],
            best_indices=[i for i, q in enumerate(quality_scores) if q == max(quality_scores)],
        ),
        "provider": ComparisonMatrixRow(
            label="Organizator / Biuro",
            values=[r.target_offer.provider.upper() for r in reports],
            best_indices=[],
        ),
    }

    # Deterministic Trade-off Recommendation Engine
    if best_score_idx == cheapest_idx:
        upgrade_rec = f"Oferta {best_score_idx + 1} ({reports[best_score_idx].target_offer.hotel_name}) jest ZARÓWNO najtańsza, JAK I posiada najwyższy Deal Score ({deal_scores[best_score_idx]}/100) — absolutnie najlepszy wybór!"
    else:
        cheapest_p = prices_pp[cheapest_idx]
        best_p = prices_pp[best_score_idx]
        diff_p = best_p - cheapest_p
        score_diff = deal_scores[best_score_idx] - deal_scores[cheapest_idx]

        if diff_p <= 400 and score_diff >= 15:
            upgrade_rec = (
                f"Zdecydowanie warto dopłacić {diff_p:.0f} PLN do oferty {best_score_idx + 1} "
                f"({reports[best_score_idx].target_offer.hotel_name}). Dopłata zwiększa Deal Score z "
                f"{deal_scores[cheapest_idx]} do {deal_scores[best_score_idx]} pkt (+{score_diff} pts) i podnosi jakość wyjazdu."
            )
        else:
            upgrade_rec = (
                f"Dla szukających budżetu oferta {cheapest_idx + 1} ({reports[cheapest_idx].target_offer.hotel_name}) "
                f"za {cheapest_p:.0f} PLN jest najtańszym wyborem. Osoby szukające wyższego komfortu mogą rozważyć "
                f"ofertę {best_score_idx + 1} za {best_p:.0f} PLN."
            )

    return MultiOfferCompareReport(
        item_ids=item_ids,
        items=items_responses,
        matrix=matrix,
        best_overall_index=best_score_idx,
        best_value_index=best_value_idx,
        cheapest_index=cheapest_idx,
        highest_standard_index=highest_std_idx,
        upgrade_recommendation=upgrade_rec,
    )


def _get_reports_from_history(history_records: list[WorkspaceAnalysisHistory]) -> list[OfferAnalysisReport]:
    """Parse JSON history records into list of OfferAnalysisReport sorted newest first."""
    sorted_history = sorted(history_records, key=lambda h: h.executed_at, reverse=True)
    reports = []
    for h in sorted_history:
        try:
            r = OfferAnalysisReport.model_validate(h.report_data)
            reports.append(r)
        except Exception as exc:
            logger.warning("Could not parse historical report %s: %s", h.id, exc)
    return reports


def _map_item_response(
    item: WorkspaceItem,
    latest_report: OfferAnalysisReport | None,
    all_reports: list[OfferAnalysisReport],
) -> WorkspaceItemResponse:
    cd_report = None
    if len(all_reports) >= 2:
        latest = all_reports[0]
        prev = all_reports[1]
        deltas = []
        old_p = float(prev.target_offer.price_per_person)
        new_p = float(latest.target_offer.price_per_person)
        p_diff = new_p - old_p
        if p_diff != 0:
            deltas.append(
                ChangeDelta(
                    metric="Cena za osobę",
                    old_value=f"{old_p:.0f} PLN",
                    new_value=f"{new_p:.0f} PLN",
                    diff_text=f"{p_diff:+.0f} PLN",
                    is_positive=p_diff < 0,
                )
            )

        old_s = prev.deal_score.total_score
        new_s = latest.deal_score.total_score
        s_diff = new_s - old_s
        if s_diff != 0:
            deltas.append(
                ChangeDelta(
                    metric="Deal Score",
                    old_value=old_s,
                    new_value=new_s,
                    diff_text=f"{s_diff:+d} pkt",
                    is_positive=s_diff > 0,
                )
            )

        cd_report = ChangeDetectionReport(
            item_id=item.id,
            previous_analysis_id=prev.analysis_id,
            latest_analysis_id=latest.analysis_id,
            compared_at=datetime.now(timezone.utc),
            deltas=deltas,
            summary=f"Zmiany: {len(deltas)} metryki zaktualizowane",
        )

    return WorkspaceItemResponse(
        id=item.id,
        session_id=item.session_id,
        collection_id=item.collection_id,
        offer_url=item.offer_url,
        offer_id=item.offer_id,
        is_pinned=item.is_pinned,
        tags=item.tags or [],
        notes=item.notes or [],
        latest_report=latest_report,
        history_count=len(all_reports),
        change_detection=cd_report,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )
