# 0.1.5 — ceny i historia Cardmarket

- Pobranie publicznego katalogu produktów i zestawienia cen Cyberpunk (gra 23).
- Przycisk w Ustawieniach i pod ceną karty; odświeżanie w wątku z postępem.
- Automatyczna próba przy starcie, jeśli tego dnia UTC nie pobrano jeszcze cen.
  Wymaga pobranego katalogu. Brak monitorowania po zamknięciu aplikacji.
- Trend EUR osobno normal/foil, kursy EUR/USD/PLN, źródło i data publikacji.
- Historia obserwacji oraz zmiana procentowa w EUR. Średnie 1/7/30 dni
  pokazywane osobno, gdy Cardmarket je udostępnia. Nie odtwarzamy minionych dni.
- Atomowy cache i historia prices.json; do 366 dat na serię. Odświeżenie tej samej
  daty nie powiela punktów. Awaria/niepoprawny lub starszy snapshot zachowuje cache.
- Jawne powody braku ceny: wykończenie nieznane, wariant niejednoznaczny,
  nieobsługiwany zestaw/język, brak produktu lub brak wartości Trend.
- Odświeżanie zachowuje wybrany finish, stan i liczbę sztuk w formularzu.
- Tłumaczenia PL/EN. Brak nowych uprawnień, kont i kluczy API.

## Pokrycie źródła

Na plikach przekazanych przez użytkownika (price guide 22.09.2026):
296 produktów, 317 rekordów cen, katalog Netdeck 686 wydań.
166 jednoznacznych dopasowań, 159 cen Trend, 65 wariantów niejednoznacznych,
453 nieobsługiwane wydania/języki, 2 bez odpowiednika. Brak dodatnich cen
Trend foil dla dopasowanych wydań w tym snapshotcie.

Potwierdzone zestawy: Welcome to Night City Beta, The Heist Beta,
Embracing Power Beta, Box Toppers Beta, Pre-Release Beta i Set 1 Promos.
Retail/FR, Demo/Alpha oraz warianty o identycznej nazwie nie są zgadywane.
Szczegóły źródeł i reguł: DATA_SOURCES.md.

## Sprawdzenie

50 testów pytest oraz Ruff. Testy obejmują ceny, separację wydań/finish,
niejednoznaczność po obu stronach, duplikaty, rollback przy awarii, daty,
historię po ponownym uruchomieniu, zmianę produktu i zniknięcie ceny.
Test interfejsu Kivy na Windows: PL/EN, rzeczywiste dane, NBP z testowej
fixture, fallback EUR, brak foil, historia i zachowanie formularza.
Dane testowe oraz dostarczone pliki źródłowe nie są dołączane do APK.

## Do sprawdzenia na Androidzie

Zbuduj przez scripts/build_android.sh. Oczekiwany wynik:
dist/NightCityBinder-0.1.5-debug.apk. Sesja agenta nadal otrzymuje
WSL E_ACCESSDENIED; nie powstało tutaj nowe APK.

1. Zainstaluj aktualizację, pobierz katalog i ceny w Ustawieniach.
2. Otwórz Mantis Blades z Welcome to Night City Beta, wybierz Zwykła:
   sprawdź Trend, datę i walutę. Foil może nie mieć ceny.
3. Zmień walutę, ponownie otwórz kartę i historię.
4. Wyłącz sieć: zapisane ceny i historia powinny pozostać dostępne.
5. Po kolejnej publikacji Cardmarket odśwież ceny: historia zyska kolejną
   datę. Kilka odświeżeń jednego zestawienia daje jeden punkt.
6. Sprawdź angielski UI, niejednoznaczny wariant V oraz wydanie Retail:
   powinny być pokazane odpowiednie wyjaśnienia zamiast zgadywanej ceny.
