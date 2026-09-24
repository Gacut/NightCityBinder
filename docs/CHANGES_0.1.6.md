# 0.1.6 — binder i menu

- Cały kafelek bindera otwiera szczegóły; usunięto przycisk Otwórz.
- Nazwa na górze, grafika, cena za sztukę wyśrodkowana pod grafiką,
  numer/ilość/wykończenie oraz pełna nazwa stanu. Cena aktualizuje się także
  po zakończeniu pobierania Cardmarket lub kursów NBP w tle.
- Near Mint, Lightly Played, Moderately Played, Heavily Played, Damaged.
  SQLite i CSV nadal używają NM/LP/MP/HP/DMG — stare bindery pozostają zgodne.
- Tytuł >NightCityBinder_ i przycisk hamburgera po prawej. Ikona rysowana
  liniami, niezależnie od dostępności glifu w czcionce. Menu zawiera
  Mój binder, Katalog i Ustawienia; zachowano historię nawigacji.
- Czerwony Usuń binder obok licznika wyłącznie dla importowanych binderów.
  Potwierdzenie usuwa wybraną lokalną kopię z SQLite, wraca do głównego bindera
  i czyści historię nawigacji. Źródłowy CSV usuwa się oddzielnie w Ustawieniach.

Sprawdzono Kivy przy szerokości 360 px: kafelki, ceny, menu, zapis pełnych nazw
stanów jako dotychczasowe kody, anulowanie i potwierdzenie usuwania, zachowanie
głównego bindera oraz PL/EN. Zrzuty: docs/previews/*-016.png.
50 testów pytest i Ruff. APK 0.1.6 wymaga kompilacji przez dotychczasowy skrypt
Ubuntu; lokalnie nie zbudowano nowego APK.
