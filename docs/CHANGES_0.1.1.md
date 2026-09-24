# Zmiany w wersji 0.1.1

- Pytanie o dostęp do aparatu następuje po wybraniu skanowania, również gdy katalog
  jest jeszcze pusty. Odmowa daje komunikat PL/EN z przejściem do ustawień aplikacji.
- Eksport i import korzystają z systemowego wyboru dokumentów Androida (SAF).
  Użytkownik zatwierdza konkretny plik/miejsce zapisu; ogólne uprawnienie do pamięci
  nie jest wymagane. Ustawienia wyjaśniają zapis lokalny i eksport CSV.
- Katalog pokazuje dwie kolumny kafelków z grafiką, nazwą, numerem i językiem.
  Grafiki pobierają się w tle i są zachowywane w lokalnym cache.
- OCR przekazuje osobno tekst z dolnej lewej części zdjęcia. Karta musi wypełniać
  kadr i być ustawiona pionowo. Numer wraz z sufiksem i prefiksem beta ma
  pierwszeństwo; następne są inne wydania tej samej karty. Gdy numeru nie uda się
  dopasować, pozostaje wyszukiwanie po tekście całej karty.
- Ten sam numer w kilku zestawach pozostaje niejednoznaczny: użytkownik potwierdza
  wydanie, nic nie dodaje się automatycznie.

Sprawdzono: 32 testy pytest, Ruff, składnię Bash, działający interfejs Kivy na
Windows (siatka, pusty wynik, ponowne wyszukiwanie, otwarcie karty, dialog odmowy).
Test wyglądu był offline, z jedną zapisaną grafiką i danymi testowymi.

Wersja 0.1.1 wymaga kompilacji i sprawdzenia na telefonie. W szczególności:
1. Odmów dostępu do aparatu, sprawdź komunikat, zezwól w ustawieniach i ponów skan.
2. Przy pustym katalogu sprawdź, czy próba skanowania pyta o aparat.
3. Pobierz katalog i przewiń siatkę; sprawdź wczytywanie grafik i otwieranie kart.
4. Zeskanuj numer z sufiksem (np. 005a): dokładny numer przed innymi wydaniami.
5. Wyeksportuj CSV do wybranego folderu, anuluj drugi eksport, zaimportuj zapisany plik.

Plik po kompilacji: dist/NightCityBinder-0.1.1-debug.apk.
Poprzednie APK 0.1.0 nie zawiera tych zmian.
