# 0.1.8 — licznik dodawania i usuwania

- Usunięto podtytuł aplikacji i zmniejszono wysokość nagłówka.
- Informacja Masz X szt. tego wydania jest pod opisem zestawu/numeru karty.
  Liczy wszystkie stany i wykończenia tego wydania w głównym binderze.
- Usunięto etykietę Liczba egzemplarzy, dopisek Dodaj zwiększy ilość oraz
  osobny przycisk Usuń 1 szt.
- Licznik przyjmuje -999999…999999. Dodatnia liczba: żółte Dodaj;
  ujemna: czerwone Usuń. Zero, puste pole i sam minus nie wykonują operacji.
- Usunięcie wymaga potwierdzenia konkretnej liczby sztuk, stanu i wykończenia.
  Dotyczy wyłącznie wybranej kombinacji. Nadmiarowe żądanie nie zmienia danych.
  Usunięcie ostatnich sztuk usuwa wiersz, pozostałe warianty pozostają.
- Importowane bindery nadal tylko do odczytu. SQLite/CSV bez zmiany formatu.

51 testów pytest i Ruff poprawne. Test UI: przełączanie licznika, anulowanie,
potwierdzanie, usunięcie części/wszystkich sztuk, odrzucenie nadmiaru,
zachowanie dodawania i usunięcie etykiet. Sprawdzono okno potwierdzenia na 360 px.
Nowego APK nie zbudowano; scripts/build_android.sh w Ubuntu wygeneruje
dist/NightCityBinder-0.1.8-debug.apk.
