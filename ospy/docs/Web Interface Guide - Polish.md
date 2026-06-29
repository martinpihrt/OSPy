Przewodnik po interfejsie WWW OSPy po polsku
====

    Instalacja OSPy
    Logowanie
    Strona glowna
    Programy
    Jednorazowe uruchomienie
    Rozszerzenia
    Dziennik
    Ustawienia
    Stacje
    Czujniki
    Pomoc
    Wylogowanie

----

# Instalacja OSPy
Zalecana jest czysta instalacja z aktualna wersja Python 3. Przy pierwszym uruchomieniu OSPy tworzy dane logowania. Po zalogowaniu nalezy zmienic haslo i w razie potrzeby nazwe uzytkownika w ustawieniach.

## Skrypt instalacyjny
Zaloguj sie do Raspberry Pi przez SSH i uruchom:

```bash
wget https://raw.githubusercontent.com/martinpihrt/OSPy/master/ospy_setup.sh
sudo bash ospy_setup.sh
```

Po zakonczeniu instalacji Raspberry Pi zostanie uruchomione ponownie, a OSPy bedzie gotowe do konfiguracji przez przegladarke.

----

# Logowanie
Strona logowania zawiera pola nazwy uzytkownika i hasla. Domyslny uzytkownik to `admin`. Przy nowej instalacji generowane jest losowe haslo, ktore nalezy pozniej zmienic.

----

# Strona glowna
Strona glowna jest centrum sterowania. Pokazuje zegar, pasek nawigacji, globalne przelaczniki, os czasu, wykresy, informacje systemowe i elementy dodawane przez rozszerzenia.

## Normalny poziom wody
Ustawia globalny procentowy poziom wody, ktory zmienia czas pracy programow.

## Aktywne opoznienie deszczowe
Wstrzymuje podlewanie dla stacji, ktore nie ignoruja deszczu.

## Harmonogram - Recznie
Przelacza system miedzy trybem automatycznym i recznym sterowaniem stacjami.

## Wlaczony - Wylaczony
Steruje ogolnym dzialaniem OSPy.

## Zatrzymaj wszystkie stacje
Natychmiast zatrzymuje uruchomiony program lub stacje.

## Wykres bilansu wody
Pokazuje ilosc wody dostarczona przez programy lub stacje.

## Deszcz i opoznienie deszczowe
Aktywny czujnik deszczu albo opoznienie deszczowe blokuje odpowiednie stacje.

## Informacje systemowe
Stopka pokazuje temperature CPU, uzycie CPU, wersje oprogramowania, zewnetrzny adres IP i czas pracy.

----

# Programy
Strona Programy sluzy do tworzenia, organizowania i uruchamiania harmonogramow podlewania.

## Dodaj nowy program
Tworzy nowy program harmonogramu.

## Grupy programow
Programy mozna porzadkowac w zwijanych grupach, na przyklad programy letnie i zimowe.

## Dodaj grupe
Tworzy nowa grupe programow.

## Zmien nazwe grupy
Zmienia tylko nazwe grupy, bez zmiany programow w srodku.

## Wlacz lub wylacz grupe
Wlacza albo wylacza wszystkie programy w grupie jednoczesnie.

## Kopiuj grupe
Tworzy kopie grupy i jej programow. Skopiowane programy sa domyslnie wylaczone.

## Usun grupe
Usuniecie wymaga potwierdzenia. Programy z usunietej grupy wracaja do grupy domyslnej.

## Uruchom teraz
Natychmiast uruchamia program niezaleznie od harmonogramu.

## Edytuj
Otwiera parametry istniejacego programu.

## Kopiuj
Tworzy wylaczona kopie programu do bezpiecznej edycji.

## Przenies do grupy
Przypisuje program do wybranej grupy.

## Usun wszystko
Po potwierdzeniu usuwa wszystkie programy.

## Wlacz lub wylacz program
Przelacznik ON/OFF wlacza albo wylacza pojedynczy program.

## Ostrzezenia o konfliktach
Podczas zapisu OSPy sprawdza wlaczone programy pod katem nakladania sie czasu na tej samej stacji lub wyjsciu. Ostrzezenie nie blokuje programu automatycznie.

## Typ harmonogramu
Dostepne sa wybrane dni, powtarzanie, tryb tygodniowy, tryb wlasny oraz programy pogodowe. W zaleznosci od typu ustawia sie start, czas trwania, powtorzenia, przerwy, interwaly, dni tygodnia albo priorytety.

## Bez korekt
Dla programu nie sa stosowane automatyczne korekty czasu.

## Odciecie
Jesli skorygowany czas pracy jest krotszy niz ustawiony limit, program zostanie pominiety.

## Aktywuj stacje glowna
Stacje ustawione na aktywacje mastera przez program uzyja mastera wybranego w programie.

----

# Jednorazowe uruchomienie
Ta strona sluzy do testow lub jednorazowego podlewania. Dla kazdej stacji mozna ustawic minuty i sekundy.

## Uruchom teraz
Uruchamia zaznaczone stacje.

## Resetuj czas
Usuwa ustawione czasy.

----

# Rozszerzenia
Strona rozszerzen sluzy do zarzadzania pluginami.

## Zarzadzaj
Otwiera menedzer rozszerzen, gdzie pluginy mozna wlaczac, wylaczac, instalowac i aktualizowac.

## Zainstaluj nowe rozszerzenie
Pokazuje dostepne rozszerzenia z repozytorium.

## Wlasny plugin ZIP
Instaluje plugin z pliku ZIP. Plik musi zawierac kompletna strukture pluginu.

## Wylacz wszystko / Wlacz wszystko
Steruje wszystkimi zainstalowanymi rozszerzeniami naraz.

## Sprawdzanie aktualizacji
Automatycznie sprawdza, czy sa dostepne nowe wersje pluginow.

## Wczytaj zmiany / Zmiany
Pobiera i pokazuje najnowsze zmiany z repozytorium pluginow.

## Automatyczne aktualizacje
Gdy sa wlaczone, pluginy aktualizuja sie automatycznie. Najpierw nalezy aktualizowac OSPy, a dopiero potem pluginy.

----

# Dziennik
Strona dziennika pokazuje zapisy podlewania, e-maili i zdarzen. Dane mozna pobrac jako CSV albo usunac. Usuniecie jest nieodwracalne.

----

# Ustawienia
Ustawienia sa podzielone na sekcje: system, pogoda, uzytkownicy, bezpieczenstwo, czujniki, obsluga stacji, stacje glowne, czujnik deszczu, logowanie, restart, backup i SSL.

## System
Nazwa systemu, motyw, format czasu, adres i port HTTP/S, jezyk, obrazy stacji oraz widocznosc pluginow i czujnikow na stronie glownej.

## Pogoda
Wlacza funkcje pogodowe, klucz API i lokalizacje.

## Uzytkownicy
Zarzadza logowaniem, haslem i dodatkowymi uzytkownikami.

## Bezpieczenstwo
Obejmuje ochrone formularzy, HTTPS, nazwe domeny i wlasne certyfikaty.

## Czujniki
Ustawia haslo do wysylania firmware do czujnikow.

## Obsluga stacji
Ustawia maksymalne uzycie, liczbe wyjsc, opoznienie stacji i minimalny czas pracy.

## Stacje glowne
Konfiguruje pierwsza i druga stacje glowna oraz opoznienia wlaczenia i wylaczenia.

## Czujnik deszczu
Wlacza czujnik, typ styku i opoznienie po deszczu.

## Logowanie
Wlacza logi uruchomien, e-maili, zdarzen i debugowania.

## Restart systemu
Pozwala zrestartowac oprogramowanie, zrestartowac Raspberry Pi, wylaczyc je lub przywrocic ustawienia domyslne.

## Backup systemu
Pozwala pobrac lub wgrac kopie konfiguracji.

## Certyfikat SSL
Pozwala wgrac albo wygenerowac certyfikat HTTPS.

----

# Stacje
Strona stacji ustawia nazwe, uzycie, opad, pojemnosc gleby, wspolczynnik ETo, korekte bilansu, podlaczenie, ignorowanie deszczu, master, notatki i obraz.

----

# Czujniki
Na stronie czujnikow mozna dodawac i usuwac czujniki. Obslugiwane sa czujniki radiowe i sieciowe oraz typy takie jak suchy kontakt, wyciek, wilgotnosc, ruch, temperatura, ultradzwiek i wilgotnosc gleby.

## Czujniki Shelly
Urzadzenia Shelly mozna zintegrowac przez plugin Shelly Cloud Integration i uzywac ich danych w OSPy.

----

# Pomoc
Strona pomocy zawiera dokumentacje OSPy, API, sprzetu i pluginow. Pliki Markdown z katalogow dokumentacji sa pokazywane automatycznie.

----

# Wylogowanie
Przycisk wylogowania konczy aktualna sesje w interfejsie WWW.

----
