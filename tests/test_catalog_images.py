import json
from dataclasses import asdict

from nightcity.core import Card
from nightcity.services import Catalog, write_json


def fixture_catalog(tmp_path, monkeypatch, count):
    catalog = Catalog(tmp_path)
    cards = [Card(str(i), str(i), f"Card {i}", "s", "Set", str(i),
                  image_url=f"https://dstcynss47vun.cloudfront.net/{i}.webp?Expires=fresh")
             for i in range(count)]

    def refresh(progress=None):
        catalog.cards = cards
        write_json(catalog.path, {"cards": [asdict(c) for c in cards]})
        return count

    monkeypatch.setattr(catalog, "refresh", refresh)
    return catalog, cards


def test_downloads_all_missing_images_and_survives_restart(tmp_path, monkeypatch):
    catalog, cards = fixture_catalog(tmp_path, monkeypatch, 700)
    for card in cards[:62]:
        path = catalog.image_path(card)
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(b"\x89PNGsaved")
    fetched = []

    def fetch(url, **kwargs):
        fetched.append(url)
        return b"\x89PNGdownloaded"

    monkeypatch.setattr("nightcity.services.fetch_bytes", fetch)
    progress = []
    result = catalog.download_catalog(image_progress=lambda n, total: progress.append((n, total)))
    assert result["cached"] == 62
    assert result["downloaded"] == len(fetched) == 638
    assert result["available"] == 700 and result["missing"] == 0
    assert progress[0] == (0, 700) and progress[-1] == (700, 700)
    reopened = Catalog(tmp_path)
    reopened.reload()
    assert reopened.image_diagnostics()["missing_cards"] == 0
    # All images are reused on the next download, even with a fresh Catalog object.
    result = catalog.download_catalog()
    assert result["downloaded"] == 0 and len(fetched) == 638


def test_partial_download_preserves_files_and_can_resume(tmp_path, monkeypatch):
    catalog, cards = fixture_catalog(tmp_path, monkeypatch, 3)

    def fetch(url, **kwargs):
        if "/1.webp" in url:
            raise OSError("offline")
        return b"\x89PNGdownloaded"

    monkeypatch.setattr("nightcity.services.fetch_bytes", fetch)
    result = catalog.download_catalog()
    assert result["available"] == 2 and result["missing"] == 1
    assert result["failed"][0]["printing_id"] == "1"
    assert json.loads((tmp_path / "image-download-report.json").read_text())["missing"] == 1
    monkeypatch.setattr("nightcity.services.fetch_bytes", lambda *a, **k: b"\x89PNGrecovered")
    result = catalog.download_catalog()
    assert result["downloaded"] == 1 and result["cached"] == 2
    assert result["missing"] == 0


def test_failed_connection_does_not_retry_entire_catalog(tmp_path, monkeypatch):
    catalog, _ = fixture_catalog(tmp_path, monkeypatch, 20)

    def offline(*args, **kwargs):
        raise OSError("offline")

    monkeypatch.setattr("nightcity.services.fetch_bytes", offline)
    result = catalog.download_catalog()
    assert len(result["failed"]) == 5
    assert result["missing"] == 20 and result["not_attempted"] == 15
