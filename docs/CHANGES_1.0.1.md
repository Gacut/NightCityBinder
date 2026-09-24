# 1.0.1 — ponowne wczytywanie ilustracji

Odśwież katalog czyści pamięć loadera, obrazów i tekstur Kivy, po czym
ponownie odczytuje obrazy z dysku. Kafelki nie utrwalają starej tekstury,
a ładowanie istniejącego pliku usuwa ewentualny wpis oczekujący loadera.
Puste pliki nie są traktowane jako pobrane obrazy. Brak ilustracji lokalnie
jest opisany wprost; odświeżanie nie pobiera katalogu ani cen ani brakujących
ilustracji z internetu. Zwykłe przeglądanie katalogu nadal pobiera brakujące zdjęcia.
JSON Netdeck zawiera adresy grafik, nie same grafiki; ceny Cardmarket nie
zawierają ilustracji. Obrazy są oddzielnymi plikami w images/.
Nowe ilustracje zapisywane są przez unikalny plik tymczasowy i atomową zamianę,
żeby loader nie odczytywał pliku w trakcie zapisu.

58 testów, Ruff i test Kivy: zablokowany wpis loadera -> odświeżenie offline
-> poprawna tekstura 1024x1024. Nie potwierdzono jeszcze na telefonie.
APK nie zbudowano w tej sesji. Wynik skryptu: NightCityBinder-1.0.1-debug.apk.
