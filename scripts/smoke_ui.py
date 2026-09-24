"""Exercise the real Kivy UI with a disposable data directory. Writes screenshots.

Usage: NCB_DATA_DIR=/tmp/ncb-test python scripts/smoke_ui.py /tmp/screenshots
Prepopulate that directory using sync_data.py to exercise real catalog artwork.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["NCB_NO_NETWORK"] = "1"
os.environ["KIVY_NO_ARGS"] = "1"
if not os.environ.get("NCB_DATA_DIR"):
    raise SystemExit("Set NCB_DATA_DIR to a disposable test directory")

from kivy.clock import Clock  # noqa: E402
from nightcity.ui import NightCityBinderApp  # noqa: E402

destination = Path(sys.argv[1])
destination.mkdir(parents=True, exist_ok=True)
app = NightCityBinderApp()
failures = []


def guarded(fn):
    def run(dt):
        try:
            fn()
        except Exception as exc:
            failures.append(exc)
            app.stop()

    return run


def show_card():
    assert app.catalog.cards, "Populate disposable catalog with sync_data.py first"
    card = next(c for c in app.catalog.cards if c.number == "005a" and c.set_code == "welcometonightcityretail")
    app.show_detail(card)


def add_card():
    app.root.export_to_png(str(destination / "scan-confirm-pl.png"))
    app.quantity.text = "3"
    app.add()
    assert app.store.entries()[0]["quantity"] == 3


def imported():
    app.root.export_to_png(str(destination / "binder-pl.png"))
    app.import_text(app.store.export_csv(), None, "Binder znajomego")
    assert app.binder_id != "mine"


def settings():
    app.root.export_to_png(str(destination / "import-pl.png"))
    app.language = "en"
    app.store.setting("language", "en")
    app.navigate("settings")


def finish():
    app.root.export_to_png(str(destination / "settings-en.png"))
    print("UI SMOKE OK: add 3, persist, export/import isolation, PL/EN views")
    app.stop()


for delay, fn in [(1, show_card), (5, add_card), (6, imported), (7, settings), (8, finish)]:
    Clock.schedule_once(guarded(fn), delay)
app.run()
if failures:
    raise failures[0]
