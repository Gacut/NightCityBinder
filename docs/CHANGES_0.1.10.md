# 0.1.10 — pływający wybór bindera

Usunięto górną rozwijaną listę binderów. Wybór jest teraz dostępny z cyjanowego,
transparentnego kwadratu z ikoną otwartej książki nad żółtym skanerem.
Ikona rysowana liniami, stylistycznie zgodna ze skanerem, 56 dp.
Lista w oknie jest przewijalna i wyróżnia aktualny binder. Importowane bindery
mają krótki identyfikator, aby odróżnić powtarzające się nazwy.
U góry pozostaje tekstowa nazwa aktualnego bindera. Po wybraniu importowanego
bindera książka jest dostępna przy dolnej krawędzi (bez przycisku skanera).
Ostatni rząd kart można przewinąć ponad pływające przyciski.

Sprawdzono Kivy przy 360 px, przełączanie z własnego na importowany binder
i z powrotem, pozostałe funkcje listy, ceny i menu. Ruff poprawny.
APK nie zbudowano; skrypt Ubuntu wygeneruje NightCityBinder-0.1.10-debug.apk.
