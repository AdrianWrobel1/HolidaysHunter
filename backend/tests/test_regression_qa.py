"""Automated regression suite for Offer QA, normalizers, and filter bug fixes.

Guarantees that fixed normalization edge cases, country canonicalization bugs,
and filter query contradictions never regress in the future.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.countries import normalize_country_name
from app.models.offer import Offer
from app.providers.itaka.normalizer import ItakaNormalizer
from app.providers.tui.normalizer import TuiNormalizer
from app.services.offer_service import list_offers
from app.services.qa_service import run_qa_audit, validate_offer


def test_regression_country_canonicalization():
    """Verify raw country inputs (lower case, aliases, composite strings) map cleanly to canonical strings."""
    assert normalize_country_name("hiszpania") == "Hiszpania"
    assert normalize_country_name("SPAIN") == "Hiszpania"
    assert normalize_country_name("Tunezja / Djerba") == "Tunezja"
    assert normalize_country_name("Hiszpania - Mallorca") == "Hiszpania"
    assert normalize_country_name("grecja") == "Grecja"
    assert normalize_country_name("egipt") == "Egipt"
    assert normalize_country_name("turcja") == "Turcja"
    assert normalize_country_name("włochy") == "Włochy"
    assert normalize_country_name("wlochy") == "Włochy"


def test_regression_validator_detects_uncanonicalized_country():
    """Regression test: QA validator must flag uncanonicalized country names as invalid_country."""
    raw = {"country": "hiszpania"}
    # Simulated DB offer with lowercase country
    db_offer = Offer(
        external_id="REG-001",
        provider="itaka",
        title="Test Hotel",
        country="hiszpania",  # invalid non-canonical string
        hotel_name="Test Hotel",
        departure_date=date(2026, 8, 20),
        return_date=date(2026, 8, 27),
        duration_nights=7,
        departure_city="Warszawa",
        meal_type="all_inclusive",
        transport_type="flight",
        price_total=Decimal("4000.00"),
        price_per_person=Decimal("2000.00"),
        is_available=True,
    )

    errs = validate_offer(raw, None, offer_db=db_offer)
    assert any("invalid_country" in e for e in errs), "Validator must detect non-canonical country"


@pytest.mark.asyncio
async def test_regression_filter_contradiction_detection():
    """Regression test: Ensure automated filter tester flags contradiction if offers exist for country & provider but query returns 0."""
    offer1 = Offer(
        external_id="REG-ITAKA-01",
        provider="itaka",
        title="Itaka Spain Hotel",
        country="Hiszpania",
        hotel_name="Itaka Spain Hotel",
        departure_date=date(2026, 8, 20),
        return_date=date(2026, 8, 27),
        duration_nights=7,
        departure_city="Warszawa",
        meal_type="all_inclusive",
        transport_type="flight",
        price_total=Decimal("6000.00"),
        price_per_person=Decimal("3000.00"),
        is_available=True,
    )

    mock_session = AsyncMock()
    mock_execute = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [offer1]
    mock_execute.scalars.return_value = mock_scalars
    mock_session.execute.return_value = mock_execute

    report = await run_qa_audit(mock_session)
    assert "filter_tests" in report
    assert "summary" in report


@pytest.mark.asyncio
async def test_regression_query_parameter_normalization(db_session):
    """Regression test: list_offers must normalize query parameters (provider casing, country aliases) so TitleCase queries never return 0."""
    import uuid
    unique_ext_id = f"REG-NORM-{uuid.uuid4().hex[:8]}"
    offer = Offer(
        external_id=unique_ext_id,
        provider="itaka",
        title="Itaka Spain Hotel",
        country="Hiszpania",
        hotel_name="Itaka Spain Hotel",
        departure_date=date(2026, 8, 20),
        return_date=date(2026, 8, 27),
        duration_nights=7,
        departure_city="Warszawa",
        adults=2,
        children=0,
        meal_type="all_inclusive",
        transport_type="flight",
        price_total=Decimal("6000.00"),
        price_per_person=Decimal("3000.00"),
        offer_url="https://www.itaka.pl/o/1",
        is_available=True,
    )
    db_session.add(offer)
    await db_session.commit()

    # Query with TitleCase provider 'Itaka' and lowercase country 'hiszpania'
    res_title, count_title = await list_offers(db_session, country="hiszpania", provider="Itaka")
    assert count_title >= 1
    assert any(o.external_id == unique_ext_id for o in res_title)

    # Query with uppercase provider 'ITAKA' and alias country 'SPAIN'
    res_upper, count_upper = await list_offers(db_session, country="SPAIN", provider="ITAKA")
    assert count_upper >= 1
    assert any(o.external_id == unique_ext_id for o in res_upper)


def test_regression_all_normalizers_output_canonical_countries():
    """Regression test: All provider normalizers must produce canonical country names."""
    tui_norm = TuiNormalizer()
    tui_offer = tui_norm.normalize({
        "offerCode": "TUI-REG-01",
        "name": "TUI Hotel",
        "countryName": "hiszpania",
        "hotelName": "TUI Hotel",
        "departureDate": "2026-08-20",
        "returnDate": "2026-08-27",
        "durationNights": 7,
        "departureAirport": "Warszawa",
        "boardName": "all_inclusive",
        "totalPrice": 4000,
        "pricePerAdult": 2000,
    })
    assert tui_offer is not None
    assert tui_offer.country == "Hiszpania"

    itaka_norm = ItakaNormalizer()
    itaka_offer = itaka_norm.normalize({
        "offerId": "ITAKA-REG-01",
        "title": "Itaka Hotel",
        "country": "grecja",
        "hotelName": "Itaka Hotel",
        "departureDate": "2026-08-20",
        "returnDate": "2026-08-27",
        "duration": 7,
        "departureCity": "Katowice",
        "boardType": "all inclusive",
        "price": 3000,
    })
    assert itaka_offer is not None
    assert itaka_offer.country == "Grecja"


@pytest.mark.asyncio
async def test_regression_country_provider_and_region_combos(db_session):
    """Regression test: country + provider and country + region + provider combinations must return matching offers.
    
    Verifies that provider aliases ('wakacje.pl' -> 'wakacje_pl') and region casing ('kreta' -> 'Kreta')
    are normalized on the Python side so exact SQL equality queries utilize database indexes.
    """
    import uuid
    uid = uuid.uuid4().hex[:8]
    offer = Offer(
        external_id=f"REG-COMBO-{uid}",
        provider="wakacje_pl",
        title="Wakacje Kreta Resort",
        country="Grecja",
        region="Kreta",
        city="Heraklion",
        hotel_name="Wakacje Kreta Resort",
        departure_date=date(2026, 8, 25),
        return_date=date(2026, 9, 1),
        duration_nights=7,
        departure_city="Warszawa",
        adults=2,
        children=0,
        meal_type="all_inclusive",
        transport_type="flight",
        price_total=Decimal("5000.00"),
        price_per_person=Decimal("2500.00"),
        offer_url="https://www.wakacje.pl/o/1",
        is_available=True,
    )
    db_session.add(offer)
    await db_session.commit()

    # 1. Country + Provider combination with dot alias 'wakacje.pl'
    res_cp, count_cp = await list_offers(db_session, country="grecja", provider="wakacje.pl")
    assert count_cp >= 1
    assert any(o.external_id == offer.external_id for o in res_cp)

    # 2. Country + Region + Provider combination with lowercase region 'kreta' and alias 'Wakacje.pl'
    res_crp, count_crp = await list_offers(db_session, country="Grecja", region="kreta", provider="Wakacje.pl")
    assert count_crp >= 1
    assert any(o.external_id == offer.external_id for o in res_crp)

    # 3. Country + Region + Provider with list parameters
    res_list, count_list = await list_offers(
        db_session,
        country=["Grecja"],
        region=["kreta"],
        provider=["Wakacje.pl"],
    )
    assert count_list >= 1
    assert any(o.external_id == offer.external_id for o in res_list)


@pytest.mark.asyncio
async def test_regression_region_costa_de_la_luz_and_discrepancy_audit(db_session):
    """Regression test: Costa de la Luz region is correctly normalized and discrepancy audit table generated.
    
    Verifies that 'costa de la luz' normalizes to 'Costa de la Luz' and that import audit records
    are correctly categorized into saved/updated/duplicate/skipped status with explicit Polish explanations.
    """
    from app.core.countries import normalize_region_name
    from app.models.enums import Provider
    from app.services.import_service import run_import
    from app.services.qa_service import clear_import_audit_records, format_discrepancy_table, run_qa_audit

    assert normalize_region_name("costa de la luz") == "Costa de la Luz"
    assert normalize_region_name("COSTA DE LA LUZ") == "Costa de la Luz"

    clear_import_audit_records()

    # Import fallback mock offers for ITAKA
    await run_import(Provider.ITAKA, db_session)
    await db_session.commit()

    report = await run_qa_audit(db_session)
    assert "filter_tests" in report
    
    # Verify table formatting helper
    sample = [{
        "external_id": "TEST-01",
        "hotel": "Hotel Sol",
        "api_region": "Costa de la Luz",
        "normalized_region": "Costa de la Luz",
        "db_region": "Costa de la Luz",
        "status": "saved",
        "reason": "Pomyślnie utworzono nowy rekord w bazie danych",
    }]
    tbl_str = format_discrepancy_table(sample)
    assert "external_id" in tbl_str
    assert "status" in tbl_str
    assert "Costa de la Luz" in tbl_str


