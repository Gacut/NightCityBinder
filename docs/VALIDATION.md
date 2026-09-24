# Weryfikacja lokalnego prototypu

Środowisko: Windows, Python 3.12.14, Kivy 2.3.1, renderowanie OpenGL/NVIDIA.

- 27 testów pytest: zaliczone.
- Ruff: bez błędów.
- Rzeczywiste pobranie i paginacja katalogu: 686 wydań kart.
- Rzeczywiste pobranie kursów NBP: tabela z 2026-09-22.
- Uruchomiony interfejs Kivy: wybór rzeczywistej karty, pobranie ilustracji,
  dodanie 3 egzemplarzy, CSV, import do osobnego bindera i przełączenie PL/EN.
- Sprawdzono zrzuty interfejsu po renderowaniu.

Nie wykonano kompilacji APK, testów Java/CameraX/Pyjnius na urządzeniu ani pobrania
rzeczywistych cen rynkowych. Testy logiki i desktopu nie potwierdzają działania
aparatu na Androidzie. Lista testów urządzenia: [ANDROID_TESTS.md](ANDROID_TESTS.md).
