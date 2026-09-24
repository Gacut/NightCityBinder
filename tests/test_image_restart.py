import json
from dataclasses import asdict, replace

from nightcity.core import Card
from nightcity.services import Catalog


def test_restart_reindexes_existing_images_and_signed_urls(tmp_path, monkeypatch):
    monkeypatch.setattr("nightcity.services.fetch_bytes", lambda *a, **k: (_ for _ in ()).throw(AssertionError("Network")))
    card = Card("e3775ed6-d3c1-47f1-a3f4-835003900d8d", "royce", "Royce — Psychoverdose",
                "retail-fr", "Retail FR", "143", language="fr",
                image_url="https://dstcynss47vun.cloudfront.net/prod/royce-fr.webp?Expires=100&Signature=old")
    catalog = Catalog(tmp_path)
    path = catalog.image_path(card)
    path.parent.mkdir()
    path.write_bytes(b"existing image")
    catalog.path.write_text(json.dumps({"cards": [asdict(card)]}), encoding="utf-8")
    restarted = Catalog(tmp_path)
    assert restarted.image_path(restarted.cards[0]) == path
    # Reissued URL / changed catalog identity still resolves the same exact asset.
    new = replace(card, printing_id="new-id", image_url=card.image_url.replace("100", "999").replace("old", "new"))
    restarted.path.write_text(json.dumps({"cards": [asdict(new)]}), encoding="utf-8")
    again = Catalog(tmp_path)
    assert again.image_path(again.cards[0]) == path
    assert again.download_image(new) == str(path)
    report = again.image_diagnostics()
    assert report["image_files"] == report["matched_files"] == 1
    assert report["missing_cards"] == 0
    # A different language/asset must never be guessed from name/number.
    other = replace(new, printing_id="english", language="en", image_url=new.image_url.replace("royce-fr", "royce-en"))
    assert not again.image_path(other).exists()


def test_index_cannot_point_outside_images(tmp_path):
    card = Card("test", "test", "V", "s", "Set", "1", image_url="https://example.com/a")
    catalog = Catalog(tmp_path)
    catalog.image_index[card.image_url] = "../../private.txt"
    assert catalog.image_path(card).parent == tmp_path / "images"
