"""Network adapters and persistent caches. Call network methods off the UI thread."""

from __future__ import annotations

import hashlib
import json
import re
import ssl
import os
import tempfile
import threading
from dataclasses import asdict
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError

import certifi

from nightcity.core import Card, convert
from nightcity.cardmarket import PRODUCTS_URL, GUIDE_URL, make_feed

CATALOG_URL = "https://api.netdeck.gg/api/cards/cyberpunk"
FX_URL = "https://api.nbp.pl/api/exchangerates/tables/a/?format=json"


def fetch_bytes(url, limit=12_000_000):
    if urlparse(url).scheme != "https":
        raise ValueError("https_required")
    request = Request(
        url,
        headers={
            "User-Agent": "NightCityBinder/0.1 (local prototype)",
            "Accept": "application/json,image/*;q=0.9,*/*;q=0.5",
        },
    )
    with urlopen(request, timeout=25, context=ssl.create_default_context(cafile=certifi.where())) as response:
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError("response_size")
    return data


def fetch_json(url):
    return json.loads(fetch_bytes(url).decode("utf-8-sig"))


def fetch_conditional_json(url, etag="", modified=""):
    """Return (payload or None for 304, ETag, Last-Modified)."""
    if urlparse(url).scheme != "https":
        raise ValueError("https_required")
    headers = {"User-Agent": "NightCityBinder/1.0", "Accept": "application/json"}
    if etag:
        headers["If-None-Match"] = etag
    elif modified:
        headers["If-Modified-Since"] = modified
    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=25, context=ssl.create_default_context(cafile=certifi.where())) as response:
            raw = response.read(12_000_001)
            if len(raw) > 12_000_000:
                raise ValueError("response_size")
            return json.loads(raw.decode("utf-8-sig")), response.headers.get("ETag", ""), response.headers.get("Last-Modified", "")
    except HTTPError as error:
        if error.code == 304:
            return None, etag, modified
        raise


class SourceCache:
    """Keep source bodies for conditional requests; publish only after validation."""

    def __init__(self, directory):
        self.directory = Path(directory) / "source-cache"
        self.pending = {}

    def _saved(self, url):
        key = hashlib.sha256(url.encode("utf-8")).hexdigest()
        path = self.directory / (key + ".json")
        previous = read_json(path, {})
        if not isinstance(previous, dict) or previous.get("url") != url or "payload" not in previous:
            previous = {}
        return path, previous

    def get(self, url, force=False):
        path, previous = self._saved(url)
        payload, etag, modified = fetch_conditional_json(
            url, "" if force else previous.get("etag", ""),
            "" if force else previous.get("modified", ""),
        )
        if payload is None:
            if not previous:
                raise ValueError("source_cache_missing")
            return previous["payload"], False
        changed = payload != previous.get("payload")
        self.pending[path] = {"url": url, "etag": etag, "modified": modified, "payload": payload}
        return payload, changed

    def contains_printing(self, url, printing_ids):
        _, previous = self._saved(url)
        for item in previous.get("payload", {}).get("items", []):
            if any(str(printing.get("id")) in printing_ids for printing in item.get("printings", [])):
                return True
        return False

    def commit(self):
        for path, value in self.pending.items():
            write_json(path, value)
        self.pending.clear()


def read_json(path, fallback):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return fallback


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)


def _card_value(sources, *names):
    for source in sources:
        if isinstance(source, dict):
            for name in names:
                if name in source and source[name] is not None:
                    return source[name]
    return None


def _card_number(value):
    if type(value) is int and 0 <= value <= 99:
        return value
    if isinstance(value, str) and value.isascii() and value.isdecimal() and 0 <= int(value) <= 99:
        return int(value)
    return None


def _card_text(value):
    if isinstance(value, dict):
        value = value.get("name") or value.get("label") or ""
    if isinstance(value, (list, tuple)):
        value = "/".join(filter(None, (_card_text(part) for part in value)))
    return value.strip() if isinstance(value, str) else ""


def _card_tags(value):
    if isinstance(value, str):
        value = value.split(",")
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(dict.fromkeys(filter(None, (_card_text(tag) for tag in value))))


def parse_catalog_page(data):
    cards = []
    for item in data["items"]:
        for printing in item.get("printings", []):
            sources = [printing]
            sources += [printing.get(key) for key in ("game_data", "card_data", "metadata", "stats", "attributes")]
            sources.append(item)
            sources += [item.get(key) for key in ("game_data", "card_data", "metadata", "stats", "attributes")]
            cards.append(
                Card(
                    printing_id=str(printing["id"]),
                    card_id=str(item["id"]),
                    name=printing.get("localized_name") or item.get("canonical_name") or item["name"],
                    set_code=printing["set"]["code"],
                    set_name=printing["set"]["name"],
                    number=printing.get("collector_number") or "",
                    language=printing.get("language") or "en",
                    rarity=printing.get("rarity") or "",
                    image_url=printing.get("image_url") or "",
                    card_type=item.get("card_type") or "",
                    color=_card_text(_card_value(sources, "color", "colour", "card_color", "colors")),
                    tags=_card_tags(_card_value(sources, "tags", "traits", "card_tags", "subtypes", "keywords")),
                    cost=_card_number(_card_value(sources, "cost", "play_cost", "eddie_cost",
                                                  "eddies_cost", "eurodollar_cost")),
                    ram=_card_number(_card_value(sources, "ram", "ram_cost", "ram_requirement", "ram_value")),
                )
            )
    return cards


class Catalog:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.path = self.directory / "catalog.json"
        self.payload = read_json(self.path, {})
        self.cards = [Card.from_dict(c) for c in self.payload.get("cards", [])]
        self._image_lock = threading.RLock()
        self.image_index_path = self.directory / "image-index.json"
        index = read_json(self.image_index_path, {})
        self.image_index = index if isinstance(index, dict) else {}
        self._index_existing_images()
        self.last_refresh_changed = False

    def _direct_image_path(self, card):
        key = hashlib.sha256(card.printing_id.encode()).hexdigest()
        return self.directory / "images" / (key + ".webp")

    @staticmethod
    def _has_image(path):
        try:
            return path.is_file() and path.stat().st_size > 0
        except OSError:
            return False

    @staticmethod
    def _image_key(card):
        url = urlparse(card.image_url)
        if url.hostname == "dstcynss47vun.cloudfront.net":
            # CloudFront signing parameters expire; the asset path identifies the image.
            return url._replace(query="", fragment="").geturl()
        return card.image_url

    def _index_existing_images(self):
        """Remember exact URL-to-file associations, never match by card name."""
        with self._image_lock:
            changed = False
            for card in self.cards:
                path = self._direct_image_path(card)
                if card.image_url and self._has_image(path) and self.image_index.get(self._image_key(card)) != path.name:
                    self.image_index[self._image_key(card)] = path.name
                    changed = True
            if changed:
                write_json(self.image_index_path, self.image_index)

    def reload(self):
        self._index_existing_images()
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        cards = [Card.from_dict(card) for card in payload["cards"]]
        if not cards:
            raise ValueError("catalog_empty")
        self.payload, self.cards = payload, cards
        self._index_existing_images()
        return len(cards)

    def refresh(self, progress=None):
        self._index_existing_images()
        old_cards = [asdict(card) for card in self.cards]
        source_cache = SourceCache(self.directory)
        # Missing artwork needs new signed CloudFront URLs even when card data
        # itself has not changed. Otherwise a cached URL can expire.
        missing_ids = {card.printing_id for card in self.cards
                       if not self._has_image(self.image_path(card))}
        offset, cards, identities = 0, {}, set()
        for _ in range(30):
            url = CATALOG_URL + "?" + urlencode({"limit": 100, "offset": offset})
            data, _ = source_cache.get(url, force=source_cache.contains_printing(url, missing_ids))
            items = data.get("items", [])
            if not items:
                raise ValueError("catalog_incomplete")
            for item in items:
                if item["id"] in identities:
                    raise ValueError("catalog_pagination")
                identities.add(item["id"])
            cards.update({c.printing_id: c for c in parse_catalog_page(data)})
            offset += len(items)
            if progress:
                progress(offset, int(data["total"]))
            if offset >= int(data["total"]):
                break
        else:
            raise ValueError("catalog_limit")
        if not cards:
            raise ValueError("catalog_empty")
        new_cards = [asdict(card) for card in cards.values()]
        def stable(records):
            return [{**card, "image_url": self._image_key(Card.from_dict(card))} for card in records]

        self.last_refresh_changed = not self.path.exists() or stable(new_cards) != stable(old_cards)
        payload = {
            "updated": datetime.now(timezone.utc).isoformat(),
            "source": CATALOG_URL,
            "cards": new_cards,
        }
        if self.last_refresh_changed or missing_ids:
            write_json(self.path, payload)
        source_cache.commit()
        self.payload, self.cards = payload, list(cards.values())
        return len(self.cards)

    def image_path(self, card):
        direct = self._direct_image_path(card)
        if self._has_image(direct):
            return direct
        # Different printings can share the exact artwork URL. Persist this
        # association so a new catalog ID or app restart doesn't orphan it.
        with self._image_lock:
            name = self.image_index.get(self._image_key(card), "")
        if isinstance(name, str) and re.fullmatch(r"[0-9a-f]{64}\.webp", name):
            indexed = self.directory / "images" / name
            if self._has_image(indexed):
                return indexed
        return direct

    def download_catalog(self, catalog_progress=None, image_progress=None):
        """Fetch fresh signed URLs, then persist all missing artwork, not just visible tiles."""
        self.refresh(catalog_progress)
        total = len(self.cards)
        downloaded = cached = unavailable = consecutive_errors = 0
        failures = []
        if image_progress:
            image_progress(0, total)
        for current, card in enumerate(self.cards, 1):
            if self._has_image(self.image_path(card)):
                cached += 1
                consecutive_errors = 0
            elif not card.image_url:
                unavailable += 1
            else:
                try:
                    self.download_image(card)
                    downloaded += 1
                    consecutive_errors = 0
                except Exception as error:
                    failures.append({"printing_id": card.printing_id, "error": type(error).__name__})
                    consecutive_errors += 1
            if image_progress:
                image_progress(current, total)
            # Don't spend hours retrying every card if the connection/source is down.
            if consecutive_errors >= 5:
                break
        available = sum(self._has_image(self.image_path(card)) for card in self.cards)
        report = {"cards": total, "available": available, "missing": total - available,
                  "downloaded": downloaded, "cached": cached, "no_url": unavailable,
                  "failed": failures, "not_attempted": total - current,
                  "up_to_date": not self.last_refresh_changed and downloaded == 0,
                  "checked_at": datetime.now(timezone.utc).isoformat()}
        write_json(self.directory / "image-download-report.json", report)
        return report

    def image_diagnostics(self):
        images = self.directory / "images"
        files = [p for p in images.glob("*") if self._has_image(p)]
        matched = {self.image_path(c).name for c in self.cards if self._has_image(self.image_path(c))}
        missing = [c for c in self.cards if not self._has_image(self.image_path(c))]
        return {"data_directory": str(self.directory.resolve()), "catalog_file": str(self.path.resolve()),
                "image_directory": str(images.resolve()), "cards": len(self.cards),
                "image_files": len(files), "matched_files": len(matched),
                "unmatched_files": [p.name for p in files if p.name not in matched][:20],
                "missing_cards": len(missing), "missing_examples": [
                    {"name": c.name, "number": c.number, "printing_id": c.printing_id,
                     "expected_file": self._direct_image_path(c).name} for c in missing[:12]]}

    def download_image(self, card):
        path = self.image_path(card)
        if path.is_file() and path.stat().st_size > 0:
            return str(path)
        host = urlparse(card.image_url).hostname or ""
        if host != "dstcynss47vun.cloudfront.net":
            raise ValueError("image_source")
        data = fetch_bytes(card.image_url, limit=8_000_000)
        if not (data.startswith(b"RIFF") or data.startswith(b"\x89PNG") or data.startswith(b"\xff\xd8")):
            raise ValueError("image_format")
        path.parent.mkdir(parents=True, exist_ok=True)
        # Readers see either the previous complete image or the new complete image.
        # Unique temporary files also allow concurrent requests for the same card.
        fd, temporary = tempfile.mkstemp(prefix=path.stem + "-", suffix=".part", dir=path.parent)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
            os.replace(temporary, path)
            with self._image_lock:
                self.image_index[self._image_key(card)] = path.name
                write_json(self.image_index_path, self.image_index)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        return str(path)


class ExchangeRates:
    def __init__(self, directory):
        self.path = Path(directory) / "fx.json"
        self.data = read_json(self.path, {})

    def refresh(self):
        table = fetch_json(FX_URL)[0]
        rates = {r["code"]: r["mid"] for r in table["rates"] if r["code"] in ("EUR", "USD")}
        if len(rates) != 2 or any(not 0 < value < 100 for value in rates.values()):
            raise ValueError("rates")
        rates["PLN"] = 1
        data = {"date": table["effectiveDate"], "source": "NBP", "rates": rates}
        write_json(self.path, data)
        self.data = data
        return data["date"]

    def convert(self, amount, source, target):
        return convert(amount, source, target, self.data.get("rates", {}))


class Prices:
    """Daily Cardmarket observations and offline cache, keyed by exact printing."""

    def __init__(self, directory):
        self.path = Path(directory) / "prices.json"
        self.data = read_json(self.path, {"quotes": []})
        self.last_refresh_changed = False

    @staticmethod
    def _catalog_fingerprint(cards):
        relevant = sorted((card.printing_id, card.name, card.set_code, card.language) for card in cards)
        return hashlib.sha256(json.dumps(relevant, ensure_ascii=False).encode("utf-8")).hexdigest()

    def refresh(self, cards):
        if not cards:
            raise ValueError("catalog_empty")
        source_cache = SourceCache(self.path.parent)
        products, products_changed = source_cache.get(PRODUCTS_URL)
        guide, guide_changed = source_cache.get(GUIDE_URL)
        card_ids = {card.printing_id for card in cards}
        self.last_refresh_changed = (
            products_changed or guide_changed or not self.path.exists()
            or card_ids != set(self.data.get("match_status", {}))
            or self.data.get("catalog_fingerprint") != self._catalog_fingerprint(cards)
        )
        if self.last_refresh_changed:
            count = self.load_cardmarket(products, guide, cards)
        else:
            count = len({q["printing_id"] for q in self.data.get("quotes", [])})
        source_cache.commit()
        return count

    def load_cardmarket(self, products, guide, cards):
        data = make_feed(products, guide, cards)
        data["catalog_fingerprint"] = self._catalog_fingerprint(cards)
        old_stamp = self.data.get("guide_created_at")
        if old_stamp and datetime.fromisoformat(data["guide_created_at"]) < datetime.fromisoformat(old_stamp):
            raise ValueError("cardmarket_older_snapshot")
        data["checked_at"] = datetime.now(timezone.utc).isoformat()
        self.load_feed(json.dumps(data))
        return len({q["printing_id"] for q in data["quotes"]})

    def quote(self, printing_id, finish):
        if finish == "unknown":
            return None
        return next(
            (q for q in self.data.get("quotes", []) if q["printing_id"] == printing_id and q["finish"] == finish), None
        )

    def binder_value(self, rows, fx, currency):
        priced, missing = [], 0
        for row in rows:
            quote = self.quote(row["card"].printing_id, row["finish"])
            if quote is None:
                missing += row["quantity"]
            else:
                priced.append((quote, row["quantity"]))

        def total(target):
            # Use the same displayed unit price as each tile, multiplied by copies.
            return sum((fx.convert(q["amount"], q["currency"], target) * quantity
                        for q, quantity in priced), Decimal("0.00"))

        try:
            return dict(amount=total(currency), currency=currency, missing=missing, fx_missing=False)
        except (KeyError, ValueError):
            try:
                return dict(amount=total("EUR"), currency="EUR", missing=missing, fx_missing=True)
            except (KeyError, ValueError):
                return dict(amount=None, currency=currency, missing=missing, fx_missing=True)

    def history(self, printing_id, finish):
        """Only compare observations from the current source/metric/currency."""
        current = self.quote(printing_id, finish)
        if current is None:
            product_id = self.data.get("matches", {}).get(printing_id)
            if product_id is None:
                return []
            saved = [q for q in self.data.get("history", [])
                     if q["printing_id"] == printing_id and q["finish"] == finish
                     and q.get("product_id") == product_id and q["source"] == "Cardmarket"
                     and q["metric"] == "Trend" and q["currency"] == "EUR"]
            return sorted(saved, key=lambda q: q["date"])
        identity = self._series_key(current)
        return sorted((q for q in self.data.get("history", []) if self._series_key(q) == identity),
                      key=lambda q: q["date"])

    @staticmethod
    def _series_key(quote):
        return tuple(quote[k] for k in ("printing_id", "finish", "source", "metric", "currency")) + (quote.get("product_id"),)

    def reload(self):
        self.load_feed(self.path.read_text(encoding="utf-8"), persist=False)

    def load_feed(self, text, persist=True):
        data = json.loads(text)
        if data.get("schema_version") != 1 or not isinstance(data.get("quotes"), list):
            raise ValueError("price_schema")
        seen = set()
        for q in data["quotes"]:
            if not isinstance(q["printing_id"], str) or q["finish"] not in ("normal", "foil"):
                raise ValueError("price_variant")
            convert(q["amount"], q["currency"], q["currency"], {})
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", q["date"]) or not q["source"] or not q["metric"]:
                raise ValueError("price_provenance")
            date.fromisoformat(q["date"])
            identity = (q["printing_id"], q["finish"])
            if identity in seen:
                raise ValueError("price_duplicate")
            seen.add(identity)
        if not persist:
            self.data = data
            return
        # One observation per source date, never manufacture missing days.
        observations = {}
        for q in self.data.get("history", []) + self.data.get("quotes", []) + data["quotes"]:
            observations[(self._series_key(q), q["date"])] = dict(q)
        series = {}
        for (identity, _), q in observations.items():
            series.setdefault(identity, []).append(q)
        data["history"] = [q for values in series.values()
                           for q in sorted(values, key=lambda q: q["date"])[-366:]]
        # Prices and history change together; failed validation leaves the cache intact.
        write_json(self.path, data)
        self.data = data
