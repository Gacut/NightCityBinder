"""Run with python main.py. Android uses the same entry point."""

import os

os.environ.setdefault("KIVY_NO_ARGS", "1")
from nightcity.ui import NightCityBinderApp  # noqa: E402

if __name__ == "__main__":
    NightCityBinderApp().run()
