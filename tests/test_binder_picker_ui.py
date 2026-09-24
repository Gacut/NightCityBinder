"""Desktop smoke test for opening the binder picker without a Kivy crash."""

import importlib.util
import os
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.skipif(
    importlib.util.find_spec("kivy") is None or
    (sys.platform != "win32" and not os.environ.get("DISPLAY")),
    reason="Kivy with a desktop display is required",
)
def test_binder_picker_opens_with_screen_margins(tmp_path):
    project = Path(__file__).resolve().parents[1]
    environment = os.environ.copy()
    environment["KIVY_HOME"] = str(tmp_path / "kivy")
    environment["NCB_DATA_DIR"] = str(tmp_path / "data")
    environment["NCB_NO_NETWORK"] = "1"
    script = """
from kivy.metrics import dp
from nightcity.ui import NightCityBinderApp

app = NightCityBinderApp()
app.build()
popup = app.show_binder_picker()
assert abs(popup.y - dp(56)) < 1
assert abs(popup._window.height - popup.top - dp(20)) < 1
popup.dismiss(animation=False)
app.on_stop()
"""
    result = subprocess.run(
        [sys.executable, "-c", script], cwd=project, env=environment,
        capture_output=True, text=True, timeout=20, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
