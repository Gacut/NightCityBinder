# 0.2.0 — motyw interfejsu inspirowany Cyberpunk 2077

Referencje obejrzane w przeglądarce:
https://www.gameuidatabase.com/gameData.php?id=439
(Inventory: Browse, ekrany 43 i 44).

## Wygląd

- Niemal czarne, bordowe tło, dyskretna poświata u góry i pionowe oznaczenia.
- Czerwone ramki i ścięte narożniki paneli, przycisków i okien dialogowych.
- Cyjanowe nazwy kart, selektory i aktywna pozycja menu.
- Czcionka Roboto Mono w tytule aplikacji, nazwie bindera, sumie i menu.
  Teksty opisowe pozostają w czytelnej czcionce proporcjonalnej z polskimi znakami.
- Jednolity wygląd bindera, katalogu, szczegółów, ustawień, historii cen,
  wyboru bindera, edycji nazwy, potwierdzeń i pól tekstowych.
- Cyjanowy pasek postępu i paski przewijania, widoczne obramowanie aktywnego pola.
- Żółty skaner, cyjanowa książka/ołówek i wartość #3af700 zachowane.
- Natywny skaner: ciemne panele z czerwonym obrysem, tekst monospace,
  cyjanowa ramka karty i postęp, zgodny przycisk rozpoznawania.

Motyw zaimplementowany wektorowo w nightcity/theme.py. Bez pobranych assetów
gry, shaderów, migotania i ciągłych animacji dekoracyjnych. Geometria skaluje
się przez dp; użyto fontu dostarczanego z Kivy. Kolory i wspólne komponenty
mają jedno miejsce definicji. Nie zmieniono modelu danych, CSV ani wyceny.

## Walidacja

- 52 testy pytest oraz Ruff przechodzą.
- Kivy: binder, importowany binder, menu, szczegóły, formularz, selektory,
  ustawienia (góra/dół), katalog i postęp, ekrany 360×800 i 320×720, PL/EN.
- Sprawdzono zmianę nazwy i eksport, przełączanie binderów, zachowanie danych,
  czerwone usuwanie wielu sztuk, anulowanie i potwierdzenie operacji.
- Podglądy aplikacji: docs/previews/theme-*-012.png.
- Zachowano istniejącą obsługę insetów Androida. Nie przeprowadzono testu
  natywnego aparatu na urządzeniu ani kompilacji Java/APK w tej sesji.

## Kompilacja

Uruchom dotychczasowy scripts/build_android.sh w Ubuntu.
Wynik: dist/NightCityBinder-0.2.0-debug.apk.
WSL z sesji agenta był niedostępny (E_ACCESSDENIED); nowe APK nie powstało tutaj.
Po instalacji sprawdź szczególnie aparat, listy rozwijane, klawiaturę podczas
zmiany nazwy i położenie pływających przycisków przy pasku nawigacyjnym Androida.
