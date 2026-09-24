# Testy wymagane przed pierwszym wydaniem APK

Poniższe testy nie zostały jeszcze wykonane na Androidzie.

- Udany build czystego projektu; ustalenie NDK i rewizji python-for-android.
- Pierwsze uruchomienie, zgoda i odmowa dostępu do aparatu, ponowna próba po odmowie.
- Podgląd tylnego aparatu, autofocus, pionowa orientacja i obrót EXIF zdjęcia.
- OCR zwykłej karty, foil z odblaskami, małej czcionki, beta, alternate art, wersji FR.
- Brak dopasowania, kilka wydań, anulowanie skanera, przycisk Wstecz, wznowienie aplikacji.
- Dodanie 1 i wielu egzemplarzy; skanowanie nie dodaje karty bez potwierdzenia.
- Zapis i ponowne otwarcie bindera po zamknięciu procesu Androida.
- Eksport przez Storage Access Framework do Downloads; otwarcie na drugim urządzeniu.
- Import CSV przez systemowy picker, anulowanie, nieprawidłowy plik i duży plik.
- Tryb samolotowy: zapisany katalog, binder, ilustracje z cache i ostatnie kursy.
- Odświeżenie katalogu po wygaśnięciu podpisanego adresu ilustracji.
- Języki PL/EN przy wąskim ekranie oraz zwiększonej czcionce systemowej.
- Fizyczny ARM64 Android 7+ oraz nowszy Android; zgodność bibliotek może wymusić
  podniesienie minSdk. Zweryfikować przed deklaracją wspieranych wersji.

Po podłączeniu cen: mapowanie konkretnego wydania i foil, brak danych, cena zero,
data wyceny, kurs konwersji, wycena w EUR/USD/PLN i awaria źródła.
