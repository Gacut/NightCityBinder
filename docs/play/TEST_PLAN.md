# Test finalnego kandydata

- Czysta instalacja z AAB przez internal testing, zimny i ciepły start, brak logowania.
- PL/EN, duży rozmiar tekstu, mały ekran, paski gestów i 3 przycisków, Android 16 edge-to-edge i Wstecz.
- Aparat: zgoda, odmowa, odmowa trwała, odebranie zgody w tle, anulowanie, powrót z przeglądarki.
- OCR numeru, kilka wydań, rozmyta karta, puste zdjęcie; kasowanie JPG po skanowaniu.
- Ręczne dodanie, +/− kilka sztuk, anulowanie usuwania, brak ujemnych stanów, różne finish/condition.
- Wartość z ilością, brak ceny, foil bez dopasowania, EUR/USD/PLN, brak sieci/stare kursy.
- Pobieranie katalogu, anulowane/zerwane połączenie, pozostawienie poprzedniego poprawnego katalogu.
- CSV eksport/import, obcy binder, zmiana nazwy, kasowanie bindera i osobno pliku; lokalny i chmurowy selektor dokumentów.
- Prywatność i notices offline, linki autora, kontakt; etykiety wersji finalnej.
- Telefon lub emulator z `adb shell getconf PAGE_SIZE` równym 16384, rzeczywisty start, skaner i przewijanie. Audyt ELF to tylko część zgodności.
- bundletool validate, wygenerowane split APK, zipalign -c -P 16 -v 4, manifest i podpis. Sprawdzić brak pustych splitów z obcym ABI z bibliotek AAR.
- Kontrola ruchu SDK po czystej instalacji i po skanowaniu, aktualizacja Data safety.
- Pre-launch report, ANR/crash, offline, slow network, brak cache i duży binder.

Nie publikować wyników jako zaliczonych dopóki nie zostaną wykonane na finalnym podpisanym kandydacie.
