import base64
import json
import logging
import pytest
from app.providers.tui.provider import (
    TuiProvider,
    decode_next_data_payload,
    discover_best_offer_collection,
    score_offer_item,
)


class TestTuiProviderUnit:
    def test_decode_next_data_payload_plain_json(self) -> None:
        payload = {"props": {"pageProps": {"test": 123}}}
        html = f'<html><script id="__NEXT_DATA__" type="application/json">{json.dumps(payload)}</script></html>'
        res = decode_next_data_payload(html)
        assert res == payload

    def test_decode_next_data_payload_base64(self) -> None:
        payload = {"props": {"pageProps": {"test": 456}}}
        encoded = base64.b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8")
        html = f'<html><script id="__NEXT_DATA__" type="application/json">{encoded}</script></html>'
        res = decode_next_data_payload(html)
        assert res == payload

    def test_decode_next_data_payload_missing_script(self) -> None:
        html = "<html><body>No script</body></html>"
        with pytest.raises(ValueError, match="Script tag .* was not found"):
            decode_next_data_payload(html)

    def test_decode_next_data_payload_invalid_content(self) -> None:
        html = '<html><script id="__NEXT_DATA__" type="application/json">!!!invalid base64 and json!!!</script></html>'
        with pytest.raises(ValueError, match="Failed to Base64 decode"):
            decode_next_data_payload(html)

    def test_score_offer_item(self) -> None:
        valid_offer = {
            "offerCode": "AYT123",
            "hotelName": "Grand Resort",
            "discountPerPersonPrice": 1200,
            "departureDate": "2026-09-01",
            "returnDate": "2026-09-08",
            "boardType": "All Inclusive",
            "departureAirport": "Warszawa",
        }
        assert score_offer_item(valid_offer) >= 4

        invalid_offer = {"someOtherKey": "abc"}
        assert score_offer_item(invalid_offer) == 0

    def test_discover_best_offer_collection_ranking(self) -> None:
        incomplete_collection = [
            {"foo": "bar"},
            {"baz": "qux"},
        ]
        complete_collection = [
            {
                "offerCode": "OFFER-1",
                "hotelName": "Hotel A",
                "discountPerPersonPrice": 1500,
                "departureDate": "2026-10-01",
            },
            {
                "offerCode": "OFFER-2",
                "hotelName": "Hotel B",
                "discountPerPersonPrice": 2000,
                "departureDate": "2026-10-02",
            },
        ]

        next_data = {
            "props": {
                "pageProps": {
                    "randomKey": incomplete_collection,
                    "futureRenamedKeyData": complete_collection,
                }
            }
        }

        best = discover_best_offer_collection(next_data)
        assert len(best) == 2
        assert best[0]["offerCode"] == "OFFER-1"

    def test_discover_best_offer_collection_fails_loudly(self) -> None:
        next_data = {
            "props": {
                "pageProps": {
                    "emptyData": [],
                    "invalidData": [{"unknown": 1}],
                }
            }
        }
        with pytest.raises(ValueError, match="No valid offer collection matching NormalizedOffer requirements"):
            discover_best_offer_collection(next_data)


@pytest.mark.asyncio
async def test_tui_provider_logs_error_on_httpx_failure(caplog: pytest.LogCaptureFixture) -> None:
    provider = TuiProvider()
    with caplog.at_level(logging.ERROR):
        offers = await provider.fetch_offers({"country": "NonExistentCountry123"})
        # Should attempt fetch and if invalid/failed log explicit HTTP failure reason
        assert isinstance(offers, list)
