# 1.0.3 — pełne pobieranie ilustracji

Raport urządzenia: 700 kart, 62 pliki, 62 dopasowane pliki, 638 brakujących
ilustracji. Nie wskazuje utraty powiązań z istniejącymi 62 zdjęciami.
Dotychczas pobranie katalogu zapisywało JSON, a grafiki były pobierane
stopniowo przy przeglądaniu widocznych kart.

Pobierz katalog Netdeck pobiera teraz świeży katalog, a następnie wszystkie
brakujące zdjęcia ze świeżych adresów. Zapisanych nie pobiera ponownie.
Postęp ma osobny etap zdjęć. Okno podsumowuje faktyczną dostępność zdjęć;
nie zgłasza pełnego sukcesu po częściowym pobraniu. Po 5 kolejnych błędach
przerywa serię, zachowując zapisane zdjęcia. Następna próba uzupełnia braki.
Obowiązuje dotychczasowy godzinny limit. Raport zapisuje się lokalnie w
image-download-report.json. Lokalne odświeżanie nadal nie używa sieci;
gdy brakuje plików, pokazuje liczby i kieruje do pobrania w Ustawieniach.

63 testy, Ruff i bash -n poprawne. Test odtwarza stan 700/62, pobiera tylko
638 brakujących plików (mock sieci), odtwarza usługi z dysku, sprawdza
częściowe błędy, ponowienie i zatrzymanie przy braku połączenia.
APK nie zbudowano. Po aktualizacji uruchomić raz Pobierz katalog Netdeck
i poczekać na zakończenie etapu zdjęć. Nie odinstalowywać starszej wersji.
