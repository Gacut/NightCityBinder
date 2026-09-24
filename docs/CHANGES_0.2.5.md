# 0.2.5 — przygotowanie Google Play

Prywatność PL/EN, credits i licencje Python w ustawieniach. Kontakt przez profil GitHub autora. Dokumenty i grafiki sklepu w docs/play/.
Profil play buduje kandydata AAB 1.0.0 / 10000, API 36, CameraX 1.4.2
(do weryfikacji), z wyłączonym allowBackup. Zwykłe APK debug nadal API 35.
Numer wersji Androida jest odczytywany z zainstalowanego pakietu.
Skrypt budowy obsługuje NCB_BUILD_MODE=play i nie podpisuje automatycznie.
Dodano kontrolę ELF i zbieranie notices Pythona z faktycznego pakietu.

52 testy, Ruff, bash -n, test okien PL/EN i kontrola grafik poprawne.
Raport starego APK wskazuje niezgodne biblioteki ELF 16 KB. Nie zbudowano
nowego APK/AAB: WSL E_ACCESSDENIED. To przygotowanie, nie gotowe wydanie.
Warunki publikacji i brakujące dowody: docs/play/README.md.
