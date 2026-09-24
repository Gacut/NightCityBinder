import csv
import io
from dataclasses import replace
from decimal import Decimal

import pytest

from nightcity.core import Card, Store, convert, match_cards
from nightcity.i18n import TEXT


@pytest.fixture
def store(tmp_path):
    value = Store(tmp_path / "binder.db")
    yield value
    value.close()


@pytest.fixture
def card():
    return Card("printing-a", "card-a", "V — Streetkid", "retail", "Retail", "005a")


def test_persistence_and_distinct_variants(tmp_path, card):
    path = tmp_path / "binder.db"
    store = Store(path)
    store.add(card, 2, "normal")
    store.add(card, 3, "normal")
    store.add(card, 1, "foil")
    store.add(replace(card, printing_id="alternate", number="144"), 1, "normal")
    store.close()
    reopened = Store(path)
    assert sorted(row["quantity"] for row in reopened.entries()) == [1, 1, 5]
    reopened.close()


def test_bulk_remove_exact_variant_and_reject_excess(store, card):
    store.add(card, 5, "normal", "NM")
    store.add(card, 3, "foil", "NM")
    store.add(card, 2, "normal", "LP")
    store.remove_many(card, 3, "normal", "NM")
    assert sorted(r["quantity"] for r in store.entries()) == [2, 2, 3]
    with pytest.raises(ValueError, match="insufficient_quantity"):
        store.remove_many(card, 3, "normal", "NM")
    assert sorted(r["quantity"] for r in store.entries()) == [2, 2, 3]
    store.remove_many(card, 2, "normal", "NM")
    assert {(r["finish"], r["condition"]) for r in store.entries()} == {("foil", "NM"), ("normal", "LP")}
    for invalid in (0, -1, True, 1.5, 1000000):
        with pytest.raises(ValueError):
            store.remove_many(card, invalid, "foil", "NM")
    imported = store.import_csv(store.export_csv(), "Friend")
    with pytest.raises(ValueError, match="readonly"):
        store.remove_many(card, 1, "foil", "NM", binder_id=imported)
    assert sum(r["quantity"] for r in store.entries(imported)) == 5


def test_roundtrip_isolated_readonly_import(store, card):
    card = replace(card, name='Żółć, "Streetkid"\nSecond line')
    store.add(card, 4, "foil", "LP")
    new_id = store.import_csv(store.export_csv(), "Friend")
    assert store.entries(new_id)[0]["card"] == card
    assert store.entries(new_id)[0]["quantity"] == 4
    assert store.entries()[0]["quantity"] == 4
    with pytest.raises(ValueError, match="readonly"):
        store.add(card, 1, binder_id=new_id)


@pytest.mark.parametrize("name", ["=SUM(A1:A3)", "+CMD", "@formula", "'quoted", "-number", "\tformula"])
def test_spreadsheet_formula_protection_roundtrip(store, card, name):
    store.add(replace(card, name=name))
    text = store.export_csv()
    row = list(csv.DictReader(io.StringIO(text.lstrip("\ufeff"))))[0]
    assert row["name"].startswith("'")
    imported = store.import_csv(text)
    assert store.entries(imported)[0]["card"].name == name


def test_import_atomic_on_invalid_second_row(store, card):
    store.add(card, 1)
    text = store.export_csv()
    lines = text.splitlines(keepends=True)
    invalid = lines[1].rsplit(",", 1)[0] + ",-1\r\n"
    before = store.binders()
    with pytest.raises(ValueError):
        store.import_csv(text + invalid)
    assert store.binders() == before
    assert len(store.entries()) == 1


@pytest.mark.parametrize("quantity", [0, -1, 1.5, True, 1000000])
def test_bad_quantity(store, card, quantity):
    with pytest.raises(ValueError):
        store.add(card, quantity)


def test_duplicate_import_rows_sum(store, card):
    store.add(card, 2)
    text = store.export_csv()
    duplicate = text + text.splitlines(keepends=True)[1]
    imported = store.import_csv(duplicate)
    assert store.entries(imported)[0]["quantity"] == 4


def test_conflicting_identity_rejected(store, card):
    store.add(card)
    text = store.export_csv()
    row = text.splitlines(keepends=True)[1].replace("V — Streetkid", "Different card")
    with pytest.raises(ValueError, match="identity_conflict"):
        store.import_csv(text + row)


def test_remove_last_copy(store, card):
    store.add(card, 2)
    store.remove_one(card, "unknown", "NM")
    assert store.entries()[0]["quantity"] == 1
    store.remove_one(card, "unknown", "NM")
    assert store.entries() == []


def test_readding_owned_variant_increments_one_row(store, card):
    store.add(card, 2, "foil", "LP")
    store.add(card, 1, "foil", "LP")
    assert len(store.entries()) == 1
    assert store.entries()[0]["quantity"] == 3


def test_edit_owned_variant_changes_quantity_and_merges_target(store, card):
    store.add(card, 2, "normal", "NM")
    store.add(card, 3, "foil", "LP")
    store.update_entry(card, "normal", "NM", 4, "foil", "LP")
    assert [(r["finish"], r["condition"], r["quantity"]) for r in store.entries()] == [("foil", "LP", 7)]
    store.update_entry(card, "foil", "LP", 1, "foil", "LP")
    assert store.entries()[0]["quantity"] == 1
    with pytest.raises(ValueError):
        store.update_entry(card, "normal", "NM", 1, "foil", "LP")
    with pytest.raises(ValueError):
        store.update_entry(card, "foil", "LP", 1, "unknown", "NM")
    assert store.entries()[0]["quantity"] == 1


def test_restore_backup_replaces_mine_atomically_and_preserves_import(store, card):
    store.add(card, 2, "foil", "NM")
    backup = store.export_csv()
    imported = store.import_csv(backup)
    store.add(replace(card, printing_id="other"), 1, "normal", "LP")
    bad_backup = backup.replace(",2\r\n", ",-1\r\n", 1)
    assert bad_backup != backup
    with pytest.raises(ValueError):
        store.restore_csv(bad_backup)
    assert len(store.entries()) == 2
    assert store.restore_csv(backup) == 1
    assert store.entries()[0]["card"] == card
    assert store.entries()[0]["quantity"] == 2
    assert store.entries(imported)[0]["quantity"] == 2
    store.delete_binder("mine")
    assert store.restore_csv(store.export_csv()) == 0


def test_delete_imported_binder_keeps_mine_and_other_imports(store, card):
    store.add(card, 2)
    data = store.export_csv()
    first, second = store.import_csv(data), store.import_csv(data)
    store.delete_binder(first)
    assert first not in {b["id"] for b in store.binders()}
    assert store.entries(first) == []
    assert store.entries()[0]["quantity"] == 2
    assert store.entries(second)[0]["quantity"] == 2
    with pytest.raises(ValueError):
        store.delete_binder("missing")
    assert len(store.binders()) == 2


def test_clear_primary_binder_preserves_import_and_can_add_again(store, card):
    store.add(card)
    imported = store.import_csv(store.export_csv())
    store.delete_binder("mine")
    assert store.entries() == []
    assert store.entries(imported)[0]["quantity"] == 1
    store.add(card)
    assert store.entries()[0]["quantity"] == 1


def test_exchange_cross_rate_and_rounding():
    rates = {"EUR": 4.2, "USD": 3.8, "PLN": 1}
    assert convert("10", "EUR", "PLN", rates) == Decimal("42.00")
    assert convert("10", "USD", "EUR", rates) == Decimal("9.05")
    assert convert("1.005", "EUR", "EUR", {}) == Decimal("1.01")
    with pytest.raises(KeyError):
        convert(10, "EUR", "PLN", {})


@pytest.mark.parametrize("value", ["NaN", "Infinity", "-1"])
def test_invalid_price(value):
    with pytest.raises(ValueError):
        convert(value, "EUR", "EUR", {})


def test_ocr_ranks_number_but_keeps_ambiguous_printings(card):
    alternate = replace(card, printing_id="other", number="144")
    beta = replace(card, printing_id="beta", set_code="beta")
    ranked = match_cards("V\nStreetkid\n005a\nCost 5", [alternate, card, beta])
    assert ranked[0][1].number == "005a"
    assert {c.printing_id for score, c in ranked} >= {"printing-a", "beta"}
    assert match_cards("", [card]) == []
    assert match_cards("unrelated random object", [card]) == []


def test_language_key_parity():
    assert TEXT["pl"].keys() == TEXT["en"].keys()


def test_number_only_finds_exact_printing_then_other_variants(card):
    other_variant = replace(card, printing_id="alternate", number="144")
    unrelated = replace(card, printing_id="unrelated", card_id="another", name="Other", number="123")
    ranked = match_cards("005a", [other_variant, unrelated, card])
    assert [c.printing_id for _, c in ranked] == ["printing-a", "alternate"]


def test_bottom_left_number_beats_full_card_text_and_numbers(card):
    misleading = replace(card, printing_id="wrong", card_id="wrong", number="144", name="Other Card")
    alternate = replace(card, printing_id="variant", number="005b")
    ranked = match_cards("Other Card 144", [misleading, alternate, card], number_text="005 a")
    assert [c.printing_id for _, c in ranked][:2] == ["printing-a", "variant"]


def test_beta_prefix_and_suffix_are_significant(card):
    beta = replace(card, printing_id="beta", number="β005a")
    alternate = replace(card, printing_id="variant", number="005b")
    ranked = match_cards("β 005a", [alternate, card, beta])
    assert ranked[0][1] == beta
    assert match_cards("005b", [card, alternate])[0][1] == alternate


def test_cost_does_not_match_collector_number(card):
    assert match_cards("Cost 5 Power 5", [card]) == []
    assert match_cards("1005a", [card]) == []


def test_same_number_in_two_sets_remains_ambiguous(card):
    another = replace(card, printing_id="other-set", card_id="other-card", set_code="promo")
    ranked = match_cards("005a", [card, another])
    assert {c.printing_id for _, c in ranked} == {"printing-a", "other-set"}


def test_preferences_persist(store):
    store.setting("language", "en")
    store.setting("currency", "USD")
    assert store.settings() == {"language": "en", "currency": "USD"}
