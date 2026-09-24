# Data safety — robocza mapa deklaracji, nie formularz do automatycznego zatwierdzenia

Weryfikacja kodu: brak kont, reklam, zakupów, backendu kolekcji oraz własnej analityki. Kamera służy OCR; zdjęcie i wynik pozostają lokalne. Tymczasowy JPG jest usuwany w normalnym zakończeniu, ale nagłe zabicie procesu może zostawić cache.

| Dane / działanie | Zachowanie | Decyzja przed publikacją |
|---|---|---|
| Zdjęcia i tekst OCR | lokalne przetwarzanie ML Kit | nie deklarować wysyłki samych zdjęć, o ile pomiar finalnego SDK to potwierdza |
| Bindery i historia cen | SQLite/JSON lokalnie | nie wysyłane do autora; eksport inicjuje użytkownik |
| Identyfikator instalacji SDK | ML Kit może przesyłać do Google | kategoria Device or other IDs, cel diagnostyka/analityka; nie zaznaczać zbiorczo „nie zbiera danych” |
| Wydajność, błędy i użycie OCR | ML Kit telemetria | App info and performance oraz odpowiednie App activity, według finalnej wersji i formularza |
| IP i żądane zasoby | Netdeck / hosty grafik / Cardmarket / NBP | ustalić logowanie i cel dostawców; nie zakładać, że techniczny dostęp oznacza brak przetwarzania |
| CSV | dokument wskazany przez użytkownika, potencjalnie chmura | rozróżnić udostępnianie inicjowane przez użytkownika od zbierania przez autora |
| E-mail wsparcia | autor otrzymuje wiadomość wysłaną poza aplikacją | opisać w polityce; nie zaznaczać automatycznie zbierania e-maila przez aplikację |

Google deklaruje HTTPS i brak przekazywania opisanej telemetrii ML Kit osobom trzecim. Nie oznacza to braku zbierania przez SDK ani automatycznej odpowiedzi na pytanie o „sharing” w całej aplikacji. Dokumentacja Google dotyczy najnowszych SDK, a projekt ma text-recognition 16.0.1: potwierdzić z finalnym drzewem zależności i pomiarem ruchu. Nie znamy czasu przechowywania telemetrii SDK i nie obiecujemy jej usunięcia przez odinstalowanie aplikacji.

Aparat jest opcjonalny względem ręcznej obsługi. Nie zakładać jednak, że cała telemetria jest opcjonalna tylko dlatego, że użytkownik nie uruchomi skanera — inicjalizacja komponentów SDK może następować wcześniej. Ustalić na finalnym buildzie.

Konto użytkownika: brak — nie wdrażać fikcyjnego mechanizmu usuwania konta. Dane bindera usuwa się lokalnie; kopie CSV pozostają do osobnego usunięcia. Profil Play wyłącza Android allowBackup; zweryfikować manifest i transfer na urządzeniach OEM.

Źródła: https://developers.google.com/ml-kit/terms ; https://developers.google.com/ml-kit/android-data-disclosure ; https://support.google.com/googleplay/android-developer/answer/10787469
