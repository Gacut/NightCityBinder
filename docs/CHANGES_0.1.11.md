# 0.1.11 — nazwa i wartość bindera

- Cyjanowa ikona ołówka przy nazwie importowanego bindera otwiera edycję nazwy.
  Zapis lokalny, nazwa 1–100 znaków po usunięciu skrajnych spacji.
  Nie zmienia kart, identyfikatora ani źródłowego pliku CSV. Nowa nazwa pojawia
  się w liście binderów, podglądzie i kolejnych eksportach.
- Podpis Wartość bindera: i kwota mają kolor #3af700. Ostrzeżenie o brakujących
  cenach pozostaje czerwone.
- Tłumaczenia PL/EN. Główny binder zachowuje nazwę systemową.

Sprawdzono lokalnie Kivy (360 px), zmianę nazwy z zachowaniem kart i aktualizacją
eksportu, listę binderów, kolor kwoty i wygląd ikony. Ruff poprawny.
APK nie zbudowano. Dotychczasowy skrypt Ubuntu wygeneruje
dist/NightCityBinder-0.1.11-debug.apk.
