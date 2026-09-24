# 0.2.3 — ekran startowy

- Własny natywny presplash zamiast domyślnej grafiki Kivy: ciemne tło,
  czerwone ramki, cyjanowy binder i nazwa w kolorze #f4f444.
- assets/presplash.png: 1080 × 1920; środkowy układ i jednolite krawędzie
  pasują do skalowania FIT_CENTER na różnych proporcjach telefonu.
- buildozer.spec wskazuje PNG oraz tło #09070c. Nie dodano opóźnień startu.
- Edytowalne źródło: scripts/render_splash.py (wymaga tylko Kivy).
  Renderowanie jest potrzebne wyłącznie przy zmianie grafiki, nie przy budowie APK.

Sprawdzone: render PNG, kontrola wizualna, Ruff, ścieżka presplash w konfiguracji.
Nie zbudowano APK w tej sesji. Natywny start wymaga sprawdzenia na Androidzie.
Ekran systemowy Androida poprzedzający uruchomienie Activity pozostaje bez zmian.

Kompilacja w Ubuntu:

```bash
bash /mnt/c/Users/Gacut/Documents/Codex/2026-09-23/he/outputs/NightCityBinder/scripts/build_android.sh
```

Wynik: dist/NightCityBinder-0.2.3-debug.apk.
