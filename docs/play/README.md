# Przygotowanie wydania Google Play

Stan przygotowania do Google Play: 24.09.2026. Ta lista kontrolna nie stanowi potwierdzenia zatwierdzenia aplikacji przez Google Play ani uzyskania zgód właścicieli praw. Nie wysłano wiadomości z prośbą o zgodę.

## Gotowe w projekcie
- Prywatność PL/EN w aplikacji i pliki HTML do hostowania.
- Credits, 28 pełnych plików licencji/NOTICE wyciągniętych z faktycznego APK 0.2.4 (biblioteki Python, nie cały stos).
- Teksty sklepu PL/EN, lista testów i mapa Data safety.
- Profil `play`: pakiet `com.nightcitybinder`, AAB, API 36, versionName 1.0.18, versionCode 10018, backup wyłączony i CameraX 1.4.2. Skrypt ustawia filtr ARM64 i API 36 bezpośrednio w wygenerowanym projekcie Gradle i ponownie buduje AAB: wcześniejszy projekt Gradle zachowywał API 35 mimo profilu Play. Konfiguracja wymaga ponownej kompilacji i testów.
- Narzędzie do kontroli ELF 16 KB; raport starego APK w audit-0.2.4.json.

## Warunki przed publikacją
1. **Prawa do treści**: uzyskać pisemną zgodę/licencję obejmującą aplikację mobilną, grafiki TCG, cache oraz zrzuty promocyjne. Wytyczne CDPR wyłączają aplikacje mobilne oparte na ich grach. Credits i darmowość nie zastępują zgody. W RIGHTS.md jest szkic wiadomości; nie została wysłana.
2. Potwierdzić zasady Netdeck i Cardmarket dla publicznej aplikacji. API dostępne publicznie nie oznacza automatycznej licencji.
3. **16 KB i ABI**: pierwsze AAB zawierały biblioteki ARM32/x86 bez środowiska Python. Skrypt budowy dodaje `ndk.abiFilters` do projektu Gradle i buduje końcowy AAB. Kandydat 1.0.16 zawierał tylko ARM64 i przeszedł audyt ELF 16 KB, ale miał błędny identyfikator pakietu `org.nightcitybinder.nightcitybinder`. Nowy audyt sprawdza także identyfikator `com.nightcitybinder`. Pełny test wymaga również bundletool i urządzenia/emulatora 16 KB.
4. Zbudować AAB, potwierdzić w raporcie `target_sdk >= 36`, sprawdzić manifest: kamera/Internet i faktycznie scalone uprawnienia SDK, brak debugowania; minSdk 24. Zmierzyć zimny start, ANR i crash. API 36 zmienia zachowanie systemu — szczególnie sprawdzić dolny pasek, edge-to-edge i Wstecz.
5. Uzupełnić licencje Android/native z dokładnie rozwiązanego drzewa Gradle i źródeł p4a — patrz LICENSE_AUDIT.md. Nie deklarować pełnej zgodności na podstawie listy bibliotek Python.
6. Wystawić privacy-pl.html / privacy-en.html pod publicznym HTTPS, bez logowania i blokad geograficznych. Wprowadzić prawdziwy URL w Play Console. Nie podano fikcyjnego adresu. W aplikacji kontakt z autorem prowadzi przez GitHub. Dane zweryfikowanego wydawcy w Console mogą wymagać imienia/nazwiska, adresu i deklaracji statusu przedsiębiorcy; właściciel konta uzupełnia je sam.
7. Zatwierdzić formularze Data safety, IARC, grupę docelową (treść kart może zawierać przemoc/język dla dorosłych), reklamy: nie, zakupy: nie. Nie oznaczać aplikacji jako gry hazardowej tylko z powodu cen kolekcjonerskich; odpowiedzieć zgodnie z faktyczną zawartością.
8. Zrobić minimum 2 prawdziwe screenshoty telefonu z finalnej wersji i legalnie użytymi grafikami; nie używać makiet jako dowodu działania. Grafiki sklepu opisano w STORE_LISTING.md.
9. Podpisać AAB kluczem upload, włączyć Play App Signing, wykonać test wewnętrzny i pre-launch report. Dla osobistych kont utworzonych po 13.11.2023 obowiązuje test zamknięty min. 12 testerów przez kolejne 14 dni, potem wniosek o produkcję. Nie jest to automatyczna gwarancja akceptacji.

## Budowa kandydata w Ubuntu

```bash
NCB_BUILD_MODE=play bash /mnt/c/Users/Gacut/Documents/Codex/2026-09-23/he/outputs/NightCityBinder/scripts/build_android.sh
```

W PowerShell użyj: `wsl -d Ubuntu-24.04 -- env NCB_BUILD_MODE=play bash /mnt/c/Users/Gacut/Documents/Codex/2026-09-23/he/outputs/NightCityBinder/scripts/build_android.sh`.

Skrypt tworzy `dist/NightCityBinder-1.0.18-unsigned.aab`, raport pakietu/API/ELF/ABI i hash. Budowa może się udać, ale zakończyć kodem 1 po wykryciu złego identyfikatora, API poniżej 36, niezgodnej biblioteki lub obcej architektury — nie traktować tego jako gotowego wydania. Nie zastępuje to walidacji Google. Zwykły tryb buduje testowe `NightCityBinder-1.0.18.apk`. Sesja agenta nie ma dostępu do WSL (`E_ACCESSDENIED`), więc AAB musi zostać zbudowany w Twoim terminalu Ubuntu.

## Podpisywanie lokalnie, poza logiem budowy

Nie wysyłaj haseł ani klucza do czatu. Przykład w Ubuntu (katalog prywatny, kopia bezpieczeństwa klucza poza repo):

```bash
mkdir -p ~/.android-keys
chmod 700 ~/.android-keys
keytool -genkeypair -keystore ~/.android-keys/nightcitybinder-upload.jks -alias upload -keyalg RSA -keysize 3072 -validity 10000
keytool -list -v -alias upload -keystore ~/.android-keys/nightcitybinder-upload.jks
bash /mnt/c/Users/Gacut/Documents/Codex/2026-09-23/he/outputs/NightCityBinder/scripts/sign_play_bundle.sh
```

`keytool -genkeypair` wykonaj tylko przy pierwszym tworzeniu klucza; `keytool -list -v` jedynie pokazuje jego publiczny certyfikat i odciski SHA-1/SHA-256, nie podpisuje AAB. Komenda dla `androiddebugkey`/`debug.keystore` dotyczy wersji testowej i nie zastępuje klucza upload. Polecenia podpisania uruchom w Ubuntu; skrypt podpisujący znajdzie projekt niezależnie od bieżącego katalogu, sprawdzi zgodność pakietu z pozytywnym audytem `com.nightcitybinder`/API 36/ARM64/16 KB i zapisze `dist/NightCityBinder-1.0.18-play.aab`. Użyj tego samego klucza upload co przy pierwszym podpisaniu; nie twórz kolejnego. Hasła wpisuj wyłącznie do interaktywnych promptów. Wykonaj bezpieczną kopię klucza. Zmiana identyfikatora z `org.nightcitybinder.nightcitybinder` tworzy na telefonie osobną aplikację z osobnym magazynem danych: wyeksportuj bindery ze starej przed jej usunięciem i zaimportuj je do nowej. Przy każdym następnym uploadzie zwiększ versionCode, nawet dla poprawki testowej.

## Źródła wymagań
- https://support.google.com/googleplay/android-developer/answer/11926878?hl=en
- https://developer.android.com/guide/practices/page-sizes
- https://support.google.com/googleplay/android-developer/answer/14151465?hl=en
- https://support.google.com/googleplay/android-developer/answer/10144311?hl=en
- https://support.google.com/googleplay/android-developer/answer/9866151?hl=en
- https://developers.google.com/ml-kit/android-data-disclosure

Sprawdzać ponownie przed wysłaniem: terminy, wyjątki i wymagania konta mogą się zmieniać.
