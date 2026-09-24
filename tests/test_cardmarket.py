from copy import deepcopy
from dataclasses import replace

import pytest

from nightcity.cardmarket import make_feed, PRODUCTS_URL, GUIDE_URL
from nightcity.core import Card
from nightcity import services


@pytest.fixture
def source():
    card = Card("printing", "card", "V — Streetkid", "welcometonightcitybeta", "Beta", "β005")
    products = dict(version=1, createdAt="2026-09-23T12:31:37+0200", products=[
        dict(idProduct=123, idCategory=1661, idExpansion=6714, name="V - Streetkid")])
    guide = dict(version=1, createdAt="2026-09-22T02:49:16+0200", priceGuides=[
        {"idProduct": 123, "idCategory": 1661, "trend": 12.5, "trend-foil": 0, "avg7": 10}])
    return products, guide, card


def test_one_to_one_match_dates_and_missing_foil(source):
    products, guide, card = source
    feed = make_feed(products, guide, [card])
    assert feed["matches"] == {"printing": 123}
    assert len(feed["quotes"]) == 1
    q = feed["quotes"][0]
    assert (q["amount"], q["currency"], q["date"], q["finish"]) == ("12.5", "EUR", "2026-09-22", "normal")
    assert q["averages"] == dict(avg1=None, avg7="10", avg30=None)
    guide["priceGuides"][0]["trend-foil"] = 20
    assert make_feed(products, guide, [card])["quotes"][1]["amount"] == "20"


def test_no_name_only_join_or_cross_language_match(source):
    products, guide, card = source
    cards = [card, replace(card, printing_id="retail", set_code="welcometonightcityretail"),
             replace(card, printing_id="fr", language="fr"),
             replace(card, printing_id="starter", set_code="theheistbetastarterdeck")]
    feed = make_feed(products, guide, cards)
    assert len(feed["quotes"]) == 1
    assert feed["match_status"] == dict(printing="matched", retail="unsupported", fr="unsupported", starter="missing")


def test_ambiguous_products_or_printings_never_get_a_price(source):
    products, guide, card = source
    cards = [card, replace(card, printing_id="alt", number="β005b")]
    assert make_feed(products, guide, cards)["quotes"] == []
    products["products"].append({**products["products"][0], "idProduct": 124})
    feed = make_feed(products, guide, [card])
    assert feed["match_status"]["printing"] == "ambiguous"
    assert feed["quotes"] == []


@pytest.mark.parametrize("bad", [-1, "NaN", "Infinity", True, "oops"])
def test_invalid_price_preserves_saved_prices(source, tmp_path, bad):
    products, guide, card = source
    prices = services.Prices(tmp_path)
    prices.load_cardmarket(products, guide, [card])
    before = prices.path.read_bytes()
    guide["priceGuides"][0]["trend"] = bad
    with pytest.raises(ValueError):
        prices.load_cardmarket(products, guide, [card])
    assert prices.path.read_bytes() == before


def test_refresh_persistence_failure_and_older_snapshot(source, monkeypatch, tmp_path):
    products, guide, card = source
    prices = services.Prices(tmp_path)
    calls = []

    def fetch(url):
        calls.append(url)
        return products if url == PRODUCTS_URL else guide

    monkeypatch.setattr(services, "fetch_conditional_json", lambda url, *args: (fetch(url), "", ""))
    assert prices.refresh([card]) == 1
    assert calls == [PRODUCTS_URL, GUIDE_URL]
    saved = prices.path.read_bytes()
    prices.refresh([card])
    assert not prices.last_refresh_changed
    assert prices.path.read_bytes() == saved
    assert len(prices.history("printing", "normal")) == 1
    newer = deepcopy(guide)
    newer["createdAt"] = "2026-09-24T02:49:16+0200"
    newer["priceGuides"][0]["trend"] = 15
    prices.load_cardmarket(products, newer, [card])
    restored = services.Prices(tmp_path)
    assert [q["amount"] for q in restored.history("printing", "normal")] == ["12.5", "15"]
    with pytest.raises(ValueError):
        restored.load_cardmarket(products, guide, [card])
    before = restored.path.read_bytes()

    def broken(url):
        if url == GUIDE_URL:
            raise OSError("offline")
        return products

    monkeypatch.setattr(services, "fetch_conditional_json", lambda url, *args: (broken(url), "", ""))
    with pytest.raises(OSError):
        restored.refresh([card])
    assert restored.path.read_bytes() == before


def test_product_change_starts_new_series_and_no_price_is_not_zero(source, tmp_path):
    products, guide, card = source
    prices = services.Prices(tmp_path)
    prices.load_cardmarket(products, guide, [card])
    products["products"][0]["idProduct"] = guide["priceGuides"][0]["idProduct"] = 456
    guide["createdAt"] = "2026-09-24T02:49:16+0200"
    prices.load_cardmarket(products, guide, [card])
    assert len(prices.history("printing", "normal")) == 1
    assert prices.history("printing", "normal")[0]["product_id"] == 456
    guide["priceGuides"][0]["trend"] = None
    prices.load_cardmarket(products, guide, [card])
    assert prices.quote("printing", "normal") is None
    assert len(prices.data["history"]) == 2
    assert len(prices.history("printing", "normal")) == 1
    assert prices.history("printing", "normal")[0]["product_id"] == 456


def test_duplicates_and_invalid_schema(source):
    products, guide, card = source
    products["products"].append(products["products"][0])
    with pytest.raises(ValueError):
        make_feed(products, guide, [card])
    products["products"].pop()
    guide["priceGuides"].append(guide["priceGuides"][0])
    with pytest.raises(ValueError):
        make_feed(products, guide, [card])
    guide["priceGuides"] = []
    with pytest.raises(ValueError):
        make_feed(products, guide, [card])
