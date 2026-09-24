## >NightCityBinder_
<center><img width="1794" height="876" src="https://github.com/user-attachments/assets/38211865-3c62-460b-b6c5-b0621f3581d7" /></center>

NightCityBinder is an unofficial Android app for managing a Cyberpunk TCG card collection. It is written in Python with Kivy. No account is required; binders are stored locally on the device.

## Features

- Scan a card's collector number with the camera using on-device OCR, then confirm the matching printing.
- Browse a two-column card catalog with search and filters.
- Manage your own binder and imported binders; edit quantities, card conditions, and finishes.
- Export and import binders as backups or to view someone else's collection.
- View indicative Cardmarket prices, the total value of a binder, and prices in EUR, USD, or PLN.
- Use the interface in English or Polish.

The installation package **does not include the card catalog or card artwork**. Users can download them from Settings. Downloaded data and images are stored in the app's private storage. See [data sources and limitations](docs/DATA_SOURCES.md) (Polish).

## Release

GitHub release **1.0.0** corresponds to Android `versionName 1.0.18`, `versionCode 10018`, and package ID `com.nightcitybinder`. The APK can be installed outside Google Play. The AAB is intended for Play Console and cannot be installed directly on a phone. See the [release notes](RELEASE_NOTES_1.0.0.md) (Polish).

Export your binder before replacing an older test build. Earlier APKs used the package ID `org.nightcitybinder.nightcitybinder`, so Android treats the current app as a separate installation with separate local data.

## Run locally

Python 3.11 or 3.12 is required for a local desktop run. On Windows:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

Run the checks with:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
```

[build_android.sh](scripts/build_android.sh) builds the Android app in Ubuntu/WSL. With `NCB_BUILD_MODE=play`, it produces an AAB and an audit report for the package ID, API level, and native libraries. The [Play release checklist](docs/play/README.md) (Polish) covers signing and additional checks.

[build_github_apk.sh](scripts/build_github_apk.sh) builds and signs the GitHub APK using the author's private upload key. Google Play may sign its installation with a different Play App Signing key. When switching installation sources, export your binder before uninstalling the previous app.

## Data and privacy

Binders do not require an account and are not sent to a NightCityBinder server. The app contacts external catalog, price, and exchange-rate providers when downloading data. See the [privacy policy](docs/play/privacy-en.html) and [export format](docs/CSV.md) (Polish).

## Credits and licensing

This is an unofficial project. It is not affiliated with CD PROJEKT RED, WeirdCo, Netdeck, or Cardmarket. Trademarks, card artwork, and card content belong to their respective owners. The repository does not contain downloaded card artwork or provider databases. See the [asset and dependency audit](docs/play/LICENSE_AUDIT.md) (Polish) and [distribution rights notes](docs/play/RIGHTS.md) (Polish).

The author's original source code, documentation, and first-party app artwork are available under the [MIT License](LICENSE). This license does **not** cover third-party trademarks, card content or artwork, provider data, fonts, libraries, or their license notices; see [licensing scope](LICENSING.md). An open-source code license does not grant permission to use third-party intellectual property or imply endorsement by its owners.

Project author: [Gacut](https://github.com/Gacut). Development was assisted by [Codex](https://openai.com/pl-PL/codex/).
