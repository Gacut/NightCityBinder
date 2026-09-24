from nightcity.storage import format_bytes, storage_usage


def test_storage_counts_only_catalog_and_images(tmp_path):
    images = tmp_path / "images"
    images.mkdir()
    (images / "card.webp").write_bytes(b"x" * 2048)
    (images / "empty.webp").touch()
    (tmp_path / "catalog.json").write_bytes(b"{}")
    (tmp_path / "binder.sqlite3").write_bytes(b"x" * 5000)
    assert storage_usage(tmp_path) == (2048, 2, 2)
    (images / "card.webp").unlink()
    assert storage_usage(tmp_path) == (0, 1, 2)


def test_storage_before_first_download(tmp_path):
    assert storage_usage(tmp_path) == (0, 0, 0)
    assert format_bytes(0) == "0 B"
    assert format_bytes(1536) == "1.50 KiB"
    assert format_bytes(1024**2) == "1.00 MiB"
