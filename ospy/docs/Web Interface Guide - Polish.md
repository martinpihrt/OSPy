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
Obejmuje ochrone formularzy, HTTPS, nazwe domeny, wlasne certyfikaty oraz opcje dostepu do API.

### API CORS allowed origin
Ta opcja steruje naglowkiem `Access-Control-Allow-Origin`, ktorego API uzywa dla klientow uruchamianych w przegladarce. `*` pozwala na dowolny origin, pojedyncza wartosc taka jak `https://example.com` pozwala tylko na ten origin, wiele originow mozna rozdzielic przecinkami, a pusta wartosc wylacza naglowki CORS. Nie zastepuje to logowania do API; okresla tylko, ktore originy przegladarki moga czytac odpowiedzi API.

### Enable API JSONP
Ta opcja wlacza starszy parametr `callback` dla odpowiedzi JSONP z API. Pozostaw ja wylaczona, chyba ze stara integracja wymaga JSONP. Zwykli klienci API powinni uzywac JSON z CORS.

### Remembered browser logins
Strona logowania moze zapamietac przegladarke za pomoca dlugoterminowego losowego tokenu zapisanego w bezpiecznym cookie. OSPy przechowuje tylko hash tego tokenu, a nie haslo uzytkownika. Przycisk Revoke usuwa wszystkie zapamietane logowania; dotkniete przegladarki musza zalogowac sie ponownie haslem.

## Czujniki
Ustawia haslo do wysylania firmware do czujnikow.

## Obsluga stacji
Ustawia maksymalne uzycie, liczbe wyjsc, przerwe miedzy stacjami i minimalny czas pracy. Maksymalne uzycie okresla, czy stacje moga pracowac jednoczesnie. `0` oznacza brak limitu, `1` oznacza jedna stacje naraz, gdy kazda stacja ma uzycie `1`.

Przerwa miedzy stacjami jest wstawiana miedzy kolejnymi uruchomieniami stacji, gdy harmonogram nie moze uruchomic ich jednoczesnie. Nie przesuwa stacji wzgledem stacji glownej. Przyklad: przy maksymalnym uzyciu `1` i uzyciu stacji `1` wartosc `30` uruchomi nastepna stacje 30 sekund po zakonczeniu poprzedniej.

Minimalny czas pracy moze pominac te przerwe, jesli poprzednie uruchomienie bylo krotsze. Przyklad: przy przerwie `30` i minimalnym czasie pracy `10` stacja dzialajaca tylko 5 sekund nie wymusi 30-sekundowej przerwy.

## Stacje glowne
Konfiguruje stacje glowna 1, stacje glowna 2 oraz przesuniecia czasu wlaczenia i wylaczenia. Stacja glowna to zwykle pompa lub glowny zawor wody i jest uzywana tylko dla stacji, ktore maja ja przypisana.

Przesuniecie startu jest wzgledem startu stacji. Wartosci ujemne wlaczaja stacje glowna wczesniej, dodatnie pozniej. Przyklad: `-10` wlacza stacje glowna 10 sekund przed stacja, `+10` wlacza ja 10 sekund po stacji.

Przesuniecie wylaczenia jest wzgledem konca stacji. Wartosci ujemne wylaczaja stacje glowna wczesniej, dodatnie utrzymuja ja wlaczona dluzej. Przyklad: `-5` wylacza stacje glowna 5 sekund przed koncem stacji, `+20` wylacza ja 20 sekund po koncu stacji.

Ta sama logika dotyczy stacji glownej 2, ktora ma wlasne przesuniecia startu i wylaczenia.

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
