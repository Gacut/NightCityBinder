# Wersja 0.1.2 — zmiany i testy

## Zmiany

- Ustawienia: usunięcie importowanego bindera albo wyczyszczenie głównego bindera.
  Operacja wymaga potwierdzenia; nie usuwa wyeksportowanych plików.
- Ustawienia: wybór pliku CSV na telefonie i osobne potwierdzenie trwałego usunięcia
  z nazwą pliku. Android używa DocumentsContract i zgody z systemowego wyboru pliku.
  Odmowa dostawcy plików kończy się komunikatem; binder w aplikacji pozostaje.
- Pasek rzeczywistego postępu pobierania katalogu (rekordy pobrane / wszystkie).
  Pozostałe operacje mają animowany wskaźnik bez szacowanego procentu.
  Natywny skaner pokazuje wskaźnik podczas otwierania aparatu i OCR.
- Odczyt/zapis dokumentu i import CSV działają w tle. Import używa osobnego
  połączenia SQLite i zachowuje transakcyjną walidację.
- Dla posiadanego wydania formularz wybiera istniejące wykończenie i stan.
  Przy kilku zapisanych kombinacjach wybiera pierwszą; można ją zmienić w formularzu.
  Domyślna ilość 1 zwiększa istniejący wpis, jeśli wykończenie i stan są identyczne.
- Historia ekranów obsługuje przycisk Wstecz oraz przycisk powrotu w szczegółach.
  Powrót do katalogu odtwarza zapytanie, wyniki skanu, limit i pozycję przewijania.
  Na pierwszym ekranie bez historii Wstecz zachowuje systemową obsługę wyjścia.
- SafeArea mierzy nakładanie się systemowych pasków/cutout na obszar aplikacji.
  Odstępy aktualizują się co 0,5 s; nie dodają ponownie miejsca już wykluczonego
  przez system. Natywny skaner również obsługuje WindowInsetsCompat.

## Weryfikacja

35 testów pytest przeszło. Ruff i składnia Bash poprawne.
Test działającego Kivy na Windows: powrót do wyszukiwania, zwiększenie foil/LP
z 2 do 3 w jednym wpisie, zmiana odstępów, pasek postępu i jego wygaszenie po
błędzie, import CSV w tle i odczyt wyniku z głównego połączenia SQLite.
Obejrzano zrzut interfejsu settings-012.png (testowy pasek 50%).

Kod natywny Androida wymaga kompilacji oraz testu na urządzeniu. Nie sprawdzono
jeszcze rzeczywistego usuwania dokumentu ani odczytu insetów na Androidzie.
Nie usuwano plików użytkownika podczas implementacji.

## Test na telefonie

1. Zainstaluj APK 0.1.2 jako aktualizację.
2. Przetestuj układ z nawigacją trzema przyciskami i gestami, także w skanerze.
3. Katalog → szczegóły → Wstecz: poprzednie wyniki i pozycja przewijania.
4. Dodaj ponownie posiadane wydanie: ilość +1, jedna pozycja przy tym samym stanie.
5. Zaimportuj testowy binder, anuluj usuwanie, następnie usuń go z aplikacji.
6. Wyeksportuj testowy CSV. Wybierz go do usunięcia; sprawdź anulowanie i potwierdzenie.
7. Sprawdź paski przy pobieraniu katalogu, skanowaniu, odczycie/zapisie/importowaniu.

Źródła implementacji Android:
https://developer.android.com/develop/ui/views/layout/edge-to-edge
https://developer.android.com/reference/android/provider/DocumentsContract
