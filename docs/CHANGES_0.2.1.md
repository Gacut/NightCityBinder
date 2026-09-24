# 0.2.1 — wycena katalogu i poprawki układu

- Szczegóły z katalogu i bindera nadal używają wspólnego render_detail/update_price.
  Dodano pobranie cen po wyborze wykończenia, jeśli danego printing_id nie ma
  jeszcze w cache dopasowań. Po odświeżeniu katalogu odświeżane są też powiązania
  cen, nawet gdy wcześniej pobrano już dzisiejszy snapshot. To obsługuje nowe
  wydania katalogu. Nie zgadujemy brakujących cen ani cen nieobsługiwanych wydań.
  Lista katalogu nadal bez cen. Błąd sieci nie kasuje cache, przycisk pozwala ponowić.
- Ramka obejmuje wyłącznie nazwę aplikacji, z 20 dp odstępu po lewej.
  Szerokość i font mierzone według rzeczywistego tekstu; menu pozostaje po prawej.
- Wartość bindera: kwota waluta w jednej linii, na wysokości nazwy bindera.
  Kwota nadal #3af700. Długa nazwa bindera skracana w widoku (bez zmiany zapisu).
  Ostrzeżenie o brakach pod wartością, licznik kart w osobnym wierszu po lewej.
- HudInput rysuje podkreślenie po zakończeniu układu przez Clock trigger,
  obliczając prawą krawędź bezpośrednio z x + width zamiast cache aliasu right.
  Pełna szerokość widoczna bez ustawiania focus; fokus nadal zmienia kolor na cyjan.

52 testy i Ruff poprawne. Test Kivy: pobranie ceny dla karty otwartej z katalogu,
przełączanie normal/foil, identyczna wycena w binderze, zachowanie licznika,
szerokość podkreślenia wyszukiwarki i licznika przed focusem.
Podglądy 360/320 px PL/EN: docs/previews/fix-*-021.png.
Nie zweryfikowano konkretnej karty użytkownika (screeny pokazują tylko pola);
źródłowy brak wyceny pozostaje możliwy i jest jawnie opisany w aplikacji.

Kompilacja: scripts/build_android.sh w Ubuntu. Wynik:
dist/NightCityBinder-0.2.1-debug.apk. Nowego APK nie zbudowano w sesji agenta.
