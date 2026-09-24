# Wersja 0.1.4 — debug pamięci

Pod numerem wersji w Ustawieniach wyświetlane są:
- suma logicznych rozmiarów plików w images oraz liczba plików;
- rozmiar catalog.json (0 B przed pobraniem).

Pomiar działa w tle przy otwarciu Ustawień, jednostki B/KiB/MiB/GiB.
Nie uwzględnia SQLite ani narzutu systemu plików. Aby odświeżyć wartości po
pobraniu kolejnych grafik, wejdź ponownie w Ustawienia.

Przycisk Pokaż folder ze zdjęciami: Windows otwiera Eksplorator; Android otwiera
wewnętrzną przeglądarkę rzeczywistego prywatnego folderu images z pełną ścieżką,
listą plików i podglądem wybranej grafiki. Nie przenosi ani nie kopiuje danych.
Nie dodaje publicznego DocumentsProvider ani dostępu do bazy binderów.

Weryfikacja: 37 testów pytest, Ruff i składnia Bash poprawne. Smoke test Kivy
sprawdził pomiar, listę plików i podgląd grafiki. Obejrzano storage-014.png.
APK 0.1.4 wymaga kompilacji i testu na telefonie.
