# 0.2.8 — odświeżanie lokalne i limity pobierania

Katalog: Odśwież katalog czyta catalog.json; przy braku lub błędzie pliku
wskazuje Ustawienia. Nie zleca pobierania brakujących ilustracji.
Szczegóły kart: Odśwież ceny Cardmarket czyta prices.json bez połączenia,
bez zmiany daty danych ani historii. Brak pliku kieruje do Ustawień.
Ustawienia: Pobierz katalog Netdeck i Pobierz / odśwież ceny Cardmarket
mają niezależne trwałe limity 3600 s, odliczanie MM:SS i blokadę przycisku.
Limit zaczyna się przy zaakceptowanej próbie, także jeśli później wystąpi błąd.
Ponowne uruchomienie nie zeruje limitu; jest to lokalny limit, nie ochrona serwera
przed świadomym obchodzeniem (zmiana zegara lub usunięcie danych aplikacji).
Usunięto automatyczne pobieranie cen przy starcie, otwieraniu kart i po sync katalogu.
NBP i zwykłe pobieranie ilustracji przy przeglądaniu pozostały bez zmian.
Szczegóły kart mają taki sam prawy margines 16 dp jak ustawienia.

57 testów, Ruff i podgląd interfejsu poprawne. Sprawdzono ponowne otwarcie
bazy z limitem, granicę 00:00, odświeżanie bez sieci i uszkodzone/brakujące pliki.
APK nie zbudowano w tej sesji. scripts/build_android.sh tworzy 0.2.8-debug.apk.
