# 0.2.4 — splash, ikona i autor

- Splash: usunięte czerwone ozdobne ramki, subtelna siatka na całej grafice.
- Ikona: cyjanowa książka w żółtej ramce ze ściętym prawym górnym narożnikiem.
  Osobne warstwy adaptacyjne i ikona klasyczna, podłączone w buildozer.spec.
- Na końcu ustawień mały przycisk O autorze / About the author.
- Okno z linkami do GitHuba Gacut i Codex, informacją o AI-assisted development.
- Źródło grafik: scripts/render_splash.py.

Sprawdzone: render splash/ikony, podgląd okna autora, oba zdarzenia linków,
Ruff. Nie zbudowano APK; natywne otwieranie przeglądarki i ikona launchera
wymagają sprawdzenia na Androidzie. Kompilacja: scripts/build_android.sh.
Wynik: dist/NightCityBinder-0.2.4-debug.apk.
