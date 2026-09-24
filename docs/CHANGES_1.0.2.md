# 1.0.2 — trwały indeks ilustracji i diagnostyka

Brak potwierdzonej przyczyny na telefonie użytkownika. Kod używa stałego
katalogu files/images i SHA-256 identyfikatora wydania, nie losowego hash().
Odtworzenie Catalog z pliku zachowuje ścieżki w testach. Przykłady zgłoszone:
Royce — Psychoverdose #143 FR i Dexter DeShawn — Off the Grid #012 EN.

Dodano trwały image-index.json mapujący dokładny zasób graficzny na zapisany
plik. Istniejące pliki są indeksowane po starcie i odświeżeniu, a nowe po zapisie.
Dla CloudFront tożsamość bazuje na ścieżce zasobu, pomija wygasającą sygnaturę
w query. Nie dopasowuje ilustracji po nazwie ani numerze karty. Pozwala
zachować obraz przy zmianie ID katalogu, jeśli ścieżka ilustracji jest ta sama.
Nie usuwa zdjęć i nie pobiera ich automatycznie w lokalnym odświeżaniu.

Ustawienia -> Diagnostyka zdjęć pokazuje katalogi, liczbę plików i dopasowań,
niepowiązane pliki oraz przykłady brakujących powiązań z oczekiwaną nazwą pliku.
Komunikat kafelka zmieniony na „Nie znaleziono pliku dla tej karty”, żeby nie
sugerował braku wszystkich zdjęć na telefonie. Raport pozostaje lokalny.

60 testów i Ruff poprawne. Sprawdzono ponowne utworzenie usług z dysku,
zmienioną sygnaturę URL, zmianę ID oraz brak pomylenia wariantów językowych.
Nie potwierdzono rozwiązania zgłoszenia na urządzeniu; potrzebny raport,
jeśli te same karty nadal są puste. APK nie zbudowano w tej sesji.
