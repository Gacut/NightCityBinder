from dataclasses import asdict

from nightcity.core import Card, card_matches_filters
from nightcity.services import parse_catalog_page


def test_netdeck_filters_survive_catalog_json_roundtrip():
    payload = {"items": [{
        "id": "card-a", "canonical_name": "V — Streetkid", "card_type": "Legend",
        "color": "Red", "tags": ["Merc", {"name": "Nomad"}], "cost": 5, "ram": "2",
        "printings": [{"id": "printing-a", "set": {"code": "s", "name": "Set"},
                       "collector_number": "005", "language": "en", "rarity": "Rare", "image_url": ""}],
    }]}
    card = parse_catalog_page(payload)[0]
    assert (card.card_type, card.color, card.tags, card.cost, card.ram) == (
        "Legend", "Red", ("Merc", "Nomad"), 5, 2)
    assert Card.from_dict(asdict(card)) == card
    assert Card.from_dict({"printing_id": "old", "card_id": "old", "name": "Old", "set_code": "s",
                           "set_name": "Set", "number": "001"}).cost is None


def test_printing_override_zero_and_missing_stats_not_guessed():
    payload = {"items": [{
        "id": "card-a", "name": "A", "card_type": "Program", "cost": 5, "ram": 2,
        "printings": [{"id": "p", "set": {"code": "s", "name": "Set"},
                       "stats": {"cost": 0, "ram": "4"}}],
    }]}
    card = parse_catalog_page(payload)[0]
    assert (card.cost, card.ram) == (0, 4)
    assert not card_matches_filters(Card.from_dict({"printing_id": "old", "card_id": "old", "name": "Old",
                                               "set_code": "s", "set_name": "Set", "number": "001"}), {"cost": 0})


def test_combined_filters_match_exact_card_attributes():
    card = Card("p", "c", "A", "s", "Set", "001", card_type="Gear", color="Blue",
                tags=("Cyberware", "Corpo"), cost=0, ram=3)
    assert card_matches_filters(card, {"card_type": "gear", "color": "blue", "tag": "Corpo", "cost": 0, "ram": 3})
    for selected in ({"card_type": "Unit"}, {"tag": "Netrunner"}, {"cost": 1}, {"ram": 2}):
        assert not card_matches_filters(card, selected)
