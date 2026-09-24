"""Read-only debug storage measurements (logical file sizes, not disk allocation)."""

from pathlib import Path


def storage_usage(directory):
    directory = Path(directory)
    images_size, images_count = 0, 0
    images = directory / "images"
    if images.exists():
        for path in images.rglob("*"):
            if path.is_file() and not path.is_symlink():
                try:
                    images_size += path.stat().st_size
                    images_count += 1
                except FileNotFoundError:
                    pass  # A cache file may disappear while measuring.
    catalog = directory / "catalog.json"
    try:
        catalog_size = catalog.stat().st_size
    except FileNotFoundError:
        catalog_size = 0
    return images_size, images_count, catalog_size


def format_bytes(size):
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if size < 1024 or unit == "TiB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.2f} {unit}"
        size /= 1024
