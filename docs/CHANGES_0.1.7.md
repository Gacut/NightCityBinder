# 0.1.7 — pływający przycisk skanera

Zastąpiono tekstowy przycisk skanowania kwadratem 56 dp z przezroczystym tłem,
żółtym obrysem i rysowaną ikoną skanera. Pływa przy prawej dolnej krawędzi
obszaru aplikacji, z uwzględnieniem istniejących odstępów systemowych i statusu.
Jest dostępny w głównym binderze i katalogu. W katalogu przycisk pobierania
ma zarezerwowaną przestrzeń obok skanera; w binderze ostatni rząd można
przewinąć ponad przycisk. Importowane bindery pozostają tylko do odczytu.

Sprawdzono lokalnie interfejs Kivy przy szerokości 360 px, przezroczystość,
kwadratowe wymiary, położenie i wywołanie skanera, wcześniejsze działania
bindera i menu. Ruff przechodzi. APK nie zbudowano w sesji agenta.
Dotychczasowy skrypt Ubuntu wygeneruje dist/NightCityBinder-0.1.7-debug.apk.
