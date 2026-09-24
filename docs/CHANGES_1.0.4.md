# 1.0.4 — edycja kart i kopia własnego bindera

- Na karcie otwartej z własnego bindera można zapisać nową ilość, wykończenie i stan
  bez dodawania kolejnego egzemplarza. Jeśli docelowy wariant już istnieje, ilości
  sumują się w jednym wpisie. Operacja jest transakcyjna.
- Dodawanie z katalogu i skanera wymaga wybrania wykończenia. Przycisk „Dodaj”
  pozostaje nieaktywny przy „Nieustalone”.
- W oknie wyboru binderów można wyeksportować własny binder i przywrócić jego kopię
  CSV. Przywrócenie wymaga potwierdzenia i zastępuje zawartość własnego bindera.
  Import z Ustawień nadal otwiera osobny binder do odczytu.
- Nazwy na kafelkach mieszczą się w jednej linii; tytuł skaluje się do dostępnej
  szerokości. Panele informacji mają pełne tło, a przyciski książki i skanera
  czarne tło pod ikonami.
- Przy zwykłym przełączaniu widoków nie czyścimy cache obrazów ani nie wymuszamy
  ich dekodowania na nowo. Ręczne „Odśwież katalog” nadal ponownie wczytuje pliki
  z telefonu.

Weryfikacja: 65 testów pytest, Ruff oraz uruchomienie interfejsu Kivy na Windows.
Kompilację APK należy wykonać w Ubuntu/WSL; środowisko agenta nie ma dostępu do
dystrybucji WSL (`E_ACCESSDENIED`).
