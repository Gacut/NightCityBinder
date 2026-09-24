"""Populate a local cache from real providers, without bundling artwork."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from nightcity.services import Catalog, ExchangeRates  # noqa: E402

parser = argparse.ArgumentParser()
parser.add_argument("directory", type=Path)
args = parser.parse_args()
catalog = Catalog(args.directory)
print(f"Catalog: {catalog.refresh()} printings")
print(f"NBP rates: {ExchangeRates(args.directory).refresh()}")
