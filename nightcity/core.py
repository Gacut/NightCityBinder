"""Pure Python domain code. No Kivy or Android imports."""

from __future__ import annotations

import csv
import io
import json
import re
import sqlite3
import unicodedata
import uuid
from dataclasses import asdict, dataclass
from decimal import Decimal, ROUND_HALF_UP
from difflib import SequenceMatcher
from pathlib import Path

CURRENCIES = ("EUR", "USD", "PLN")
FINISHES = ("unknown", "normal", "foil")
CONDITIONS = ("NM", "LP", "MP", "HP", "DMG")
CSV_FIELDS = (
    "schema_version",
    "binder_name",
    "printing_id",
    "card_id",
    "name",
    "set_code",
    "set_name",
    "number",
    "language",
    "rarity",
    "finish",
    "condition",
    "quantity",
)


@dataclass(frozen=True)
class Card:
    printing_id: str
    card_id: str
    name: str
    set_code: str
    set_name: str
    number: str
    language: str = "en"
    rarity: str = ""
    image_url: str = ""
    card_type: str = ""
    color: str = ""
    tags: tuple[str, ...] = ()
    cost: int | None = None
    ram: int | None = None

    @classmethod
    def from_dict(cls, value):
        fields = {k: value[k] for k in cls.__dataclass_fields__ if k in value}
        if "tags" in fields:
            fields["tags"] = tuple(fields["tags"] or ())
        return cls(**fields)


def normalized(value):
    value = unicodedata.normalize("NFKD", value.casefold())
    return " ".join(re.findall(r"[^\W_]+", value, re.UNICODE))


def card_matches_filters(card, selected):
    """Only match known card attributes; missing values never pass an active filter."""
    if selected.get("card_type") and normalized(card.card_type) != normalized(selected["card_type"]):
        return False
    if selected.get("color") and normalized(selected["color"]) not in {
        normalized(color) for color in card.color.split("/")
    }:
        return False
    if selected.get("tag") and normalized(selected["tag"]) not in {normalized(tag) for tag in card.tags}:
        return False
    for key in ("cost", "ram"):
        if selected.get(key) is not None and getattr(card, key) != selected[key]:
            return False
    return True


def collector_numbers(text):
    """Keep leading zeroes, beta prefixes and variant suffixes significant."""
    text = unicodedata.normalize("NFKC", text).casefold()
    return {
        re.sub(r"\s+", "", token)
        for token in re.findall(r"(?<!\w)(?:β\s*)?\d{3,4}(?:\s?[a-z](?!\w))?(?!\w)", text)
    }


def match_cards(text, cards, limit=30, number_text=""):
    """Rank candidates only; never infer a finish or auto-add an OCR result."""
    query = normalized(text)
    if not query and not number_text:
        return []
    cards = list(cards)
    # Prefer the lower-left OCR region; use whole-card numbers only as fallback.
    numbers = collector_numbers(number_text)
    exact = {c.printing_id for c in cards if c.number.casefold() in numbers}
    if not exact:
        numbers = collector_numbers(text)
        exact = {c.printing_id for c in cards if c.number.casefold() in numbers}
    identities = {c.card_id for c in cards if c.printing_id in exact}
    tokens = set(query.split())
    lines = [normalized(line) for line in text.splitlines() if line.strip()]
    ranked = []
    for card in cards:
        name = normalized(card.name)
        name_tokens = set(name.split())
        coverage = len(tokens & name_tokens) / max(1, len(name_tokens))
        similarity = max((SequenceMatcher(None, line, name).ratio() for line in lines), default=0)
        score = max(coverage * 0.8, similarity * 0.7)
        if name and name in query:
            score = 0.9
        if normalized(card.set_code) in tokens:
            score += 0.1
        if card.printing_id in exact:
            score = 3 + score
        elif card.card_id in identities:
            score = 2 + score
        if score >= 0.40:
            ranked.append((score, card))
    ranked.sort(key=lambda item: (-item[0], item[1].set_code, item[1].number, item[1].printing_id))
    return ranked[:limit]


class Store:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path))
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.executescript("""
          CREATE TABLE IF NOT EXISTS binders (
            id TEXT PRIMARY KEY, name TEXT NOT NULL, readonly INTEGER NOT NULL);
          CREATE TABLE IF NOT EXISTS entries (
            binder_id TEXT NOT NULL REFERENCES binders(id), printing_id TEXT NOT NULL,
            finish TEXT NOT NULL, condition TEXT NOT NULL, quantity INTEGER NOT NULL
              CHECK(quantity > 0 AND quantity <= 999999), card_json TEXT NOT NULL,
            PRIMARY KEY(binder_id, printing_id, finish, condition));
          CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
          INSERT OR IGNORE INTO binders VALUES ('mine', 'My binder', 0);
        """)
        self.db.commit()

    def close(self):
        self.db.close()

    def settings(self):
        values = {row[0]: row[1] for row in self.db.execute("SELECT * FROM settings")}
        return {"language": "pl", "currency": "PLN", **values}

    def setting(self, key, value):
        if key not in ("language", "currency", "download_until_netdeck", "download_until_cardmarket"):
            raise ValueError("setting")
        if key.startswith("download_until_"):
            timestamp = Decimal(value)
            if not timestamp.is_finite() or timestamp < 0:
                raise ValueError("setting")
        elif value not in (("pl", "en") if key == "language" else CURRENCIES):
            raise ValueError("setting")
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO settings VALUES (?,?)", (key, value))

    def binders(self):
        return [dict(r) for r in self.db.execute("SELECT * FROM binders ORDER BY readonly,name")]

    def entries(self, binder_id="mine"):
        rows = self.db.execute(
            "SELECT * FROM entries WHERE binder_id=? ORDER BY printing_id,finish,condition", (binder_id,)
        )
        return [{**dict(row), "card": Card.from_dict(json.loads(row["card_json"]))} for row in rows]

    def delete_binder(self, binder_id):
        """Delete an imported binder; keep the user's primary binder empty."""
        if not any(b["id"] == binder_id for b in self.binders()):
            raise ValueError("binder")
        with self.db:
            self.db.execute("DELETE FROM entries WHERE binder_id=?", (binder_id,))
            if binder_id != "mine":
                self.db.execute("DELETE FROM binders WHERE id=?", (binder_id,))

    def rename_binder(self, binder_id, name):
        name = name.strip()
        if not name or len(name) > 100 or any(ord(char) < 32 for char in name):
            raise ValueError("binder_name")
        with self.db:
            cursor = self.db.execute("UPDATE binders SET name=? WHERE id=? AND readonly=1", (name, binder_id))
            if cursor.rowcount != 1:
                raise ValueError("readonly_binder_required")

    def _writable(self, binder_id):
        row = self.db.execute("SELECT readonly FROM binders WHERE id=?", (binder_id,)).fetchone()
        if row is None or row[0]:
            raise ValueError("readonly")

    def add(self, card, quantity=1, finish="unknown", condition="NM", binder_id="mine"):
        self._writable(binder_id)
        if type(quantity) is not int or not 1 <= quantity <= 999999:
            raise ValueError("quantity")
        if finish not in FINISHES or condition not in CONDITIONS:
            raise ValueError("variant")
        with self.db:
            self.db.execute(
                """INSERT INTO entries VALUES (?,?,?,?,?,?)
              ON CONFLICT(binder_id,printing_id,finish,condition)
              DO UPDATE SET quantity=quantity+excluded.quantity,card_json=excluded.card_json""",
                (
                    binder_id,
                    card.printing_id,
                    finish,
                    condition,
                    quantity,
                    json.dumps(asdict(card), ensure_ascii=False),
                ),
            )

    def update_entry(self, card, old_finish, old_condition, quantity, finish, condition):
        """Edit one owned variant atomically; combine quantities on a variant collision."""
        self._writable("mine")
        if type(quantity) is not int or not 1 <= quantity <= 999999:
            raise ValueError("quantity")
        if old_finish not in FINISHES or old_condition not in CONDITIONS:
            raise ValueError("variant")
        if finish not in FINISHES[1:] or condition not in CONDITIONS:
            raise ValueError("variant")
        old_key = ("mine", card.printing_id, old_finish, old_condition)
        new_key = ("mine", card.printing_id, finish, condition)
        with self.db:
            old = self.db.execute(
                "SELECT quantity FROM entries WHERE binder_id=? AND printing_id=? AND finish=? AND condition=?",
                old_key,
            ).fetchone()
            if old is None:
                raise ValueError("missing_entry")
            if old_key == new_key:
                self.db.execute(
                    "UPDATE entries SET quantity=?,card_json=? WHERE binder_id=? AND printing_id=? AND finish=? AND condition=?",
                    (quantity, json.dumps(asdict(card), ensure_ascii=False), *old_key),
                )
                return
            target = self.db.execute(
                "SELECT quantity FROM entries WHERE binder_id=? AND printing_id=? AND finish=? AND condition=?",
                new_key,
            ).fetchone()
            if target and target[0] + quantity > 999999:
                raise ValueError("quantity")
            self.db.execute(
                "DELETE FROM entries WHERE binder_id=? AND printing_id=? AND finish=? AND condition=?", old_key
            )
            self.db.execute(
                """INSERT INTO entries VALUES (?,?,?,?,?,?)
                ON CONFLICT(binder_id,printing_id,finish,condition)
                DO UPDATE SET quantity=quantity+excluded.quantity,card_json=excluded.card_json""",
                (*new_key, quantity, json.dumps(asdict(card), ensure_ascii=False)),
            )

    def remove_one(self, card, finish, condition):
        with self.db:
            key = ("mine", card.printing_id, finish, condition)
            row = self.db.execute(
                "SELECT quantity FROM entries WHERE binder_id=? AND printing_id=? AND finish=? AND condition=?", key
            ).fetchone()
            if row and row[0] > 1:
                self.db.execute(
                    "UPDATE entries SET quantity=quantity-1 WHERE binder_id=? AND printing_id=? AND finish=? AND condition=?",
                    key,
                )
            elif row:
                self.db.execute(
                    "DELETE FROM entries WHERE binder_id=? AND printing_id=? AND finish=? AND condition=?", key
                )

    def remove_many(self, card, quantity, finish, condition, binder_id="mine"):
        self._writable(binder_id)
        if type(quantity) is not int or not 1 <= quantity <= 999999:
            raise ValueError("quantity")
        if finish not in FINISHES or condition not in CONDITIONS:
            raise ValueError("variant")
        key = (binder_id, card.printing_id, finish, condition)
        with self.db:
            cursor = self.db.execute(
                "UPDATE entries SET quantity=quantity-? WHERE binder_id=? AND printing_id=? "
                "AND finish=? AND condition=? AND quantity>?", (quantity, *key, quantity))
            if cursor.rowcount:
                return
            cursor = self.db.execute(
                "DELETE FROM entries WHERE binder_id=? AND printing_id=? AND finish=? AND condition=? AND quantity=?",
                (*key, quantity))
            if not cursor.rowcount:
                raise ValueError("insufficient_quantity")

    def export_csv(self, binder_id="mine"):
        binder = self.db.execute("SELECT name FROM binders WHERE id=?", (binder_id,)).fetchone()
        if not binder:
            raise ValueError("binder")
        out = io.StringIO(newline="")
        writer = csv.DictWriter(out, CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for entry in self.entries(binder_id):
            row = {
                **asdict(entry["card"]),
                "schema_version": "1",
                "binder_name": binder[0],
                "finish": entry["finish"],
                "condition": entry["condition"],
                "quantity": entry["quantity"],
            }
            # Spreadsheet formula injection protection. Reversible on our own imports.
            row = {
                k: "'" + v if isinstance(v, str) and v.startswith(("=", "+", "-", "@", "'", "\t", "\r")) else v
                for k, v in row.items()
            }
            writer.writerow(row)
        return "\ufeff" + out.getvalue()

    def _parse_csv(self, text, allow_empty=False):
        """Validate a complete backup before changing the database."""
        if len(text.encode("utf-8")) > 10_000_000:
            raise ValueError("file_size")
        reader = csv.DictReader(io.StringIO(text.lstrip("\ufeff"), newline=""))
        if not reader.fieldnames or not set(CSV_FIELDS).issubset(reader.fieldnames):
            raise ValueError("columns")
        entries = {}
        for index, row in enumerate(reader, start=2):
            if index > 20001 or None in row or any(v is None for v in row.values()):
                raise ValueError("rows")
            row = {k: v[1:] if v.startswith("'") else v for k, v in row.items()}
            if any(len(v) > 1000 or "\x00" in v for v in row.values()):
                raise ValueError("field")
            if row["schema_version"] != "1":
                raise ValueError("version")
            if not row["printing_id"] or not row["card_id"] or not row["name"]:
                raise ValueError("identity")
            if row["finish"] not in FINISHES or row["condition"] not in CONDITIONS:
                raise ValueError("variant")
            if not re.fullmatch(r"[0-9]{1,6}", row["quantity"]):
                raise ValueError("quantity")
            quantity = int(row["quantity"])
            if quantity < 1:
                raise ValueError("quantity")
            card = Card.from_dict(row)
            key = (card.printing_id, row["finish"], row["condition"])
            if key in entries:
                old_card, old_quantity = entries[key]
                if old_card != card:
                    raise ValueError("identity_conflict")
                quantity += old_quantity
            if quantity > 999999:
                raise ValueError("quantity")
            entries[key] = (card, quantity)
        if not entries and not allow_empty:
            raise ValueError("empty")
        return entries

    def import_csv(self, text, name="Imported binder"):
        """Validate all rows before a single atomic, isolated import."""
        entries = self._parse_csv(text)
        binder_id = str(uuid.uuid4())
        with self.db:
            self.db.execute("INSERT INTO binders VALUES (?,?,1)", (binder_id, name[:100]))
            for (printing, finish, condition), (card, quantity) in entries.items():
                self.db.execute(
                    "INSERT INTO entries VALUES (?,?,?,?,?,?)",
                    (binder_id, printing, finish, condition, quantity, json.dumps(asdict(card))),
                )
        return binder_id

    def restore_csv(self, text):
        """Replace the own binder with an exported CSV, including an empty backup."""
        entries = self._parse_csv(text, allow_empty=True)
        with self.db:
            self.db.execute("DELETE FROM entries WHERE binder_id='mine'")
            for (printing, finish, condition), (card, quantity) in entries.items():
                self.db.execute(
                    "INSERT INTO entries VALUES (?,?,?,?,?,?)",
                    ("mine", printing, finish, condition, quantity,
                     json.dumps(asdict(card), ensure_ascii=False)),
                )
        return len(entries)


def convert(amount, source, target, rates):
    """Rates are PLN per one unit. Round only the final displayed value."""
    if source not in CURRENCIES or target not in CURRENCIES:
        raise ValueError("currency")
    value = Decimal(str(amount))
    if not value.is_finite() or value < 0:
        raise ValueError("amount")
    if source != target:
        source_rate, target_rate = Decimal(str(rates[source])), Decimal(str(rates[target]))
        if not all(r.is_finite() and r > 0 for r in (source_rate, target_rate)):
            raise ValueError("rate")
        value = value * source_rate / target_rate
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
