# 1.0.5 — stronicowanie bindera i zachowanie grafik katalogu

- Lista „Mój binder” pokazuje początkowo 12 wariantów. „Pokaż kolejne” dokłada
  po 12 bez przebudowy wcześniej widocznych kafelków. Wyszukiwanie zaczyna od
  pierwszej strony wyników; powrót ze szczegółów przywraca liczbę kart i pozycję
  przewijania.
- Widok katalogu pozostaje w pamięci po przejściu do innej zakładki. Powrót
  pokazuje te same widżety i tekstury obrazów, bez automatycznego ponownego
  dekodowania. „Pokaż kolejne” w katalogu również dokłada tylko nową porcję.
- Pobieranie brakującej grafiki może dokończyć się w tle po zmianie zakładki.
  Ręczne „Odśwież katalog” ponownie wczytuje lokalne pliki, a pobranie nowego
  katalogu unieważnia zachowany widok.

Weryfikacja: 65 testów pytest, Ruff, test interfejsu Kivy obejmujący obie listy
i zachowanie tego samego widżetu obrazu po nawigacji, test ręcznego odświeżenia
lokalnych grafik. APK wymaga kompilacji w Ubuntu/WSL.
