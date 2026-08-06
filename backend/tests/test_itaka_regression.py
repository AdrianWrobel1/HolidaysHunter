from pathlib import Path
from decimal import Decimal
import pytest
from app.models.enums import Provider
from app.providers.itaka.normalizer import ItakaNormalizer
from app.providers.itaka.provider import ItakaProvider

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "itaka_page_snapshot.html"


class TestItakaRegression:
    def setup_method(self) -> None:
        self.provider = ItakaProvider()
        self.normalizer = ItakaNormalizer()

    def test_parses_real_html_snapshot(self) -> None:
        """Regression test ensuring provider extracts and normalizes offers from real HTML snapshot."""
        assert FIXTURE_PATH.exists(), f"Fixture missing at {FIXTURE_PATH}"
        html_content = FIXTURE_PATH.read_text(encoding="utf-8")

        raw_offers = self.provider._extract_offers_from_html(html_content)
        assert len(raw_offers) > 0, "ITAKA provider returned 0 raw offers from snapshot!"
        assert len(raw_offers) == 15, f"Expected 15 offers from snapshot, got {len(raw_offers)}"

        normalized_offers = []
        for raw in raw_offers:
            norm = self.normalizer.normalize(raw)
            assert norm is not None, f"Failed to normalize offer: {raw.get('supplierObjectId') or raw.get('id')}"
            assert norm.provider == Provider.ITAKA
            assert norm.external_id is not None and len(norm.external_id) > 0
            assert norm.title is not None and len(norm.title) > 0
            assert norm.price_total > Decimal("0")
            assert norm.price_per_person > Decimal("0")
            assert norm.departure_date is not None
            assert norm.return_date is not None
            assert norm.departure_date <= norm.return_date
            assert norm.country == "Hiszpania"
            normalized_offers.append(norm)

        assert len(normalized_offers) == len(raw_offers)

    def test_fails_loudly_on_missing_next_data(self) -> None:
        """Ensures parser raises RuntimeError when __NEXT_DATA__ tag is missing."""
        invalid_html = "<html><body><h1>No data here</h1></body></html>"
        with pytest.raises(RuntimeError, match="script tag missing"):
            self.provider._extract_offers_from_html(invalid_html)

    def test_fails_loudly_on_unrecognized_schema(self) -> None:
        """Ensures parser raises RuntimeError when __NEXT_DATA__ contains no offer collection."""
        invalid_json_html = (
            '<html><head><script id="__NEXT_DATA__" type="application/json">'
            '{"props": {"pageProps": {"unknownContainer": {}}}}'
            '</script></head><body></body></html>'
        )
        with pytest.raises(RuntimeError, match="Failed to discover offer dataset"):
            self.provider._extract_offers_from_html(invalid_json_html)

    @pytest.mark.asyncio
    async def test_live_importer_against_production_website(self) -> None:
        """Run ITAKA live importer against production website and verify offer yield and schema integrity."""
        SNAPSHOT_COUNT = 15
        MIN_EXPECTED_OFFERS = max(1, int(SNAPSHOT_COUNT * 0.5))  # at least 50% of snapshot count (8)

        try:
            raw_offers = await self.provider.fetch_offers({"country": "Hiszpania"})

            if len(raw_offers) < MIN_EXPECTED_OFFERS:
                pytest.fail(
                    f"ITAKA live importer returned {len(raw_offers)} offers, which is below minimum threshold "
                    f"of {MIN_EXPECTED_OFFERS} (50% of snapshot count {SNAPSHOT_COUNT}). "
                    f"Drastic drop or 0 offers detected!"
                )

            assert len(raw_offers) >= MIN_EXPECTED_OFFERS

            normalized_offers = [self.normalizer.normalize(o) for o in raw_offers]
            valid_normalized = [n for n in normalized_offers if n is not None]

            assert len(valid_normalized) > 0, "Failed to normalize any live offers!"
            assert len(valid_normalized) == len(raw_offers), (
                f"Normalized {len(valid_normalized)} out of {len(raw_offers)} live offers."
            )
        finally:
            await self.provider.close()
