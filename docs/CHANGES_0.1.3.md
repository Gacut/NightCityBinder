# Wersja 0.1.3

- Pusta stopka statusu/progresu jest odłączana od układu. Nie zajmuje 38 dp ani
  dodatkowych odstępów. Margines dolny to 8 dp plus zmierzony bezpieczny obszar
  Androida. Komunikaty znikają po 6 sekundach; aktywny postęp pozostaje widoczny.
- Skaner: FrameLayout, tekst WRAP_CONTENT na półprzezroczystej warstwie nad
  podglądem, wymiary kontrolek w dp. PreviewView COMPATIBLE umożliwia nakładki.
- Cyjanowa ramka 63:88 dopasowuje się do przestrzeni między instrukcją a przyciskiem.
  Otoczenie ramki jest przyciemnione. To wskazówka kadrowania, nie automatyczne
  wykrywanie krawędzi ani przycięcie zdjęcia OCR.
- Katalog: AsyncImage dekoduje także lokalne pliki w tle. Pierwsza partia to
  12 kafelków, kolejne po 12. Limit wysyłania tekstur: jedna na klatkę.
  Zachowano cache, wyniki skanowania, paginację i historię powrotu.

Weryfikacja: 35 testów pytest, Ruff, składnia Bash. Test działającego Kivy:
pusty dół 8 dp, dodawanie/ukrywanie stopki, insets, asynchroniczna grafika z cache,
12/24 kafelki i powrót z detalu. Obejrzano docs/previews/binder-013.png.
Czas zbudowania 12 kafelków w teście desktopowym: około 24 ms; to nie benchmark
telefonu ani czas wczytania wszystkich grafik. Test zawierał jedną realną grafikę.

Wymagana kompilacja APK i test Androida: ramka/tekst skanera (także większa czcionka),
mały odstęp nad gestami/przyciskami systemowymi, szybkość katalogu z pełnym cache.
Plik docelowy: dist/NightCityBinder-0.1.3-debug.apk.

Źródła:
https://kivy.org/doc/stable/api-kivy.uix.image.html
https://developer.android.com/reference/androidx/camera/view/PreviewView.ImplementationMode
