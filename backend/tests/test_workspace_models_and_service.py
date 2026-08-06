"""Tests for Research Workspace persistence, service, change detection, and multi-offer comparison."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.research_workspace import (
    ItemCreate,
    ItemUpdate,
    SessionCreate,
    add_item_to_workspace,
    compare_multi_offers,
    compute_change_detection,
    create_session,
    execute_item_analysis,
    get_or_create_default_session,
    list_sessions,
    update_workspace_item,
)


@pytest.mark.asyncio
async def test_workspace_session_creation_and_listing(db_session: AsyncSession):
    default_s = await get_or_create_default_session(db_session)
    assert default_s.id is not None

    new_s = await create_session(db_session, SessionCreate(name="Egipt Wrzesień 2026", description="Test"))
    assert new_s.name == "Egipt Wrzesień 2026"

    all_sessions = await list_sessions(db_session)
    assert len(all_sessions) >= 2


@pytest.mark.asyncio
async def test_workspace_item_lifecycle_and_analysis_history(db_session: AsyncSession):
    s = await get_or_create_default_session(db_session)

    url = "https://www.itaka.pl/wczasy/hiszpania/teneryfa/hotel-playa-sur,987654.html"
    item_res = await add_item_to_workspace(
        db_session,
        ItemCreate(
            session_id=s.id,
            offer_url=url,
            tags=["Favorite", "Observe"],
            notes=["Dobra cena za All Inclusive"],
        ),
    )

    assert item_res.id is not None
    assert item_res.latest_report is not None
    assert item_res.history_count == 1
    assert "Favorite" in item_res.tags

    # Update item pin and notes
    updated_item = await update_workspace_item(
        db_session,
        item_res.id,
        ItemUpdate(is_pinned=True, notes=["Dobra cena za All Inclusive", "Czekamy na ocenę"]),
    )
    assert updated_item.is_pinned is True
    assert len(updated_item.notes) == 2

    # Run second analysis to trigger history & change detection
    reanalyzed = await execute_item_analysis(db_session, item_res.id)
    assert reanalyzed.history_count == 2

    cd_report = await compute_change_detection(db_session, item_res.id)
    assert cd_report.item_id == item_res.id
    assert cd_report.latest_analysis_id != ""


@pytest.mark.asyncio
async def test_side_by_side_multi_offer_comparison(db_session: AsyncSession):
    s = await get_or_create_default_session(db_session)

    item1 = await add_item_to_workspace(
        db_session,
        ItemCreate(session_id=s.id, offer_url="https://www.itaka.pl/wczasy/egipt/hotel-a"),
    )
    item2 = await add_item_to_workspace(
        db_session,
        ItemCreate(session_id=s.id, offer_url="https://www.tui.pl/wypoczynek/egipt/hotel-b"),
    )

    compare_report = await compare_multi_offers(db_session, [item1.id, item2.id])

    assert len(compare_report.items) == 2
    assert "deal_score" in compare_report.matrix
    assert "price_per_person" in compare_report.matrix
    assert compare_report.upgrade_recommendation != ""
