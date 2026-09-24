# Zweryfikowane źródła i ograniczenia

Sprawdzenie: 23 września 2026.

## Karty i ilustracje

- Oficjalna baza: https://cyberpunktcg.com/cards
- Publiczny endpoint odczytu używany przez tę stronę:
  `https://api.netdeck.gg/api/cards/cyberpunk?limit=100&offset=0`
- Sprawdzono paginację: 151 logicznych kart, 686 wydań. Liczby mogą się zmieniać.
- Kluczem kolekcji jest `printings[].id`; język, numer, zestaw i ilustracja pochodzą
  z tego samego wydania. Sama nazwa nie wystarcza do przypisania ceny.
- Endpoint jest integracją strony, nie potwierdzonym stabilnym publicznym API z SLA.
  Zmiana formatu może wymagać aktualizacji aplikacji. Przy błędzie cache pozostaje.
- Obrazy mają podpisane adresy z datą wygaśnięcia. Pobieramy je na żądanie i
  przechowujemy lokalnie. Nie obchodzimy wygasłych podpisów; należy odświeżyć katalog.
- Przed publiczną dystrybucją należy ustalić warunki wykorzystania katalogu i grafik.
  Sam publiczny adres nie stanowi licencji na redystrybucję.

## Ograniczanie pobrań (1.0.7)

Pobieranie Netdeck i Cardmarket w Ustawieniach ma osobny, trwały limit jednej próby
na godzinę dla każdego źródła. Ponowne wejście do aplikacji go nie resetuje.
Odczyt zapisanych danych w Katalogu i na karcie nie łączy się ze źródłami.

Aplikacja przechowuje zweryfikowane odpowiedzi źródłowe w `source-cache` i wysyła
warunkowe żądanie GET (`If-None-Match` albo `If-Modified-Since`), jeśli serwer
przekazał ETag lub Last-Modified. Odpowiedź 304 używa lokalnej kopii bez pobrania
treści. Jeśli serwer nie udostępnia tych nagłówków, treść trzeba pobrać, aby
porównać ją z kopią; identyczne dane nie zastępują wtedy cen ani historii.
Netdeck sprawdzany jest stronami. Strony zawierające brakujące ilustracje są
pobierane ponownie, żeby uzyskać świeże podpisane adresy grafik; same grafiki
pobierane są tylko, jeśli nie ma pliku na urządzeniu. Zmiana samego podpisu URL
nie jest nową wersją karty.

Źródła nie udostępniają w tej integracji potwierdzonego API różnicowego.
Zmiana strony katalogu albo pliku Cardmarket wymaga pobrania tej całej strony
lub pliku. Kontrola wersji nadal wykonuje żądanie do serwera, a ograniczenie
lokalne nie zastępuje limitu po stronie dostawcy.

## Kursy walut

- Dokumentacja: https://api.nbp.pl/
- Endpoint: https://api.nbp.pl/api/exchangerates/tables/a/?format=json
- Kurs średni NBP, tabela A, PLN za jednostkę EUR/USD; data `effectiveDate`.
- Przeliczenie: kwota × kurs źródłowy PLN / kurs docelowy PLN.
- Zaokrąglenie dopiero wyniku końcowego do 2 miejsc, Decimal / HALF_UP.
- W weekendy i offline widoczna jest data ostatniego dostępnego kursu.
- To przeliczenie waluty, nie zmiana rynku referencyjnego ceny.

## Ceny — Cardmarket (0.1.5)

Oficjalne publiczne pliki (gra 23), bez klucza i konta:
- https://downloads.s3.cardmarket.com/productCatalog/productList/products_singles_23.json
- https://downloads.s3.cardmarket.com/productCatalog/priceGuide/price_guide_23.json
- https://www.cardmarket.com/en/Cyberpunk/Data/Price-Guide
- Codzienna publikacja: https://news.cardmarket.com/en/Magic/were-making-the-price-guide-and-product-catalogue-available-for-download

24.09.2026 zweryfikowano pliki przekazane przez użytkownika: 296 produktów,
317 rekordów cen (także produktów innych niż single). Aplikacja filtruje kategorię
1661. Cena to `trend` lub `trend-foil`, w EUR, z datą `createdAt` pliku cen.
Zero/null oznacza brak wyceny, bez zastępowania ceny foil ceną zwykłej karty.
Opcjonalne avg1/7/30 to osobne średnie Cardmarket, nie punkty historii Trend.
Cena jest referencją rynku; nie uwzględnia stanu konkretnego egzemplarza.

Identyfikatory ekspansji odczytano z pola Expansion na
https://www.cardmarket.com/en/Cyberpunk/Products/Singles :
6714 Welcome to Night City Beta, 6715 The Heist Beta, 6716 Embracing Power Beta,
6717 Box Toppers Beta, 6718 Pre-Release Beta, 6719 Set 1 Promos.
Demo/Alpha nie mają jeszcze zweryfikowanego odpowiednika Netdeck.

Plik produktów nie zawiera numerów kolekcjonerskich ani oznaczeń V.1/V.2/V.3.
Łączenie wymaga znanego zestawu, zgodnej angielskiej nazwy i dokładnie jednego
produktu oraz jednego wydania Netdeck dla tej pary. Akcenty są zachowane;
normalizowane są wielkość liter i separatory. Nie ma fuzzy match ani dopasowania
po samej nazwie. Retail, FR i niejednoznaczne warianty pozostają bez ceny.
Na dostarczonych danych: 166 dopasowanych wydań, 159 wycen, 65 niejednoznacznych,
453 nieobsługiwane, 2 bez odpowiednika. To stan konkretnego snapshotu, nie stała.

Przy starcie aplikacji z pobranym katalogiem sprawdzamy ceny raz dziennie po
udanym odświeżeniu (dzień UTC); dostępny jest też przycisk ręcznego odświeżania.
Nie ma pracy w tle po zamknięciu aplikacji. Awaria nie kasuje zapisanych danych.
Oba pliki są pobierane i walidowane przed atomowym zastąpieniem prices.json.
Starszy snapshot nie nadpisuje nowszego. Dane powyżej 3 dni mają oznaczenie w UI.

Historia: jedna obserwacja na datę źródła, do 366 na serię. Nie uzupełniamy
brakujących dni. Seria rozdziela printing_id, finish, produkt Cardmarket,
źródło, metrykę i walutę. Zmiana produktu zaczyna osobną serię.
Historia pozostaje dostępna, jeśli bieżący Trend zniknie dla nadal dopasowanego
produktu. Konwersja historii używa jednego bieżącego kursu NBP; zmiana procentowa
liczona jest w EUR, bez wpływu kursów walut.

Pliki użytkownika wykorzystano wyłącznie do lokalnej weryfikacji; nie są
dołączone do APK. Nie dołączono danych testowych ani kluczy API. Sieciowe pobranie
z APK wymaga sprawdzenia na telefonie: ta sesja ma ograniczony dostęp sieciowy.

## Prywatność

Binder i zdjęcie skanu pozostają na urządzeniu. CameraX zapisuje zdjęcie tymczasowo
w prywatnym cache, ML Kit wykonuje OCR lokalnie, a plik jest usuwany po rozpoznaniu.
Zewnętrzne połączenia obejmują pobranie katalogu, ilustracji oraz kursów NBP i publicznych plików Cardmarket.
Nie ma kont, analityki, reklam, wysyłania kolekcji ani zdjęć na serwer.
