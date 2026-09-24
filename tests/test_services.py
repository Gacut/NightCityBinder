import json

import pytest
from pathlib import Path

from nightcity import services
from nightcity.core import Card
from decimal import Decimal


def test_image_download_publishes_only_complete_file(monkeypatch, tmp_path):
    catalog = services.Catalog(tmp_path)
    card = Card("atomic", "a", "V", "s", "Set", "1",
                image_url="https://dstcynss47vun.cloudfront.net/test.png")
    destination = catalog.image_path(card)
    data = b"\x89PNG" + b"example bytes"
    monkeypatch.setattr(services, "fetch_bytes", lambda *a, **k: data)
    replace = services.os.replace

    def checked_replace(source, target):
        if Path(target) == destination:
            assert not destination.exists()
            assert Path(source).read_bytes() == data
        replace(source, target)

    monkeypatch.setattr(services.os, "replace", checked_replace)
    assert catalog.download_image(card) == str(destination)
    assert destination.read_bytes() == data
    assert not list(destination.parent.glob("*.part"))
    monkeypatch.setattr(services, "fetch_bytes", lambda *a, **k: pytest.fail("Downloaded cached art"))
    assert catalog.download_image(card) == str(destination)


def page(number=0, total=1):
    return {
        "total": total,
        "items": [
            {
                "id": f"card-{number}",
                "name": "V",
                "canonical_name": "V — Streetkid",
                "printings": [
                    {
                        "id": f"printing-{number}",
                        "collector_number": "005a",
                        "set": {"code": "retail", "name": "Retail"},
                        "finish": None,
                    }
                ],
            }
        ],
    }


def test_catalog_pagination_and_cache(monkeypatch, tmp_path):
    pages = iter([page(0, 2), page(1, 2)])
    monkeypatch.setattr(services, "fetch_conditional_json", lambda url, *args: (next(pages), "", ""))
    catalog = services.Catalog(tmp_path)
    progress = []
    assert catalog.refresh(lambda count, total: progress.append((count, total))) == 2
    assert progress == [(1, 2), (2, 2)]
    assert len(services.Catalog(tmp_path).cards) == 2
    monkeypatch.setattr(services, "fetch_conditional_json", lambda url, *args: ({"items": [], "total": 2}, "", ""))
    with pytest.raises(ValueError):
        catalog.refresh()
    assert len(services.Catalog(tmp_path).cards) == 2


def test_catalog_ignores_changed_image_signature(monkeypatch, tmp_path):
    data = page()
    printing = data["items"][0]["printings"][0]
    image = "https://dstcynss47vun.cloudfront.net/card.webp"
    printing["image_url"] = image + "?Expires=1"
    monkeypatch.setattr(services, "fetch_conditional_json", lambda *args: (data, "", ""))
    catalog = services.Catalog(tmp_path)
    catalog.refresh()
    assert catalog.last_refresh_changed
    saved = catalog.path.read_bytes()
    printing["image_url"] = image + "?Expires=2"
    catalog.refresh()
    assert not catalog.last_refresh_changed
    assert catalog.path.read_bytes() != saved  # keep a fresh signed URL for missing artwork


def test_nbp_cache_and_offline(monkeypatch, tmp_path):
    monkeypatch.setattr(
        services,
        "fetch_json",
        lambda url: [
            {
                "effectiveDate": "2026-09-22",
                "rates": [{"code": "EUR", "mid": 4.2}, {"code": "USD", "mid": 3.8}, {"code": "GBP", "mid": 5.1}],
            }
        ],
    )
    fx = services.ExchangeRates(tmp_path)
    assert fx.refresh() == "2026-09-22"
    assert services.ExchangeRates(tmp_path).convert(10, "EUR", "PLN") == 42


def test_quotes_require_exact_printing_and_finish(tmp_path):
    prices = services.Prices(tmp_path)
    quote = {
        "printing_id": "abc",
        "finish": "foil",
        "amount": "1.2",
        "currency": "EUR",
        "date": "2026-09-22",
        "source": "TEST ONLY",
        "metric": "market",
    }
    prices.load_feed(json.dumps({"schema_version": 1, "quotes": [quote]}))
    assert prices.quote("abc", "foil") == quote
    assert prices.quote("abc", "normal") is None
    assert prices.quote("abc", "unknown") is None
    assert prices.quote("xyz", "foil") is None
    with pytest.raises(ValueError):
        prices.load_feed(json.dumps({"schema_version": 1, "quotes": [quote, quote]}))


def test_price_history_is_daily_persistent_and_keeps_source_separate(tmp_path):
    prices = services.Prices(tmp_path)
    q = dict(printing_id="test", finish="normal", amount="2", currency="EUR",
             date="2026-09-22", source="TEST ONLY", metric="trend")

    def load(**changes):
        prices.load_feed(json.dumps({"schema_version": 1, "quotes": [{**q, **changes}]}))

    load()
    load(amount="3")
    assert len(prices.history("test", "normal")) == 1
    load(date="2026-09-24", amount="4")
    assert [x["date"] for x in prices.history("test", "normal")] == ["2026-09-22", "2026-09-24"]
    restored = services.Prices(tmp_path)
    assert [x["amount"] for x in restored.history("test", "normal")] == ["3", "4"]
    assert restored.history("test", "foil") == []
    load(source="OTHER TEST SOURCE")
    assert len(prices.history("test", "normal")) == 1


def test_invalid_price_date_does_not_replace_cache(tmp_path):
    prices = services.Prices(tmp_path)
    q = dict(printing_id="test", finish="foil", amount="2", currency="EUR",
             date="2026-09-22", source="TEST ONLY", metric="trend")
    prices.load_feed(json.dumps({"schema_version": 1, "quotes": [q]}))
    before = prices.path.read_bytes()
    q["date"] = "2026-02-31"
    with pytest.raises(ValueError):
        prices.load_feed(json.dumps({"schema_version": 1, "quotes": [q]}))
    assert prices.path.read_bytes() == before


def test_binder_value_counts_copies_variants_and_displayed_unit_prices(tmp_path):
    prices, fx = services.Prices(tmp_path), services.ExchangeRates(tmp_path)
    fx.data = {"rates": {"EUR": 4.2, "USD": 3.8, "PLN": 1}}
    card = Card("a", "a", "Test", "set", "Set", "1")
    q = dict(printing_id="a", finish="normal", amount="1.234", currency="EUR",
             date="2026-09-22", source="TEST ONLY", metric="Trend")
    prices.load_feed(json.dumps(dict(schema_version=1, quotes=[q, {**q, "finish": "foil", "amount": "3"}])))
    rows = [dict(card=card, finish="normal", quantity=3), dict(card=card, finish="foil", quantity=2),
            dict(card=card, finish="unknown", quantity=7)]
    result = prices.binder_value(rows, fx, "PLN")
    assert result == dict(amount=Decimal("40.74"), currency="PLN", missing=7, fx_missing=False)
    assert prices.binder_value([], fx, "PLN")["amount"] == 0
    assert prices.binder_value(rows[2:], fx, "PLN")["missing"] == 7
    fx.data = {}
    fallback = prices.binder_value(rows, fx, "PLN")
    assert fallback == dict(amount=Decimal("9.69"), currency="EUR", missing=7, fx_missing=True)
