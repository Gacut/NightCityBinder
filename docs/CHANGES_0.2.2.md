# 0.2.2 — kompaktowe kafelki i margines ustawień

- Ustawienia: dodatkowe 16 dp marginesu po prawej, między zawartością a paskiem
  przewijania/ramką. Wszystkie przyciski i pola mieszczą się w obszarze.
- Wspólny układ kafelka dla bindera i katalogu: nazwa u góry, obraz, metadane
  pod obrazem. Taki sam kolor, wyrównanie i rozmiar nazwy oraz numeru.
- Wysokość kafelka wynika z zawartości. Grafika zachowuje proporcje i ma
  maksymalnie 170 dp wysokości, odstępy zmniejszono do 2 dp.
- Status grafiki jest warstwą wewnątrz obszaru ilustracji, zamiast osobnego
  wiersza zajmującego miejsce również po pobraniu grafiki.
- Binder zachowuje cenę, ilość, wykończenie i pełny stan; katalog bez cen.
  Długie nazwy zawijają się i powiększają wysokość kafelka.

Sprawdzono Kivy 360/320 px, PL/EN, binder, katalog, szczegóły i ustawienia.
Podglądy: docs/previews/compact-*-022.png. Ruff poprawny.
APK nie zbudowano. scripts/build_android.sh w Ubuntu wygeneruje
dist/NightCityBinder-0.2.2-debug.apk.
