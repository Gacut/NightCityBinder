# 0.1.9 — wartość bindera

- Suma cen po prawej od licznika wariantów i sztuk. Dotyczy całego wybranego
  bindera, niezależnie od filtra wyszukiwania.
- Każda cena jednostkowa widoczna na kafelku mnożona jest przez ilość w wierszu;
  obliczenia Decimal. Uwzględnione osobne wykończenia. Cena pozostaje referencją
  Cardmarket bez korekty za stan, zgodnie z wyceną szczegółów karty.
- Czerwony komunikat pod sumą podaje liczbę sztuk bez ceny (nie wariantów).
  Bez brakujących cen komunikat znika. Pusty binder: 0.00 w wybranej walucie.
- Odświeżenie cen lub FX aktualizuje sumę i kafelki. Przy braku kursu sumowanie
  przechodzi na EUR z komunikatem; waluty nigdy nie są dodawane bez konwersji.
- Usunięty napis Zapis lokalny · bez konta. W importowanym binderze przycisk
  usuwania znajduje się w wierszu poniżej sumy, przy informacji o odczycie.

52 testy pytest oraz Ruff poprawne. Smoke test Kivy 360 px: suma i brakujące
sztuki w głównym/importowanym binderze oraz dotychczasowe funkcje.
APK nie zbudowano w sesji agenta. Uruchom scripts/build_android.sh w Ubuntu;
wynik: dist/NightCityBinder-0.1.9-debug.apk.
