"""Cardmarket public daily dumps; conservative, one-to-one printing matches."""

from collections import defaultdict
from datetime import datetime
from decimal import Decimal, InvalidOperation
import re
import unicodedata

PRODUCTS_URL = "https://downloads.s3.cardmarket.com/productCatalog/productList/products_singles_23.json"
GUIDE_URL = "https://downloads.s3.cardmarket.com/productCatalog/priceGuide/price_guide_23.json"

# Verified against the Expansion select on Cardmarket Cyberpunk Singles (2026-09-24).
# Demo/Alpha sets deliberately excluded: their relationship to Netdeck is unverified.
EXPANSIONS = {
    "welcometonightcitybeta": 6714,
    "theheistbetastarterdeck": 6715,
    "embracingpowerbetastarterdeck": 6716,
    "boxtoppersbeta": 6717,
    "prereleasebeta": 6718,
    "PRM01": 6719,
}


def name_key(value):
    # Normalize separator punctuation, but preserve accents and actual words.
    return " ".join(re.findall(r"[^\W_]+", unicodedata.normalize("NFC", value).casefold()))


def dump_rows(data, key):
    if data.get("version") != 1 or not isinstance(data.get(key), list) or not data[key]:
        raise ValueError("cardmarket_schema")
    stamp = datetime.fromisoformat(data["createdAt"])
    if stamp.tzinfo is None:
        raise ValueError("cardmarket_date")
    return data[key], stamp


def positive_price(value):
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError("cardmarket_price")
    try:
        amount = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("cardmarket_price") from exc
    if not amount.is_finite() or amount < 0:
        raise ValueError("cardmarket_price")
    # Cardmarket uses zero for unavailable price metrics, especially foil trend.
    return str(amount) if amount > 0 else None


def make_feed(products_dump, guide_dump, cards):
    products, products_stamp = dump_rows(products_dump, "products")
    guide, guide_stamp = dump_rows(guide_dump, "priceGuides")
    by_name, by_printing = defaultdict(list), defaultdict(list)
    ids, guide_ids = set(), set()
    for p in products:
        if type(p["idProduct"]) is not int or p["idProduct"] <= 0 or p["idProduct"] in ids:
            raise ValueError("cardmarket_product_id")
        ids.add(p["idProduct"])
        if p["idCategory"] == 1661:
            by_name[(p["idExpansion"], name_key(p["name"]))].append(p)
    prices = {}
    for row in guide:
        pid = row["idProduct"]
        if type(pid) is not int or pid in guide_ids:
            raise ValueError("cardmarket_duplicate_price")
        guide_ids.add(pid)
        if row["idCategory"] == 1661 and pid in ids:
            prices[pid] = {key: positive_price(row.get(key))
                           for key in ("trend", "trend-foil", "avg1", "avg7", "avg30",
                                       "avg1-foil", "avg7-foil", "avg30-foil")}
    if not prices:
        raise ValueError("cardmarket_no_singles")
    for card in cards:
        if card.language.lower() == "en" and card.set_code in EXPANSIONS:
            by_printing[(EXPANSIONS[card.set_code], name_key(card.name))].append(card)
    quotes, matches, status = [], {}, {}
    for card in cards:
        if card.language.lower() != "en" or card.set_code not in EXPANSIONS:
            status[card.printing_id] = "unsupported"
            continue
        key = (EXPANSIONS[card.set_code], name_key(card.name))
        candidates = by_name[key]
        if not candidates:
            status[card.printing_id] = "missing"
            continue
        if len(candidates) != 1 or len(by_printing[key]) != 1:
            status[card.printing_id] = "ambiguous"
            continue
        pid = candidates[0]["idProduct"]
        matches[card.printing_id] = pid
        status[card.printing_id] = "matched"
        for finish, suffix in (("normal", ""), ("foil", "-foil")):
            metrics = prices.get(pid, {})
            amount = metrics.get("trend" + suffix)
            if amount is None:
                continue
            quotes.append(dict(printing_id=card.printing_id, finish=finish, amount=amount,
                               currency="EUR", source="Cardmarket", metric="Trend",
                               date=guide_stamp.date().isoformat(), product_id=pid,
                               averages={key: metrics.get(key + suffix) for key in ("avg1", "avg7", "avg30")}))
    return dict(schema_version=1, quotes=quotes, matches=matches, match_status=status,
                guide_date=guide_stamp.date().isoformat(), guide_created_at=guide_stamp.isoformat(),
                products_created_at=products_stamp.isoformat())
