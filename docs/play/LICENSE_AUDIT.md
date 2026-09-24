# Licencje i pochodzenie

Pełne notices Pythona wyciągnięto z faktycznie zbudowanego APK 0.2.4, nie ze środowiska Windows: assets/legal/python-notices.txt (28 plików). Obejmuje m.in. Kivy, PyJNIus, certifi, charset-normalizer, requests i zależności. Nie wolno traktować tego jako kompletnego SBOM/licencji aplikacji.

Przed finalnym AAB:
1. Uruchomić scripts/collect_python_notices.py na finalnym artefakcie, porównać z obecnymi notices i przebudować, jeśli się zmieniły.
2. Wygenerować `./gradlew dependencies --configuration releaseRuntimeClasspath` w wygenerowanym projekcie. Zachować rozstrzygnięte wersje, POM i wymagane LICENSE/NOTICE z AndroidX, Kotlin, ML Kit, Google Play Services i zależności. Sprawdzić warunki modeli ML Kit.
3. Zebrać licencje dokładnych źródeł p4a: CPython i jego komponenty, SDL2/SDL_image/SDL_mixer/SDL_ttf i kodeki, FreeType, libffi, SQLite, OpenSSL, libpng/libjpeg/zlib oraz wszystko faktycznie zlinkowane. Skan samych nazw .so nie wykrywa statycznych zależności.
4. Roboto i Roboto Mono dostarczone z Kivy są opisane przez Kivy jako Apache-2.0. Dołączyć właściwe oznaczenia fontów i pełny tekst (Apache-2.0 znajduje się także w notices requests, ale nie zastępuje sprawdzenia notice fontów). DejaVu, jeśli pozostaje w pakiecie, wymaga własnych notices.
5. Zachować oryginalne copyright, NOTICE i wymagania udostępnienia źródeł dla komponentów, których licencja tego wymaga. Nie przepisywać zbiorczo wszystkiego jako MIT i nie dodawać licencji open-source do własnego kodu bez decyzji autora.
6. Udostępnić w aplikacji komplet po audycie, zamiast samej obecnej sekcji „Licencje bibliotek Python”.

Źródła: https://kivy.org/doc/stable/guide/licensing.html ; https://github.com/kivy/kivy ; https://developers.google.com/ml-kit/terms

Asset provenance: ikona i splash wygenerowane deterministycznie przez scripts/render_splash.py z kształtów Kivy i fontu Roboto Mono. Nie użyto generowanych bitmap AI ani kupionego packa ikon. Card art pozostaje odrębną kwestią praw do TCG, patrz RIGHTS.md.
