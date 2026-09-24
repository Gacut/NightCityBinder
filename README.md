# NightCityBinder

NightCityBinder to nieoficjalna aplikacja na Androida do prowadzenia kolekcji kart Cyberpunk TCG. Kod aplikacji powstał w Pythonie i Kivy. Działa bez konta; bindery są przechowywane lokalnie na urządzeniu.

## Funkcje

- Skanowanie numeru karty aparatem z lokalnym OCR i potwierdzeniem rozpoznanego wydania.
- Katalog kart w dwóch kolumnach z wyszukiwaniem i filtrami.
- Własny binder oraz importowane bindery; edycja liczby egzemplarzy, stanu i wykończenia.
- Eksport i import binderów jako kopii zapasowej lub do przeglądania cudzej kolekcji.
- Orientacyjne ceny Cardmarket, sumaryczna wartość bindera i waluty EUR, USD oraz PLN.
- Interfejs po polsku i angielsku.

Aplikacja **nie zawiera katalogu ani ilustracji kart w pakiecie instalacyjnym**. Użytkownik może pobrać dane z poziomu Ustawień. Pobrane dane i zdjęcia są następnie przechowywane w prywatnym katalogu aplikacji. Źródła i ograniczenia opisano w [DATA_SOURCES.md](docs/DATA_SOURCES.md).

## Wydanie

Wydanie GitHub **1.0.0** odpowiada Android `versionName 1.0.18`, `versionCode 10018`, identyfikator `com.nightcitybinder`. APK służy do instalacji poza Google Play; AAB jest przeznaczony dla Play Console i nie instaluje się go bezpośrednio na telefonie. [Opis wydania](RELEASE_NOTES_1.0.0.md) zawiera najważniejsze zmiany.

Przed zastąpieniem starszych testowych instalacji wyeksportuj swój binder. Wcześniejsze APK używały identyfikatora `org.nightcitybinder.nightcitybinder`, więc Android traktuje obecną aplikację jako osobną instalację z osobnym magazynem danych.

## Uruchomienie kodu lokalnie

Wymagany jest Python 3.11 lub 3.12. Na Windows:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

Testy:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
```

Skrypt [build_android.sh](scripts/build_android.sh) buduje aplikację w Ubuntu/WSL. Tryb `NCB_BUILD_MODE=play` tworzy AAB i raport audytu pakietu, API oraz bibliotek natywnych. [Instrukcje wydania](docs/play/README.md) opisują podpisywanie i pozostałe kontrole.

[build_github_apk.sh](scripts/build_github_apk.sh) buduje i podpisuje APK do wydania GitHub przy użyciu prywatnego klucza upload. Aplikacja instalowana z Google Play może być podpisana innym kluczem przez Play App Signing; przy zmianie źródła instalacji wyeksportuj binder przed odinstalowaniem poprzedniej aplikacji.

## Dane i prywatność

Bindery nie wymagają konta i nie są wysyłane na serwer NightCityBinder. Aplikacja łączy się z zewnętrznymi dostawcami katalogu, cen oraz kursów walut podczas pobierania danych. Zobacz [politykę prywatności](docs/play/privacy-pl.html) oraz [format eksportu](docs/CSV.md).

## Autorzy i prawa

Projekt jest nieoficjalny i nie jest powiązany z CD PROJEKT RED, WeirdCo, Netdeck ani Cardmarket. Znaki, ilustracje i treść kart należą do odpowiednich właścicieli. Repozytorium nie zawiera pobranych ilustracji kart ani baz dostawców. Pochodzenie własnych grafik aplikacji i informacje o bibliotekach opisano w [LICENSE_AUDIT.md](docs/play/LICENSE_AUDIT.md); kwestie praw do publicznej dystrybucji w [RIGHTS.md](docs/play/RIGHTS.md).

Kod źródłowy jest dostępny do wglądu; autor nie nadał mu jeszcze licencji na ponowne wykorzystanie.

Autor projektu: [Gacut](https://github.com/Gacut). Rozwój aplikacji był wspomagany przez [Codex](https://openai.com/pl-PL/codex/).
