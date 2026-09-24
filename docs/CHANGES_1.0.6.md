# 1.0.6 — wyszukiwanie i filtry kart

- „Mój binder” ma lejek obok lupki. „Katalog” ma taki sam zestaw przycisków;
  oba pola są domyślnie schowane i rozwijają się na żądanie.
- Filtry działają razem z wyszukiwaniem i stronicowaniem: rodzaj karty,
  kolor, tag, dokładny koszt E$ oraz RAM. „Wyczyść filtry” przywraca wszystkie
  wyniki. Nieznana wartość nie przechodzi aktywnego filtru liczbowego.
- Parser zachowuje nowe pola z pobieranego katalogu Netdeck w `catalog.json`.
  Stare katalogi i bindery nadal się otwierają; koszt i RAM wymagają ponownego
  pobrania katalogu, jeśli wcześniejszy plik nie miał tych pól. Cardmarket nadal
  służy do wyceny, nie do statystyk rozgrywki.
- Nagłówek nie ma już pełnego, ciemnego prostokąta między nazwą aplikacji a menu.
  Wypełnienie pozostaje pod ramką nazwy.

Weryfikacja: 68 testów pytest, Ruff, test interfejsu Kivy i podglądy obu paneli.
APK trzeba zbudować w Ubuntu/WSL i sprawdzić na telefonie, zwłaszcza czy aktualny
feed Netdeck zawiera pola kosztu, RAM, koloru i tagów.
