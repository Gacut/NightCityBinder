# Format wymiany v1

Kodowanie UTF-8 z BOM, separator przecinek, standardowe cytowanie CSV.
Jeden wiersz oznacza konkretne wydanie × wykończenie × stan i liczbę sztuk.

`schema_version,binder_name,printing_id,card_id,name,set_code,set_name,number,language,rarity,finish,condition,quantity`

- `printing_id`: identyfikator wydania Netdeck, nie tylko nazwa postaci.
- `card_id`: identyfikator logicznej karty.
- `number`: tekst, zachowuje zera wiodące, litery i prefiks beta.
- `finish`: `unknown`, `normal`, `foil`.
- `condition`: `NM`, `LP`, `MP`, `HP`, `DMG`.
- `language`: język nadruku, niezależny od języka aplikacji.
- `quantity`: liczba całkowita od 1 do 999999.

Import w Ustawieniach tworzy nowy binder do odczytu; powtórny import tworzy kolejny snapshot.
Opcja „Importuj mój binder (backup)” w wyborze binderów przywraca karty do własnego
bindera po potwierdzeniu i zastępuje jego dotychczasową zawartość. Przed tą operacją
warto wyeksportować aktualny binder. Przywrócenie jest transakcyjne: błędny plik
nie zmienia żadnej karty.
Zgodne duplikaty w jednym pliku sumują się. Sprzeczne metadane tego samego klucza
powodują odrzucenie całego importu. Nieznane wydania są zachowane; ilustracja pojawi
się, gdy lokalny katalog będzie zawierał odpowiedni identyfikator. Żadne URL-e
z importowanego pliku nie są pobierane. Plik nie przenosi cen ani ilustracji.

Eksport poprzedza komórki zaczynające się od `=`, `+`, `-`, `@`, apostrofu,
tabulatora lub CR apostrofem; importer cofa to zabezpieczenie. Import jest przeznaczony
do eksportów NightCityBinder v1, nie arbitralnych plików innych aplikacji.
Limit: 10 MB, 20000 wierszy, 1000 znaków na pole. Pusty binder można wyeksportować,
ale pusty plik z samym nagłówkiem nie tworzy nowego bindera do odczytu;
może natomiast posłużyć do przywrócenia pustego własnego bindera.
