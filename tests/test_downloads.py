import json
from dataclasses import asdict

import pytest

from nightcity.core import Store, Card
from nightcity.downloads import DownloadCooldown
from nightcity.services import Catalog, Prices


def test_cooldown_persists_and_sources_are_independent(tmp_path):
    path = tmp_path / "binder.db"
    now = [10000]
    store = Store(path)
    cooldown = DownloadCooldown(store, lambda: now[0])
    assert cooldown.start("netdeck")
    assert cooldown.countdown("netdeck") == "60:00"
    assert not cooldown.start("netdeck")
    assert cooldown.start("cardmarket")
    store.close()
    store = Store(path)
    cooldown = DownloadCooldown(store, lambda: now[0])
    now[0] += 3599
    assert cooldown.countdown("netdeck") == "00:01"
    now[0] += 1
    assert cooldown.countdown("netdeck") == "00:00"
    assert cooldown.start("netdeck")
    assert cooldown.remaining("cardmarket") == 0
    store.close()


def test_local_refresh_reads_disk_without_network_or_rewriting(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Local refresh attempted a network call")
    monkeypatch.setattr("nightcity.services.fetch_json", forbidden)
    monkeypatch.setattr("nightcity.services.fetch_bytes", forbidden)
    card = Card("a", "a", "V", "set", "Set", "001")
    catalog = Catalog(tmp_path)
    catalog.path.write_text(json.dumps({"cards": [asdict(card)]}), encoding="utf-8")
    assert catalog.reload() == 1
    assert catalog.cards == [card]
    prices = Prices(tmp_path)
    data = {"schema_version": 1, "quotes": [{"printing_id": "a", "finish": "normal",
            "amount": "3.25", "currency": "EUR", "date": "2026-09-24",
            "source": "Cardmarket", "metric": "trend"}]}
    prices.path.write_text(json.dumps(data), encoding="utf-8")
    before = prices.path.stat().st_mtime_ns
    prices.reload()
    assert prices.quote("a", "normal")["amount"] == "3.25"
    assert prices.path.stat().st_mtime_ns == before
    prices.path.write_text('{"schema_version": 99}', encoding="utf-8")
    with pytest.raises(ValueError):
        prices.reload()
    assert prices.quote("a", "normal")["amount"] == "3.25"


def test_missing_local_files_do_not_fetch(tmp_path, monkeypatch):
    monkeypatch.setattr("nightcity.services.fetch_json", lambda *_: pytest.fail("Unexpected download"))
    with pytest.raises(FileNotFoundError):
        Catalog(tmp_path).reload()
    with pytest.raises(FileNotFoundError):
        Prices(tmp_path).reload()
