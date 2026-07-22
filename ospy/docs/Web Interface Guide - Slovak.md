OSPy sprievodca webovým rozhraním v slovencine
====

## SQLite ako primárne úložisko (beta)

Keď Diagnostika oznámi **Pripravenosť SQLite primary beta: Pripravené**, Nastavenia sprístupnia v poli **Režim úložiska nastavení** voľbu **SQLite primárne (beta)**. OSPy pred vstupom do tohto režimu aj návratom z neho vytvorí úplnú systémovú zálohu, spoločne potvrdí overenú SQLite a shelve/DBM kópiu a reštartuje sa. Pri ďalšom štarte SQLite pred použitím ako zdroja nastavení nezávisle overí; synchronizovaná shelve/DBM kópia zostáva okamžitou zálohou. Chýbajúci aktivačný marker, poškodená databáza, nezhoda kontrolného súčtu či schémy alebo neplatné nastavenie bezpečne ponechá OSPy na shelve/DBM a problém zobrazí Diagnostika. K automatickému prepnutiu nikdy nedôjde a návrat do režimu **Overovací** je kedykoľvek dostupný rovnakým postupom so zálohou a reštartom.

    Inštalácia OSPy
    Prihlásiť sa
    Domovská stránka
        Normálna - % doby programu
        Aktívne - Oneskorenie pri daždi
        Plánovač - Ručne
        Povolené - Zakázané
        Zastaviť všetky stanice
        Štatistika zavlažovania (graf)
        Potlačené oneskorením pri daždi
        Zistený dážď
        Teplota CPU
        Využitie CPU
        Verzia programu OSPy
        Externá IP adresa
        Doba prevádzky
        Diagnostika
    Spätná väzba (Feedback)
    Programy
        Pridat nový program
        Skupiny programov
        Pridať skupinu
        Premenovať skupinu
        Zapnúť/Vypnúť skupinu
        Kopírovať skupinu
        Odstrániť skupinu
        Spustiť teraz
        Upraviť
        Kopírovať
        Presunúť do skupiny
        Vymazať všetko
        Zapnúť/Vypnúť program
        Upozornenie na kolízie
        Typ plánovača
            Vybrané dni (Jednoduchý)
                Čas štartu
                Trvanie
                Opakovať
                Opakovanie
                Pauza
            Vybrané dni (Rozšírené)
                Plánovač
            Opakovanie (Jednoduché)
                Interval zavlažovania
                Štart v dňoch
                Čas štartu
                Trvanie
                Opakovať
                Opakovanie
                Pauza
            Opakovanie (Rozšírené)
                Interval zavlažovania
                Štart v dňoch
                Plánovač
            Týždenný (Rozšírené)
                Pondelok-Nedeľa
            Vlastné
                Interval zavlažovania
                Štart v dňoch
                Deň 1 - Deň 7
            Týždenný (Predpoveď počasia)
                Minimálne zavlažovanie
                Maximálne zavlažovanie
                Maximálna dávka
                Pomer pauzy
                Uprednostnené momenty vykonávania
                    Deň
                    Čas štartu
                    Prednosť
                    Pridať - Zmazať
        Žiadne úpravy
        Odrezať
        Aktivovať hlavnú stanicu
    Spustiť raz
        Spustiť teraz
        Zmazať čas
    Doplnky
        Spravovať
        Nainštalovať nový doplnok
            Vlastný doplnok (ZIP)
            Github (https://github.com/martinpihrt/OSPy-plugins/archive/master.zip)
        Zakázať všetky
        Povoliť všetky
        Povoliť kontrolu aktualizácií
        Načítať zmeny
        Zmeny
        Automatické aktualizácie
    Denník
        Denník udalostí
        Stiahnuť denník udalostí ako
        Vymazať denník
        Zmazať záznam Email
    Nastavenia
        Systém
            Zobraziť tipy
            Názov systému
            Šablóna webu
            24-hodinový čas
            HTTP IP adresa
                O čísle portu
            HTTP/S port
            Zobraziť doplnky na hlavnej stránke
            Zobraziť senzory na hlavnej stránke
            Jazyk systému
            Zobrazenie obrázkov na staniciach
        Počasie
            Použiť počasie
            Poskytovateľ počasia
            Stormglass API kľúč
            Poloha
        Užívatelia
            Zakázať zabezpečenie
            Meno správcu
            Aktuálne heslo
            Nové heslo
            Potvrďte heslo
            Ďalši užívateľia
        Zabezpečenie
            Ochrana formulárov
            Použíť HTTPS
            Doménové meno
            Používanie vlastného prístupu HTTPS
            API CORS povolený origin
            Povoliť API JSONP
            Zapamätané prihlásenie v prehliadači
        Senzory
            Heslo pre nahrávanie firmvéru
        Konfigurácia staníc
            Vytaženie
                O sekvenčných a súbežných režimoch
            Počet výstupov
            Pauza medzi stanicami
            Minimálna doba prevádzky
        Nastavenie hlavnej stanice
            Hlavná stanica
            Druhá hlavná stanica
            Aktivovať relé
            Posun štartu hlavnej stanice
            Posun vypnutia hlavnej stanice
            Posun štartu hlavnej stanice 2
            Posun vypnutia hlavnej stanice 2
        Dažďový senzor
            Používať senzor
            Normálne otvorený
            Nastaviť dažďové oneskorenie
            Dážďové oneskorenie
        Zaznamenávanie udalostí
            Povoliť záznam udalostí
            Max položiek
            Aktivovať záznam Emailov
            Max položiek
            Povoliť protokol udalostí
            Max položiek
            Povoliť protokol ladenia
        Reštartovať systém
            Reštart OSPy
            Reštart HW
            Vypnúť
            Predvolené nastavenia
        Záloha a obnovenie
            Stiahnuť
            Nahrať
        Certifikát SSL
            Nahrať
            Generovať
    Stanica
        Stanica
        Názov
        Využitie
        Závlaha
        Zásoba
        ETo faktor
        Zostatok
        Pripojené
        Ignorovať Dážď
        ZAP Hlavné?
            Nepoužité
            ZAP Hlavné
            ZAP Hlavné 2
            ZAP Hlavný 1/2 programom
        Poznámky
        Obrázok
    Senzory
        Pridať nový senzor
            Vlastnosti snímačov
        Odstrániť všetky senzory
    Pomocník
        OSPy
            Readme
            Changelog
            Programs
            Web Interface Guide - Czech
            Web Interface Guide - English
            Web Interface Guide - German
            Web Interface Guide - Polish
            Web Interface Guide - Russian
            Web Interface Guide - Serbian
            Web Interface Guide - Slovak
        API
            Readme
            Podrobnosti
        Plug-ins
            Readme
            Usage Statistics
            LCD Display
            Pressure Monitor
            Voice Notification
            Pulse Output Test
            Button Control
            CLI Control
            System Watchdog
            Voltage and Temperature Monitor
            Remote Notifications
            System Information
            MQTT
            Air Temperature and Humidity Monitor
            Wind Speed Monitor
            Weather-based Rain Delay
            Relay Test
            UPS Monitor
            Water Consumption Counter
            SMS Modem
            Signaling Examples
            Email Notifications
            Remote FTP Control
            System Update
            Water Meter
            Webcam Monitor
            Weather-based Water Level Netatmo
            Direct 16 Relay Outputs
            MQTT Zone Broadcaster
            System Debug Information
            Weather-based Water Level
            Real Time and NTP time
            Water Tank
            Humidity Monitor
            Monthly Water Level
            Pressurizer
            Ping monitor
            Temperature Switch
            Pool Heating
            E-mail Notifications SSL
            Sunrise and Sunset
            Photovoltaic Boiler
            IP CAM
            Modbus stations
            CHMI
            Proto
            Label Maker
            IP Scanner
            Database Connector
            OSPy Backup
            MQTT Home Assistant
            Shelly Cloud Integration
            Current loop tanks monitor

----

# Inštalácia OSPy
Na čistú inštaláciu sa odporúča Raspberry Pi OS alebo Debian 12 a Python 3.11 či novší. Inštalátor vždy stiahne stabilnú vetvu OSPy `master`. Pri prvom spustení sa na prihlasovacej stránke zobrazí vygenerované heslo správcu; po prihlásení ho ihneď zmeňte v Možnostiach.

## POMOCOU INŠTALAČNÉHO SKRIPTU
Prihláste sa do Pi pomocou SSH. Zadajte alebo skopírujte a vložte nasledujúci príkaz:
Pamätajte: Príkazy na Raspberry Pi rozlišujú veľké a malé písmená.

```bash
wget https://raw.githubusercontent.com/martinpihrt/OSPy/master/ospy_setup.sh
sudo bash ospy_setup.sh
```

Ponuka oddeľuje základné požiadavky od voliteľných balíkov MQTT a multimédií. Vyberte `/opt` alebo domovský adresár používateľa, ktorý spustil skript. Inštalátor nikdy nevymaže, neresetuje ani automaticky neaktualizuje existujúcu Git inštaláciu. Službu vytvorí z verzovanej šablóny systemd, spustí ju a overí jej stav; pri chybe zobrazí posledné záznamy služby. Reštart sa odporúča iba po zmene I²C alebo skupín. Úspešná inštalácia je dostupná na porte 8080. Podrobný bezpečný postup, ručná aktualizácia a lokálna obnova účtu sú v dokumente Pomocníka **Clean installation**.

----

# Odhlásiť sa
Po kliknutí na tlačidlo "Odhlásiť sa" sa užívateľ odhlási zo systému.

----

# Dvojfázové zabezpečenie (2FA)
Dvojfázové overenie chráni hlavný administrátorský účet druhým krokom po zadaní hesla. Otvorte **Nastavenia → Dvojfázové zabezpečenie → Konfigurovať** a vyberte práve jednu metódu: **Autentifikačná aplikácia (TOTP)**, **Kód odoslaný e-mailom** alebo **Vypnuté**. Obe metódy nemôžu byť aktívne súčasne.

Pre TOTP spustite raz `python setup.py install`, ak chýba podpora QR. Naskenujte QR kód pomocou Google Authenticatora, Microsoft Authenticatora, 2FAS, Aegis alebo inej TOTP aplikácie a zadajte aktuálny šesťmiestny kód. OSPy aktivuje tajný kľúč až po potvrdení. TOTP vyžaduje správny systémový čas.

E-mailové overenie je dostupné iba vtedy, keď je **E-mail Notifications SSL** nainštalovaný, spustený a má nastavený SMTP server, účet, heslo a príjemcu. Pri zapnutí OSPy ihneď odošle potvrdzovací kód. Prihlasovacie kódy platia päť minút a nikdy sa neukladajú do fronty doplnku na neskoršie odoslanie.

Po zapnutí bezpečne uložte zobrazené jednorazové záložné kódy. Každý môže raz nahradiť druhý faktor a potom sa odstráni; znovu sa nezobrazí. Zmena alebo vypnutie 2FA zruší všetky zapamätané prihlásenia prehliadačov. Pri strate telefónu alebo nedostupnom e-maile použite záložný kód; bez neho obnovte zálohu konfigurácie alebo lokálne resetujte 2FA na zariadení OSPy.
    Odhlásiť sa

----

# Prihlásiť sa
Prihlasovacia stránka predstavuje textové pole pre zadanie mena a hesla. Predvolené meno je **admin**. Pri prvej inštalácii bude vygenerované náhodné heslo (toto heslo je potom nutné zmeniť v nastavení na iné heslo! Na stránke - záložke "Nastavenia" sa odporúča zmeniť si heslo (alebo aj meno) na Vaše nové vlastné heslo.
Zadajte meno, heslo a kliknite na tlačidlo **PRIHLÁSIŤ SA**.


----

# Domovská stránka
Domovská stránka je hlavným ovládacím centrom webového rozhrania. To zahŕňa:

* Hodiny zobrazujúce aktuálny čas Na všetkých stránkach.
* Navigačná lišta v hornej časti pre pohyb medzi stránkami. Rozhranie sa tiež nachádza na ostatných stránkach okrem prihlasovacej stránky.
* Sada tlačidiel pre vykonávanie globálnych zmien správania systému.
* Časová os, ktorá poskytuje informácie o dokončených a naplánovaných zavlažovacích udalostiach.
* Graf, ktorý poskytuje informácie o zavlažovacích udalostiach.
* Zápätie, ktoré je prítomné na všetkých stránkach (ak je prihlásený užívateľ). Zápätie obsahuje: Teplota procesora, Využitie procesora, Verzia softvéru, Externá IP adresa, Doba prevádzky OS.
* Niektoré rozšírenia vedia injektovať domácu stránku a pridávať ďalšie prvky. Napríklad rozšírenie astral pridáva do časovej osi grafickej znázornená východu a západu slnka. Rozšírenie tank monitor grafické stĺpce s objemom a množstvom vody.


## Normálna - % doby programu
Tlačidlo, ktoré umožňuje nastaviť „hladinu vody“ ako celkové percento doby behu pre všetky zavlažovacie programy (pri programoch predĺžiť, alebo skrátiť ich nastavenú dobu).

## Aktívne - Oneskorenie pri daždi
Oneskorenie pri daždi. Tlačidlo, ktoré umožňuje na zadanú dobu pozastavenia zavlažovania pre všetky stanice okrem tých, ktoré boli nastavené tak, aby ignorovali dážď na stránke Stanice.

## Plánovač - Ručne
Plánovač - Ručne. Tlačidlo, ktoré prepína systém medzi plánom (automatickým režimom) a manuálnym režimom, ktorý umožňuje priame ovládanie staníc.

## Povolené - Zakázané
Tlačidlo pre povolenie, alebo zakázanie behu OSPy programu (pri zakázané nepobeží plánovač).

## Zastaviť všetky stanice
Tlačidlo „Zastaviť všetky stanice“ slúži na okamžité zrušenie spusteného zavlažovacieho programu alebo aktívnej stanice.

## Štatistika zavlažovania (graf)
Ak je v plánovači nastavený aspoň jeden program, v spodnej časti obrazovky bude nakreslený graf s množstvom vody dodanej pre každú stanicu (programy).

## Potlačené oneskorením pri daždi
Ak je aktivované oneskorenie pri daždi, zobrazí sa „Blokované systémom“ a všetky stanice (okrem tých, ktoré boli nastavené tak, aby ignorovali dážď na stránke Stanice) budú po určitú dobu blokované.

## Zistený dážď
Ak je aktivovaný dažďový senzor, zobrazí sa „Blokované dažďovým senzorom“ a všetky stanice (okrem tých, ktoré boli nastavené tak, aby ignorovali dážď na stránke Stanice) budú blokované.

## Teplota CPU
Teplota procesora Raspberry pri. Zobrazenú teplotu je možné prepínať medzi C a F.

## Využitie CPU
Využitie procesora Raspberry pri. Využitie je zobrazené v %.

## Verzia programu OSPy
Odkaz na úložisko softvéru projektu a číslo revízie nainštalovaného softvéru.
Stabilné zostavenie z vetvy `master` používa číselnú verziu, napríklad `3.0.238`. Testovacie zostavenie z vetvy `beta` zobrazuje rovnakú revíziu s príponou `-beta`, napríklad `3.0.238-beta`. Po presune rovnakého commitu do `master` prípona zmizne, ale číslo revízie sa nezmení.

### Bezpečná aktualizácia a automatický návrat

Pred každou aktualizáciou doplnok System Update najprv uloží nastavenia a vytvorí overenú bezpečnostnú zálohu. Potom, ešte pred zmenou súborov sledovaných systémom Git, spustí externý watchdog. Na inštaláciách so systemd beží watchdog v samostatnej dočasnej službe a zostáva aktívny aj počas reštartu OSPy. Bez systemd sa použije oddelený pomocný proces.

Nový proces OSPy potvrdí úspešnú aktualizáciu až vtedy, keď plánovač zaznamená novú odozvu heartbeat a webové rozhranie začne prijímať spojenia. Ak sa zdravé spustenie nepotvrdí do 120 sekúnd, watchdog automaticky vráti predchádzajúci commit aj pôvodnú vetvu a znova spustí OSPy. Ak watchdog nemožno spustiť, aktualizácia sa zastaví skôr, než sa zmenia sledované súbory. Výsledok watchdogu je dostupný aj v Diagnostike v stave doplnku System Update.

System Update zobrazuje úplný commit práve spustenej verzie aj presný cieľový commit z vybraného kanála. Za overené stabilné vydanie považuje iba anotovaný Git tag v tvare `vX.Y.Z`, ktorého commit je súčasťou `origin/master`. Správa anotovaného tagu slúži ako stručné poznámky k vydaniu. Ľahké tagy, iné názvy a tagy mimo `master` sa neponúkajú.

Návrat na posledné overené stabilné vydanie aj ručný návrat na starší commit najprv uloží nastavenia, vytvorí overenú bezpečnostnú zálohu a spustí rovnaký externý watchdog ako bežná aktualizácia. Stabilný návrat prepne pracovnú vetvu na `master`. Tag vydania vytvára správca projektu ručne až po úspešných testoch; samotný doplnok tagy nevytvára.

## Externá IP adresa
Externá IP adresa pre systém OSPy (adresa vášho poskytovateľa pripojenia - routera). Testované prostredníctvom služby pihrt.com.

## Doba prevádzky
Doba behu systému Raspberry pri zapnutí (alebo reštarte).

## Diagnostika
Riadok **Databáza** navyše zobrazuje aktívne úložisko nastavení a pripravenosť SQLite. Táto prechodná verzia naďalej číta a zapisuje existujúce súbory shelve/DBM. Samotná kontrola pripravenosti používa iba dočasnú databázu v pamäti a nevytvára súbor ani migráciu údajov. Ak podpora SQLite v Pythone nie je dostupná, OSPy naďalej používa shelve/DBM a dôvod zobrazí iba ako pasívnu informáciu, nie ako poruchu systému.

Po každom úspešnom uložení nastavení vytvorí OSPy vedľa aktívnych súborov shelve/DBM aj overenú tieňovú kópiu `options.sqlite3`. Zapisuje ju cez dočasný súbor a atomicky ju nahradí až po úspešnej kontrole schémy, kľúčov, hodnôt a integrity. Pri spustení OSPy z tieňovej kópie nikdy nenačítava nastavenia. Zlyhanie synchronizácie ponechá autoritatívne uloženie shelve nedotknuté a zobrazí sa ako varovanie v riadku **Databáza**; chýbajúca tieňová kópia čaká na ďalšie uloženie nastavení.

Pri spustení OSPy porovná autoritatívne hodnoty shelve s kontrolnými súčtami SHA-256 uloženými v tieňovej schéme 2. Pri tomto automatickom porovnaní nedeserializuje hodnoty pickle z tieňovej kópie a nikdy ich nepoužije na obnovu ani spustenie OSPy. Zhodná kópia sa označí ako overená; chýbajúce, zmenené alebo neočakávané kľúče a poškodenie kontrolného súčtu či databázy sa zobrazia ako varovanie, zatiaľ čo shelve zostane v prevádzke. Tieňová kópia schémy 1 z predchádzajúcej prechodnej fázy sa nečíta a pri ďalšom uložení nastavení sa bezpečne nahradí.

Pri spustení a po každom úspešnom nahradení tieňovej kópie vykoná OSPy skúšobné dekódovanie až vtedy, keď sa v jedinom snímku iba na čítanie zhodujú všetky kľúče a kontrolné súčty, a na zrekonštruované hodnoty SQLite použije bežnú validáciu nastavení. Zrekonštruovaný slovník sa zahodí a nikdy sa nepriradí bežiacej konfigurácii. Diagnostika uvedie, či test čítania SQLite prešiel; zlyhanie zostane varovaním a OSPy pokračuje výhradne s už aktívnymi nastaveniami shelve.

Tieňová schéma 3 obsahuje aj manifest s celkovým počtom záznamov a kontrolným súčtom nad úplným zoradeným zoznamom kľúčov a ich súčtov. Nezávisle tak pred dekódovaním odhalí odstránený alebo pridaný riadok. OSPy vykoná a zahodí úplnú skúšku obnovy pre aktuálnu SQLite kópiu aj predchádzajúcu kópiu v záložnom adresári. Diagnostika zobrazí oba výsledky. Neúspešný alebo nedostupný kandidát obnovy nikdy nezmení voľbu pri spustení; autoritatívne zostáva shelve/DBM.

Pri spustení OSPy použije prvého nezávisle overeného kandidáta SQLite iba na skúšku obnovy v izolovanom dočasnom adresári. Vytvorí z neho dočasnú databázu shelve/DBM, znovu ju otvorí, overí všetky nastavenia a porovná ich serializované hodnoty; potom dočasný adresár odstráni. Aktívna databáza ani zdroj nastavení pri spustení sa nemenia. Ak je aktuálna SQLite kópia poškodená, skúška môže použiť overenú záložnú kópiu, zatiaľ čo bežiace nastavenia sa stále načítajú z autoritatívneho shelve. Riadok **Databáza** v Diagnostike zobrazuje výsledok, zdroj a počet nastavení.

OSPy navyše iba simuluje núdzové rozhodnutie pre prípad, že by boli neplatné všetky databázy shelve/DBM. Prednosť má nezávisle overená aktuálna SQLite kópia; overená záloha by sa zvolila iba pri chybe aktuálnej kópie. Vybraný slovník sa zahodí a nikdy sa nepriradí k bežiacim nastaveniam, takže ani tento stav zatiaľ neaktivuje obnovu zo SQLite. Diagnostika zobrazuje pripravenosť, hypotetický zdroj a počet nastavení.

Experimentálna voľba **Povoliť núdzovú obnovu nastavení SQLite** v kategórii **Úložisko nastavení** je predvolene vypnutá. Po zapnutí OSPy vytvorí nesekretný atómový aktivačný marker až po nezávislom overení SQLite schémy 3; povolenie musí obsahovať aj samotná overená kópia, takže marker ani databáza samostatne nestačia. Obnova sa použije iba vtedy, keď sú neplatné aktuálna, dočasná aj záložná databáza shelve/DBM. OSPy uprednostní aktuálnu SQLite kópiu, prípadne overenú zálohu, obnoví a znovu overí shelve databázu v dočasnom adresári a až potom ju načíta. Existujúce aktuálne a záložné adresáre sa neprepíšu a bežné ukladanie zostáva shelve/DBM. Vypnutie odstráni marker ešte pred zápisom nastavení. Diagnostika a štartovacia správa zobrazia použitie alebo chybu; po obnove skontrolujte systém a vytvorte zálohu.

Experimentálna voľba **Uprednostniť overené čítanie nastavení SQLite** v kategórii **Úložisko nastavení** je tiež predvolene vypnutá. Po zapnutí OSPy vždy najprv načíta a overí shelve/DBM, porovná úplnú sadu kľúčov a kontrolných súčtov SQLite s týmto presným autoritatívnym snímkom a nezávisle dekóduje a overí každú hodnotu. Až úplná zhoda priradí ekvivalentný slovník SQLite k bežiacim nastaveniam. Chýbajúca kópia, rozdiel, poškodenie alebo chyba dekódovania ponechá už načítané hodnoty shelve bez prerušenia. Zápisy, rotácia adresárov a zálohy naďalej používajú výhradne shelve/DBM; SQLite zostáva overenou kópiou. Diagnostika zobrazuje použitie, vypnutie alebo návrat k shelve.

Experimentálna voľba **Vyžadovať overené SQLite na potvrdenie nastavení** v kategórii **Úložisko nastavení** je predvolene vypnutá. Po zapnutí smie nový adresár nastavení nahradiť aktívne údaje iba vtedy, keď sa v dočasnom adresári úspešne zapíše a nezávisle overí databáza shelve/DBM aj jej SQLite kópia. Ak SQLite nie je dostupné alebo zápis či overenie zlyhá, OSPy odstráni celý nepotvrdený dočasný adresár, zachová predchádzajúce aktívne nastavenia aj čas posledného uloženia a oznámi chybu zápisu. Vypnutie obnoví kompatibilné správanie s prioritou shelve. Úspešné prísne potvrdenie možno čítať overenou SQLite cestou, ale shelve/DBM zostáva formátom ukladania a záloh. Aktívnu politiku potvrdenia zobrazuje Diagnostika.

Diagnostika uchováva neautoritatívny **dôkaz migrácie SQLite**: počty po sebe nasledujúcich úspešných štartov s overeným čítaním a prísnych dvojitých zápisov. Chyba vynuluje iba príslušnú sériu a uloží čas a dôvod. Samostatný atomicky zapisovaný súbor neobsahuje nastavenia a nikdy sa nepoužíva na spustenie, obnovu ani výber úložiska.

Jazyk rozhrania sa pri skorom štarte naďalej najprv načíta z platnej databázy shelve/DBM. Ak je povolené overené čítanie SQLite, bootstrap porovná všetky kľúče a kontrolné súčty s týmto presným shelve snímkom a až po úplnej zhode načíta zo SQLite jedinú hodnotu `lang`. Chýbajúca, staršia, rozdielna alebo poškodená SQLite kópia vždy bezpečne použije jazyk zo shelve. Kontrola chýbajúcej databázy sama nevytvorí prázdny súbor.

Selektor **Režim úložiska nastavení** združuje bezpečné prechodové voľby. **Kompatibilný** ponechá shelve/DBM ako hlavné úložisko a SQLite ako voliteľnú tieňovú kópiu. **Overovací** zapne núdzovú obnovu, overené čítanie a prísny dvojitý zápis; ani tento režim nerobí zo SQLite hlavnú databázu. Jednotlivé prepínače zostávajú dostupné na pokročilé riadenie a ich zmiešaná kombinácia sa automaticky označí ako **Vlastné pokročilé nastavenia**. Staršie inštalácie odvodia režim z uložených prepínačov bez zmeny ich hodnôt.

Diagnostika navyše vyhodnocuje pasívnu kontrolu **Pripravenosť SQLite primary beta**. Stav Pripravené vyžaduje režim Overovací, overenú aktuálnu tieňovú kópiu, úspešné testy čítania a obnovy aktuálnej aj záložnej kópie, úspešnú skúšku obnovy a núdzového výberu, zapnutú núdzovú obnovu, overené čítanie a prísny dvojitý zápis a najmenej päť po sebe idúcich overených štartov a dvadsať prísnych zápisov. Dovtedy Diagnostika zobrazuje zber dôkazov alebo konkrétne blokujúce kontroly. Táto kontrola nikdy automaticky neprepne úložisko; hlavným zostáva shelve/DBM.

Tlačidlo **Diagnostika** v päte otvorí administrátorskú stránku na kontrolu, ako OSPy a jeho doplnky využívajú systém.

Keď Diagnostika zistí chybu, otvorí červené okno s opisom problému, dostupnými podrobnosťami, možným riešením a odkazom na súvisiacu stránku. Administrátor môže rovnaké okno zapnúť aj na domovskej stránke voľbou **Nastavenia > Diagnostika > Zobrazovať chyby diagnostiky na domovskej stránke**. Chybové okno má prednosť pred upozornením na aktualizáciu. Vypnutie voľby ovplyvní iba domovskú stránku; chyby zostanú viditeľné v Diagnostike.

Stránka používa rozbaľovacie sekcie **Stav systému**, **Výkon a procesy** a **Kontrola zabezpečenia**. Kliknutím na tmavý pruh sa sekcia rozbalí alebo zbalí. **Stav systému** priraďuje každej prevádzkovej oblasti stav v poriadku, varovanie, chyba alebo nenakonfigurované. Sleduje heartbeat plánovača, posledný úspešný výpočet plánu a najbližší beh, zápisy príkazov do výstupov, komunikáciu snímačov, dostupnosť databázy nastavení, voľné miesto, chyby povolených doplnkov, pripravenosť e-mailu, počasie, internetové pripojenie a najnovšiu dostupnú zálohu. Úspešný zápis výstupu potvrdzuje, že OSPy odovzdalo požadovaný stav ovládaču; bez hardvérovej spätnej väzby nepotvrdzuje fyzické zopnutie relé.

Riadok **Jazyky** porovnáva každý prekladový katalóg s aktuálnou šablónou a pri každom jazyku zobrazuje percento preložených a presný počet chýbajúcich reťazcov. Úplný preklad je zelený, pokrytie od 80 % je žlté a nižšie pokrytie červené. Ide iba o informáciu pre správcov prekladov: stav jazykov nemení celkový stav systému ani neotvára chybové okno Diagnostiky.

**Kontrola zabezpečenia** pasívne vyhodnocuje HTTPS, anonymný prístup, dvojfaktorové overovanie, autentizáciu API snímačov, ochranu API proti CSRF, CORS, heslo snímačov a odporúčané bezpečnostné HTTP hlavičky. Heslo snímača nikdy nezobrazuje a nemení žiadne nastavenie. Profil **Domáca sieť** hodnotí vybrané kompromisy kompatibility ako varovania, zatiaľ čo **Prístup z internetu** vyžaduje šifrovaný, overený a obmedzený prístup. Každý nález obsahuje aktuálny stav, odporúčanie a odkaz na súvisiace nastavenie. Reverzný proxy server môže hlavičky doplniť až po odoslaní odpovede z OSPy; Diagnostika uvádza iba to, čo dokáže zaručiť samotné OSPy.

Zachytené prevádzkové chyby jadra sa zobrazujú v **Stave systému** ako samostatné aktívne problémy. Každý záznam uvádza dotknutú súčasť, počet opakovaní, posledný výskyt, technickú príčinu a odporúčaný postup obnovy. Úspešné zopakovanie operácie automaticky odstráni aktívny problém, zatiaľ čo úplný traceback zostáva v zázname udalostí. Očakávané kompatibilné fallbacky sa ako chyby nezobrazujú.

Rozbaľovacia sekcia **História incidentov** uchováva najviac 200 posledných problémov aj po reštarte OSPy. Filtrovať možno všetky, aktívne, vyriešené a reštartom prerušené incidenty. Opakovanie rovnakého aktívneho problému zvýši jeho počítadlo namiesto vytvárania duplicít; tabuľka uvádza čas otvorenia, posledného výskytu a vyriešenia. História sa atomicky ukladá do overeného JSON súboru s obmedzenou veľkosťou a neukladá celé tracebacky.

Súhrn systému zobrazuje aktuálne využitie CPU, teplotu CPU, dobu behu systému, load average, využitie CPU procesom OSPy, využitie pamäte OSPy, počet vlákien, informácie o platforme a čas posledného obnovenia.

Tabuľka doplnkov zobrazuje všetky dostupné doplnky, či bežia a či sú povolené, ich vlastný prevádzkový stav, aktuálnu záťaž CPU, celkový čas CPU, počet vlákien, čas spustenia, počet reštartov a dostupné akcie. Doplnok môže voliteľne poskytovať funkciu `health()`, ktorá vracia napríklad `{'status': 'ok', 'summary': '...', 'details': '...'}`; povolené stavy sú `ok`, `warning`, `error` a `unknown`. Staršie doplnky bez tejto funkcie zostávajú plne kompatibilné a zobrazujú stav „nehlásené“. Chyba alebo prekročenie časového limitu kontroly stavu nezastaví doplnok ani stránku Diagnostika. Dáta sa obnovujú automaticky, takže stránku je možné nechať otvorenú pri sledovaní zaťaženia systému.

V predvolenom stave sú doplnky zoradené podľa aktuálnej záťaže CPU od najvyššej po najnižšiu. Pomocou voľby **Zoradiť doplnky** je možné prepnúť zoradenie podľa názvu doplnku alebo podľa celkového času CPU, keď je potrebný stabilný zoznam alebo hľadanie dlhodobých spotrebiteľov CPU.

Akcia **Otvoriť** otvorí stránku doplnku. **Restart plugin** reštartuje iba vybraný bežiaci doplnok; nereštartuje celé OSPy.

Ak sa zobrazí varovanie pri obnovení, posledné automatické čítanie z diagnostického API zlyhalo alebo vrátilo kontrolovanú chybu. Existujúce dáta môžu zostať zobrazené do ďalšieho úspešného obnovenia a varovanie sa po úspešnom obnovení automaticky vymaže.

----

# Spätná väzba (Feedback)
Tlačidlo **Feedback** v hlavičke vľavo od názvu systému otvorí stránku na hlásenie chýb, návrhov na zlepšenie a otázok. Stránka je dostupná prihláseným správcom aj používateľom; na prihlasovacej stránke sa tlačidlo nezobrazuje.

Vyberte **Bug report**, **Feature request** alebo **Question** a potom zadajte stručný názov a podrobný popis. Tlačidlo **Continue to GitHub** otvorí predvyplnené nové Issue na GitHube. Používateľ sa prihlási na GitHub, obsah skontroluje a odošle ho tam. OSPy neukladá prístupový token GitHubu a pred týmto potvrdením Issue nevytvorí.

Možnosť priložiť systémové informácie je predvolene zapnutá a pred odoslaním zobrazí presný náhľad: verziu a dátum OSPy, architektúru, distribúciu a verziu operačného systému a verziu Pythonu. Názov systému OSPy, meno obsluhy, IP adresy ani jedinečný identifikátor štatistík používania sa neprikladajú. Túto možnosť zrušte, ak chcete odoslať iba vlastný text.

Tlačidlo **View existing reports** otvorí GitHub Issues projektu. **GitHub Discussions** vedie priamo do diskusií projektu a je vhodné na všeobecné otázky a spoločné návrhy. Snímky obrazovky a ďalšie súbory možno priložiť po otvorení GitHubu.

Formulár používa existujúce prihlásenie OSPy a ochranu CSRF. Pri prechode na GitHub sa adresa otvorenej stránky OSPy neposiela ako HTTP referrer.

----

# Programy
## Pridat nový program
Tlačidlom "Pridat nový program" vytvoríme nový program plánovača.

## Skupiny programov
Programy je možné usporiadať do rozbaľovacích skupín. Skupiny sa hodia napríklad na oddelenie letných a zimných programov, alebo na prehľadné rozdelenie podľa časti záhrady.

## Pridať skupinu
Tlačidlom "Pridať skupinu" vytvoríme novú skupinu programov.

## Premenovať skupinu
Akcia pre premenovanie skupiny zmení iba názov skupiny. Programy priradené do skupiny zostanú zachované.

## Zapnúť/Vypnúť skupinu
Akcia ZAP/VYP v skupine povolí alebo zakáže všetky programy v danej skupine naraz. Je vhodná napríklad na sezónne prepínanie viacerých programov.

## Kopírovať skupinu
Akcia kopírovania vytvorí novú skupinu a skopíruje do nej všetky programy z pôvodnej skupiny. Skopírované programy sú vytvorené ako zakázané, aby sa nespustili skôr, ako ich skontrolujeme.

## Odstrániť skupinu
Vymazanie skupiny vyžaduje potvrdenie. Programy zo zmazanej skupiny sa presunú do východiskovej skupiny.

## Odložiť skupinu
Tlačidlo „Odložiť skupinu“ vedľa tlačidla „Pridať nový program“ jednorazovo presunie najbližší naplánovaný beh celej skupiny. Vyberieme nový dátum a čas spustenia prvého programu; pred potvrdením sa zobrazí náhľad pôvodného a nového časového rozsahu. Nový začiatok musí byť neskorší ako pôvodný začiatok, musí byť v budúcnosti a je možné ho nastaviť najviac 30 dní dopredu.

OSPy vyhľadá najbližší budúci beh každého povoleného programu v skupine a všetky tieto behy posunie o rovnaký časový rozdiel. Poradie programov, ich dĺžky a vzájomné časové rozostupy zostanú zachované. Napríklad skupinu naplánovanú dnes od 18:00 do 22:00 môžeme odložiť na zajtra od 07:00; presunutý beh sa potom skončí približne o 11:00.

Odklad nemení bežné definície programov ani ich ďalšie naplánované dni. Pôvodný najbližší beh sa iba jednorazovo preskočí a jeho náhrada sa spustí v novom čase. Odložené programy naďalej rešpektujú zapnutie plánovača, dažďové blokovania, dažďový senzor, obmedzenia zaťaženia výstupov a oneskorenia medzi stanicami. Odklad je uložený v nastaveniach a prežije reštart služby OSPy. Pre jednu skupinu je povolený iba jeden aktívny odklad.

Aktívny odklad je pri skupine zobrazený ako pôvodný čas, šípka a nový čas. Tlačidlom „Zrušiť odklad“ ho môžeme odstrániť. Ak pôvodný čas ešte nenastal, obnoví sa normálny pôvodný beh. Ak už pôvodný čas nastal, z bezpečnostných dôvodov sa znova nespustí a zruší sa iba náhradný odložený beh. Skupinu s aktívnym odkladom nie je možné odstrániť; najprv musíme odklad zrušiť. Vytvorenie a zrušenie odkladu je dostupné iba administrátorovi a je chránené prihlásením a CSRF kontrolou.

## Spustiť teraz
Tlačidlom "Spustiť teraz" spustíme program okamžite bez ohľadu na čas a dátum plánovača.

## Upraviť
Tlačidlo "Upraviť" slúži na upravenie parametrov už vytvoreného programu.

## Kopírovať
Tlačidlo "Kopírovať" vytvorí kópiu vybraného programu. Kópia je v predvolenom stave zakázaná, takže ju môžeme bezpečne upraviť pred použitím v plánovači.

## Presunúť do skupiny
Program je možné priradiť do skupiny na stránke úpravy programu. Tým sa zmení iba jeho umiestnenie na stránke Programy.

## Vymazať všetko
Tlačidlo "Vymazať všetko" odstráni po potvrdení všetky existujúce programy.

## Zapnúť/Vypnúť program
Prepínač "ZAP/VYP" umožňuje vytvorený program povoliť/zakázať v plánovači.

## Upozornenie na kolízie
Pri uložení programu OSPy kontroluje povolené programy a hľadá prekryvy plánovaného behu na rovnakej stanici/výstupe. Ak je v rovnakom čase naplánovaný iný program, stránka Programy zobrazí upozornenie s dobou prekrytia. Ide iba o upozornenie, program sa automaticky nezablokuje ani neupraví.

## Typ plánovača
Typ plánovača umožňuje zvoliť vhodný typ programu podľa našej požiadavky (vybrané dni, opakovania, týždenné, vlastné a programy založené na predpovedi počasia).

### Vybrané dni (Jednoduchý)

#### Čas štartu

#### Trvanie

#### Opakovať

#### Opakovanie

#### Pauza

### Vybrané dni (Rozšírené)

#### Plánovač

### Opakovanie (Jednoduché)

#### Interval zavlažovania

#### Štart v dňoch

#### Čas štartu

#### Trvanie

#### Opakovať

#### Opakovanie

#### Pauza

### Opakovanie (Rozšírené)

#### Interval zavlažovania

#### Štart v dňoch

#### Plánovač

### Týždenný (Rozšírené)

#### Pondelok-Nedeľa

### Vlastné

#### Interval zavlažovania

#### Štart v dňoch

#### Deň 1 - Deň 7

### Týždenný (Predpoveď počasia)

#### Minimálne zavlažovanie

#### Maximálne zavlažovanie

#### Maximálna dávka

#### Pomer pauzy

#### Uprednostnené momenty vykonávania

#### Deň

#### Čas štartu

#### Prednosť

#### Pridať - Zmazať

## Žiadne úpravy
Na tento program nebudú použité žiadne úpravy (napríklad skrátenie, alebo predĺženie doby)

## Odrezať
Pokiaľ by upravená doba behu programu bola kratšia ako táto nastavená doba, tak sa program preskočí (napríklad upravená doba behu z rozšírenia predpovede počasia, alebo mesačná úprava množstva vody a iných rozšírení). Doba sa nastavuje v percentách.

## Aktivovať hlavnú stanicu
Všetky stanice, ktoré majú nastavenú možnosť „Aktivovať Master 1/2 programom“, aktivujú hlavnú stanicu 1/2 podľa tohto priradenia v programe. Oznámenie! pri staniciach, ktoré majú nastavenú možnosť „Aktivovať hlavný 1/2 programom“, nie je možné použiť možnosť ovládania „spustiť jednorazovo“ a „manuálne“. Spustia sa iba stanice, nie hlavné stanice (1 alebo 2)! Toto nastavenie je k dispozícii, iba ak používate obe hlavné stanice!

----

# Spustiť raz

Stránka "Spustiť raz" predstavuje zoznam povolených staníc s poľom minúty a sekundy pre každú z nich. Táto stránka môže byť použitá na testovanie a poskytnutie dodatočného zavlažovania jednorazovo.

## Spustiť teraz
Tlačidlo aktivuje všetky vybrané predvolené stanice.

## Zmazať čas
Tlačidlo odstráni všetky prednastavené časy na všetkých staniciach.

----

# Doplnky

Na stránke "Doplnky" môžeme nakonfigurovať alebo ovládať všetky rozšírenia v systéme OSPy.

## Spravovať

Po kliknutí na tlačidlo "Spravovať" sa otvorí okno správcu rozšírenia v systéme OSPy. Všetky dostupné rozšírenia je možné zapínať, vypínať, inštalovať z repozitára atď...

Doplnok používa súbor `plugin.json` s názvom, verziou, opisom, autorom, domovskou stránkou a licenciou. Správca tieto metadáta zobrazí, ak sú dostupné. Pri už nainštalovaných starších doplnkoch bez manifestu zostáva zachovaná spätná kompatibilita a OSPy načíta ich názov z `__init__.py`; pravidlá pre nové inštalácie sú opísané nižšie.

Manifest môže v zozname `dependencies` deklarovať závislosti od iných doplnkov podľa názvu ich adresára. Povinná závislosť musí byť nainštalovaná a povolená. Voliteľná závislosť doplnok neblokuje, ale ak sú povolené oba doplnky, OSPy najprv spustí poskytovateľa. Pri zastavení sa použije opačné poradie a cyklické závislosti sa nespustia. Pri hromadnej inštalácii možno povinnú závislosť dodať v rovnakom ZIPe; samostatná inštalácia závislého doplnku vyžaduje, aby už bol poskytovateľ nainštalovaný.

Pred zapnutím OSPy kontroluje deklarované verzie OSPy a Pythonu, požadované Python moduly, podporovanú platformu, dostupnosť GPIO/I²C a konflikty s už povolenými doplnkami, GPIO pinmi alebo I²C adresami. Blokujúci problém zabráni zapnutiu a voľba zapnúť všetko taký doplnok preskočí. Správa doplnkov a Diagnostika zobrazujú podrobnosti aj deklarované oprávnenia k sieti, súborom, I²C, GPIO, e-mailu, podprocesom alebo systému. Oprávnenia sú informáciou pre správcu, nie izolovaným systémovým sandboxom.

Od OSPy 3.0.294 musí správca pred prvým spustením novo nainštalovaného doplnku výslovne schváliť oprávnenia uvedené v manifeste. Jednorazová migrácia pri aktualizácii automaticky zachová schválenia všetkých už nainštalovaných doplnkov vrátane vypnutých, takže aktualizácia OSPy nenaruší existujúcu inštaláciu. Nezmenený alebo menší rozsah oprávnení zostáva schválený; pridanie oprávnenia zablokuje ručnú aj automatickú aktualizáciu, kým správca nový rozsah neskontroluje a neschváli. Odobratie schválenia doplnok vypne. Schválenie sa ukladá v OSPy ako rozhodnutie správcu a záznam pre audit; nevytvára systémový sandbox.

Nové doplnky môžu používať spoločnú správu vlákien so stop signálom OSPy. Pri vypnutí doplnku OSPy najprv odošle stop signál, zavolá jeho existujúcu funkciu `stop()` a najviac päť sekúnd čaká na registrované vlákna. Vlákna, ktoré sa nezastavia, sa zobrazia ako chyba v Diagnostike a zabránia spusteniu druhej kópie doplnku. Existujúce doplnky bez tohto rozhrania zostávajú kompatibilné.

Pred importom a spustením prebehne automatický statický test, ktorý nespúšťa kód doplnku ani nepristupuje k hardvéru. Kontroluje adresár, `__init__.py`, syntax a veľkosť Python súborov, voliteľný manifest a pri doplnkoch s manifestom deklarované funkcie `start()` a `stop()`; staršie doplnky bez manifestu si zachovávajú doterajšiu kompatibilitu. Symbolické odkazy nenasleduje. Chyba zabráni aktivácii a podrobnosti sú dostupné v Správe doplnkov a Diagnostike. Kompatibilita, manifest a výsledok testu sa v Správe doplnkov zobrazujú v kontrastných stavových paneloch, ktoré zostávajú čitateľné pri zapnutých aj vypnutých doplnkoch.

## Nainštalovať nový doplnok

Po kliknutí na tlačidlo "Nainštalovať nový doplnok" sa otvorí okno so vzdialeným repozitárom, kde si môžeme vybrať dostupné rozšírenia pre inštaláciu do systému OSPy a prečítať si všeobecné informácie k rozšíreniam.

Pred kopírovaním súborov OSPy bezpečne načíta `plugin.json` priamo zo stiahnutého ZIP archívu a pri každom doplnku zobrazí stav kompatibility aj konkrétne dôvody prípadného problému. Nekompatibilný doplnok nie je možné nainštalovať ani ručne aktualizovať. Doplnok iba s varovaniami možno po ich zobrazení nainštalovať. Hromadná inštalácia nainštaluje kompatibilné doplnky a nekompatibilné preskočí s uvedením dôvodu. Rovnaká kontrola platí pre vlastné ZIP súbory, jednotlivé a hromadné operácie aj aktualizácie. Chýbajúci, neplatný alebo príliš veľký `plugin.json` je pri novej inštalácii chybou; už nainštalované staršie doplnky bez manifestu môžu naďalej fungovať v režime spätnej kompatibility.

### Vlastný doplnok (ZIP)
OSPy overí celý ZIP skôr, než zapíše jediný súbor doplnku. Archív musí obsahovať aspoň jeden adresár doplnku so súborom `__init__.py` a platným UTF-8 súborom `plugin.json`, ktorého `id` zodpovedá názvu adresára. Doplnok môže obsahovať aj Python moduly, `README.md` a adresáre `templates`, `static`, `script`, `docs`, `i18n` a `data`. Archív repozitára môže mať doplnky v adresári `plugins/`; vlastný archív môže obsahovať doplnok priamo v koreňovom adresári.

Zakázané sú absolútne cesty a cesty do nadradeného adresára, neprenosné názvy, duplicitné cesty alebo identifikátory doplnkov, symbolické odkazy, špeciálne či šifrované položky a poškodené archívy. Limity sú 64 MiB stiahnutých ZIP dát, 4 096 položiek archívu, 256 doplnkov, 32 MiB na jeden rozbalený súbor, spolu 128 MiB rozbalených dát a kompresný pomer najviac 200:1. Inštalácia každého doplnku je atomická: súbory sa najprv pripravia, existujúci adresár `data` sa zachová a pri chybe výmeny alebo spustenia sa obnoví predchádzajúca verzia.

Správca rozšírenia umožňuje do systému OSPy nainštalovať aj vlastné rozšírenie, ktoré nie je zverejnené vo vzdialenom repozitári (napríklad vaše nejaké osobné rozšírenie). Pomocou tlačidla "prechádzať" zvolíme požadovaný súbor v našom počítači na inštaláciu do systému OSPy. Súbor rozšírenia (zips) musí obsahovať kompletnú štruktúru rozšírenia (init, templates, i18n, readme atď).

Správca doplnkov predvolene používa stabilný kanál `master`. Správca môže prepnúť na testovací kanál `beta`; zvolený kanál je viditeľný v správe aj pri inštalácii a používa sa pre zoznam, ručné inštalácie, hromadné operácie aj automatické aktualizácie. Testovacie verzie môžu obsahovať chyby. Prepnutie kanála zahodí stiahnutú cache predchádzajúcej vetvy a ďalšia kontrola načíta údaje z novej vetvy. Po otvorení stránky nainštalovaného doplnku sa nad obsahom zobrazí názov a verzia načítaná z `plugin.json`.

### Github (https://github.com/martinpihrt/OSPy-plugins/archive/master.zip)
Na vyššie uvedenom umiestnení sa nachádza repozitár s dostupnými rozšíreniami pre systém OSPy.

Inštalácia alebo aktualizácia rozšírenia spúšťa kód z vybraného zdroja. OSPy pred inštaláciou alebo aktualizáciou zobrazia URL repozitára a požiada o potvrdenie. Akcia Načítať zmeny počas kontaktovania vzdialeného repozitára zobrazí správu o prebiehajúcej kontrole.

## Zakázať všetky
Tlačidlo zakáže všetky nainštalované rozšírenia.

## Povoliť všetky
Tlačidlo povolí všetky nainštalované rozšírenia.

## Povoliť kontrolu aktualizácií
Keď je tlačidlo aktívne, tak sa automaticky po hodine kontroluje vo vzdialenom repozitári dostupnosť novej verzie rozšírenia. Pri dostupnosti novej verzie sa pri rozšírení zobrazí hláška "aktualizovať".

## Načítať zmeny
Tlačidlo načíta najnovší zoznam dostupných zmien zo vzdialeného repozitára rozšírenia.

## Zmeny
Tlačidlo otvorí prehľad dostupných zmien rozšírenia a informácií k aktualizáciám.

## Automatické aktualizácie
Keď je tlačidlo aktívne, pri dostupnosti novej kompatibilnej verzie sa automaticky vykoná aktualizácia rozšírenia. Nekompatibilná nová verzia sa automaticky nenainštaluje a správca zobrazí dôvod. Upozornenie: systém OSPy sa neustále vyvíja a pokiaľ dôjde k zásadnej zmene v systéme OSPy a užívateľ systém OSPy nebude aktualizovať, môže dôjsť k tomu, že rozšírenie po aktualizácii nebude pracovať. Vždy najskôr aktualizujte systém OSPy a následne všetky rozšírenia!

----

# Denník
Pomocou stránky "Denník" môžeme zobraziť všetky protokoly zaznamenané v systéme OSPy. Počet záznamov sa nastavuje na stránke "Nastavenia".

## Denník udalostí
Denník udalostí je prevádzková a auditná história oddelená od denníka behov staníc aj od technického debug denníka. Zaznamenáva zásahy do zavlažovania a zablokované behy, zmeny konfigurácie, udalosti používateľov a zabezpečenia, operácie systému a rozšírení a udalosti alebo stavy senzorov. Každý záznam obsahuje dátum, čas, úroveň, kategóriu, predmet a podrobnosti. Úroveň je rozlíšená aj farbou: informácia modrou, úspech zelenou, varovanie oranžovou, chyba červenou a kritická udalosť tmavočervenou. Pomocou zoznamu **Kategória udalostí** možno zobraziť všetky udalosti alebo jednu kategóriu. Export `events.csv` obsahuje stĺpce Date, Time, Level, Category, Subject a Status. Existujúce debug protokolovanie ani jeho súbor `events.log` nie sú týmito ovládacími prvkami ovplyvnené.

Do toho istého auditného denníka sa ukladajú aj operácie meniace stav vykonané cez overené API, napríklad ovládanie staníc a programov, zmeny konfigurácie, vymazanie denníka a systémové operácie. Neúspešná autentifikácia API a dočasné zablokovanie brute-force pokusov sa zobrazujú v kategórii **Používatelia a zabezpečenie**. Bežné čítanie z API ani každé úspešné Basic overenie sa nezaznamenáva, aby častá API prevádzka nezaplnila denník.

## Stiahnuť denník udalostí ako
Odkaz "Stiahnuť záznam ako Excel log.csv" umožní uložiť do počítača záznam o behu zavlažovania ako súbor csv (program Excel).
* Štruktúra tabuľky je: Date, Štart Time, Zone, Duration, Program. Dáta sú oddelené čiarkou.
* Príklad: 2019-08-12 05:00:00 Filtrácia 60:00 Filtrácia

Odkaz "Stiahnuť záznam ako Excel log email.csv." umožní uložiť do počítača záznam o odoslaných emailoch ako súbor csv (program Excel).
* Štruktúra tabuľky je: Date, Time, Subject, Body, Status. Dáta sú oddelené čiarkou.
* Príklad: 2019-08-12 06:00:04 Odoslané CHATA SYSTÉM Ukončené zalievanie-> Program: Filtrácia , Stanica: Filtrácia , Začiatok: 2019-08-12 05:00:00 , Trvanie: 60 170 cm (90 %), Ping: 95 cm, Volume: 1.28 m3 , Temperature DS1-DS6-> SKLEP: 21.1 ℃ ČERPADLO: 33.5 ℃ BOJLER: 26.6 ℃ VNÚTRI: 22.1 ℃ ŠTUDNA: 12.

## Vymazať denník
Po stlačení tlačidla "Vymazať denník" dôjde k vymazaniu všetkých záznamov o behu zavlažovania. Akcia je nevratná.

## Zmazať záznam Email
Po stlačení tlačidla "Zmazať záznam Email" dôjde k vymazaniu všetkých záznamov o odoslaných emailoch zo systému. Akcia je nevratná.

----

# Nastavenia
Na stránke "Nastavenia" môžeme upravovať nastavenie celého OSPy systému.
Stránka obsahuje niekoľko skladacích oddielov. Kliknutím na pruh otvoríme alebo zatvoríme požadovanú časť.

### Zobraziť tipy

* Kliknutím na tlačidlo "Zobraziť pomocníka" zobrazíme, alebo skryjeme informácie o každej možnosti.

### Názov systému
Pomenovanie systému je užitočné pri práci s niekoľkými OSPy systémami.

* Zadajte jedinečný popisný názov systému.
* Kliknutím na tlačidlo "Potvrdiť zmeny" v spodnej časti stránky uložte zmeny.

Názov systému je v predvolenom stave "OpenSprinkler Pi" a bude zobrazený v záhlaví každej stránky pre jednoduchú identifikáciu systému.

### Šablóna webu
Určuje vzhľad GUI. V zozname je k dispozícii niekoľko tém (zelený režim, čiernobiely režim...)

### 24-hodinový čas
Voľba 24-hodinový čas vyberá medzi medzinárodným formátom 24 hodín, niekedy označovaným ako vojenský čas, a formátom 12 hodín-AM/PM.

* Zrušte začiarknutie políčka a vyberte 12 hodinový formát AM/PM.
* Kliknutím na tlačidlo "Potvrdiť zmeny" v spodnej časti stránky uložte zmeny.

Budete presmerovaní na domovskú stránku a hodiny budú vo vybranom formáte.

### HTTP IP adresa
IP adresa pre HTTP/S server. IPv4 alebo IPv6 adresa (prejaví sa až po reštarte.) Predvolená je 0.0.0.0.

#### O čísle portu
Číslo portu HTTP/S je súčasťou webovej adresy.
Port 80 je predvolené číslo pre webové stránky a ako také nemusí byť zahrnuté, keď je adresa URL zadaná do adresného riadku prehliadača. Veľa webových serverov štandardne používa port 80.
Ak prevádzkujete iný server na rovnakom Raspberry Pi ako OSPy a používate rovnaké číslo portu, dôjde ku konfliktu a OSPy sa nemusia spustiť.
Konfliktu sa môžete vyhnúť zmenou čísla portu OSPy na stránke Možnosti na niečo iné napríklad 8080. Ak zmeníte číslo portu, ktoré OSPy používa, budete musieť zahrnúť toto číslo, ktorému predchádza dvojbodka, do adresy URL pre webové rozhranie OSPy. Napríklad:
[URL Raspberry pi]: 8080

### HTTP/S port
Číslo portu HTTP/S je súčasťou webovej adresy. Port 80 je predvolené číslo pre webové stránky.

* Kliknite do textového poľa vedľa možnosti HTTP/ S port.
* Zadajte číslo portu, ktorý chcete použiť, napr. 8080.
* Kliknite na tlačidlo "Potvrdiť zmeny" v spodnej časti stránky.

Vrátite sa na domovskú stránku. Systém sa reštartuje, ale vo webovom rozhraní nie je viditeľná indikácia reštartu. Počkajte aspoň 60 sekúnd, potom pridajte nové číslo portu do adresy URL Pi, pred ktorým je dvojbodka (:), a skúste sa znova pripojiť k OSPy.

### Zobraziť doplnky na hlavnej stránke
Pokiaľ chceme na úvodnej (domácej stránke) zobrazovať pod grafom namerané dáta z rozšírenia (vietor, teplota, hladina...) zaškrtneme políčko. V prípade, že nechceme zobrazovať dáta z rozšírenia zrušíme začiarknutie.
* Upozornenie: aby sa dáta zobrazovali v poriadku je nevyhnutné mať rozšírenie povolené a správne nastavené.

Doplnok môže pomocou `showOnTimeline` priradiť živú hodnotu ku konkrétnej stanici. OSPy ju každé tri sekundy obnovuje vedľa stavu práve bežiacej stanice vrátane hlavných staníc a ručného režimu. Po zastavení stanice alebo vyprázdnení hodnoty údaj zmizne; zobrazenie nemení riadenie výstupov ani plánovanie.

### Zobraziť senzory na hlavnej stránke
Pokiaľ chceme na úvodnej (domácej stránke) zobrazovať pod grafom namerané dáta zo snímačov zaškrtneme políčko. V prípade, že nechceme zobrazovať dáta zo snímačov zrušíme začiarknutie.
* Upozornenie: aby sa dáta zobrazovali v poriadku je nevyhnutné mať snímače povolené a správne nastavené.

### Jazyk systému
Voľbou jazyka môžeme zmeniť jazyk používaný vo webovom rozhraní.

* Kliknutím na šípku nadol napravo od poľa jazyka zobrazíte zoznam dostupných jazykov.
* Kliknite na jazyk, ktorý chcete použiť v rozhraní.
* Kliknite na tlačidlo "Potvrdiť zmeny" v spodnej časti stránky.

Software sa reštartuje a po niekoľkých sekundách sa rozhranie zobrazí vo zvolenom jazyku.

### Zobrazenie obrázkov na staniciach
Zaškrtnutím tohto políčka zobrazíte obrázky staníc na domovskej stránke a na stránke staníc.

## Počasie
Sekcia počasia poskytuje spoločné údaje predpovede pre OSPy aj rozšírenia, ktoré upravujú zavlažovanie. Všetci odberatelia používajú poskytovateľa vybraného v Nastaveniach, takže ho netreba nastavovať osobitne v každom rozšírení.

### Použiť počasie
Povolí alebo zakáže načítanie počasia od vybraného poskytovateľa.

### Poskytovateľ počasia
**Open-Meteo – automatický model** vyberie vhodný dostupný model bez API kľúča. **ČHMÚ ALADIN cez Open-Meteo** vynúti model ALADIN tam, kde je dostupný. **Stormglass** zachováva pôvodnú službu a vyžaduje vlastný API kľúč. Open-Meteo je určené na nekomerčné použitie podľa podmienok služby a OSPy uvádza zdroj pri predpovedi.

Po aktualizácii staršej inštalácie zostane pri uloženom kľúči vybraný Stormglass. Inštalácia bez kľúča prejde na Open-Meteo. Pri dočasnom výpadku služby zostanú zobrazené posledné platné údaje; OSPy sa bez vedomia používateľa neprepne k inému poskytovateľovi.

### Storm Glass API kľúč
Je potrebný iba pri výbere poskytovateľa Stormglass.

### Poloha
Názov mesta alebo PSČ. OpenStreetMap podľa neho určí polohu pre vybraného poskytovateľa počasia.

Tlačidlom **Vybrať na mape** otvoríte mapu vhodnú aj na dotykové ovládanie, kliknete na presný bod počasia a výber potvrdíte. **Použiť polohu zariadenia** môže po súhlase používateľa umiestniť značku podľa prehliadača. Po uložení Nastavení sú zemepisná šírka a dĺžka rozhodujúcou polohou počasia; ručná zmena poľa Poloha prepne späť na vyhľadanie názvu cez OpenStreetMap. Pod stavom súradníc domovská stránka zobrazí tri karty predpovede pre aktuálny čas, približne +3 a +6 hodín s miestnymi ikonami, teplotou a zrážkami. Podrobnosti uvádzajú zdroj údajov a čas aktualizácie.

## Užívatelia
Pre zvýšenie bezpečnosti odporúčame zmeniť systémové heslo pre OSPy a užívateľské meno z východiskového "admin". V prípade potreby môžete tiež požiadavku na heslo deaktivovať.

* Kliknutím na trojuholník naľavo od lišty s popisom "Užívatelia" rozbaľte sekciu.
* Označte zaškrtnutím políčko "Bez hesla", ak máte veľmi dobrý dôvod na deaktiváciu ochrany heslom a menom. Systém už nebude vyžadovať prihlásenie používateľa. Bude umožnený prístup do všetkých sekcií.
* Zadajte Vaše užívateľské meno.
* Zadajte Vaše aktuálne heslo.
* Zadajte nové heslo do polí označených "Nové heslo" a "Potvrďte heslo".
* Kliknite na tlačidlo "Potvrdiť zmeny" v spodnej časti stránky.

Vrátite sa na domovskú stránku. Vaše nové heslo s meno bude vyžadované pri ďalšom prihlásení.

### Zakázať zabezpečenie
Ak je zaškrtnuté políčko "Zakázať zabezpečenie" povolíme prístup do systému anonymným užívateľom bez hesla.

### Používateľské meno
Do textového poľa zadajte užívateľské meno. To je pri novej inštalácii "admin".

### Aktuálne heslo
Do textového poľa zadajte aktuálne heslo.

### Nové heslo
Zadajte nové heslo do poľa označeného "Nové heslo".

### Potvrďte heslo
Do poľa označeného "Potvrďte heslo" zadajte rovnaké nové heslo ako v poli "Nové heslo".

### Ďalši užívateľia
Po kliknutí na tlačidlo sa otvorí stránka, kde môžeme vytvárať a prípadne upravovať nových užívateľov pre prístup do systému.

## Zabezpečenie

### Ochrana formulárov
Akcie, ktoré menia nastavenia alebo stav systému, sú vo webovom rozhraní chránené tokenom formulára. Ak je stránka otvorená dlho alebo vyprší relácia v prehliadači, načítajte stránku znova a akciu zopakujte.

### Použíť HTTPS
V prípade, že sme nakonfigurovali server OSPy pre vyššie zabezpečenie prenosu dát pomocou certifikátu SSL, zaškrtnite políčko "Použíť HTTPS". Ak je zaškrtnutá voľba "Použíť HTTPS" a server nie je správne nastavený, OSPy sa spustia ako http server bez zabezpečenia.

Serverová časť je teraz jednoznačná: vlastný certifikát má prioritu, inak sa použije Let’s Encrypt; zapnutie oboch volieb už nespôsobí tichý návrat na HTTP.

### Doménové meno
Certifikát je umiestnený v systéme v adresári '/etc/letsencrypt/live/' meno domény '/fullchain.pem' a '/etc/letsencrypt/live/' meno domény '/privkey.pem'. Certifikát je nutné pomocou nástroja "Certbot" nainštalovať do systému (Linux) ručne (použitie https sa prejaví v OSPy až po reštarte OSPy).
* Postup pre inštaláciu Certifikačnej služby nájdeme v súbore "Readme" pomocníka, alebo na Githube.

### Použiť HTTPS pomocou Certbot
SSL certifikát pomocou Let’s Encrypt certifikačnej autority.
Certbot (https://certbot.eff.org/) a Let's Encrypt (https://letsencrypt.org/).

```bash
sudo apt-get install certbot
```

```bash
certbot --version
```

```bash
sudo certbot certonly --standalone -d your_domain_name
```

```bash
sudo certbot renew
```

```bash
sudo cp /etc/letsencrypt/live/your.domain.com/fullchain.pem /home/pi/OSPy/ssl
```

```bash
sudo cp /etc/letsencrypt/live/your.domain.com/privkey.pem /home/pi/OSPy/ssl
```

```bash
sudo service ospy restart
```

### Používanie vlastného prístupu HTTPS
Ak je v nastavení OSPy vybraná možnosť „Použiť vlastný prístup HTTPS“, musíte do adresára ssl v umiestnení OSPy vložiť súbor: fullchain.pem a privkey.pem. Varovanie: OSPy musia byť znovu reštartované.
```bash
sudo openssl req -new -newkey rsa:4096 -x509 -sha256 -days 3650 -nodes -out fullchain.pem -keyout privkey.pem
```
Druhý spôsob je pomocou tlačidla "generovať" v záložke SSL certifikát.

### API CORS povolený origin
Táto voľba nastavuje hlavičku `Access-Control-Allow-Origin`, ktorú API používa pre klientov spustených v prehliadači. Hodnota `*` povolí ľubovoľný origin, je možné zadať jeden origin napríklad `https://example.com`, viac originov oddelených čiarkou, alebo ponechať pole prázdne a CORS hlavičky sa nebudú posielať. Nenahrádza to overenie API; iba to určuje, ktoré webové originy smú čítať odpovede API.

### Povoliť API JSONP
Táto voľba povoľuje starší parameter `callback` pre JSONP odpovede API. Nechajte ju vypnutú, pokiaľ ju nevyžaduje stará integrácia. Bežné API klienti majú používať JSON s CORS.

### Zapamätané prihlásenia v prehliadači
Prihlasovacia stránka môže zapamätať prehliadač pomocou dlhodobého náhodného tokenu uloženého v zabezpečenej cookie. OSPy ukladá iba hash tohto tokenu, nie heslo používateľa. Tlačidlom Zrušiť odstránite všetky zapamätané prihlásenia v prehliadačoch; dotknuté prehliadače sa musia znovu prihlásiť heslom.

## Senzory
Sekcia snímača obsahuje nastavenia pre zabezpečenie snímačov.

### Heslo pre nahrávanie firmvéru
Heslo pre nahrávanie firmvéru z OSPy do senzoru (pre všeky použité senzory - rovnaké heslo musí byť použité aj v nastavení senzora). Predvolené heslo je: "fg4s5b.s,trr7sw8sgyvrDfg".

## Konfigurácia staníc
Sekcia "Konfigurácia staníc" obsahuje všeobecné nastavenia, ktoré ovplyvňujú plánovanie a kombinovanie staníc.

### Vytaženie
Určuje, ako sa môžu behy staníc prekrývať. `0` znamená bez obmedzenia využitia, takže stanice môžu bežať súčasne, pokiaľ sa ich programy časovo prekrývajú. `1` znamená vždy jednu stanicu naraz, pokiaľ má každá stanica využitie `1`. Vyššia hodnota dovolí súbeh viacerých staníc, pokiaľ ich súčet využitia neprekročí nastavený limit.

Toto nastavenie tiež ovplyvňuje, kedy sa vloží pauza medzi stanicami.

#### O sekvenčných a súbežných režimoch
* Sekvenčný režim sa používa hlavne vtedy, keď zdroj vody nezvládne napájať viac vetiev naraz. Príklad: pri Maximálnom využití `1` a využití stanice `1` musí stanica 3 skončiť skôr, ako môže začať stanica 4.
* Súbežný režim sa používa vtedy, keď zdroj vody zvládne viac vetiev naraz. Príklad: pri Maximálnom využití `0` môžu stanice 2, 3 a 4 bežať súčasne, pokiaľ sa ich programy prekrývajú.

### Počet výstupov
Celkový počet dostupných výstupov je 8 výstupov plus výstupy z rozširujúcich dosiek. Počet výstupov je možné nastaviť vyšší, než je skutočný počet fyzických výstupov, a tým vytvoriť virtuálne výstupy.

### Pauza medzi stanicami
Pauza vložená medzi postupne spúšťané stanice, keď ich plánovač nemôže spustiť súčasne, v sekundách medzi 0 a 3600. Toto neposúva stanicu voči hlavnej stanici.

Príklad: pri Maximálnom využití `1` a využití stanice `1` hodnota `30` spustí ďalšiu stanicu 30 sekúnd po skončení predchádzajúcej stanice.

### Minimálna doba prevádzky
Preskočí pauzu medzi stanicami, ak bol predchádzajúci beh kratší ako táto hodnota, v sekundách medzi 0 a 86400.

Príklad: pri pauze `30` a minimálnej dobe behu `10` stanica, ktorá bežala iba 5 sekúnd, nevynúti 30sekundovú pauzu.

## Nastavenie hlavnej stanice
Sekcia "Nastavenie hlavnej stanice" vyberá hlavnú stanicu 1, hlavnú stanicu 2 a časové posuny používané pri aktivácii hlavnej stanice. Hlavná stanica je obvykle čerpadlo alebo hlavný ventil prívodu vody.

Hlavná stanica sa použije iba pri staniciach, ktoré ju majú nastavenú na stránke Stanice, prípadne pri programoch, ktoré vyberajú hlavnú stanicu 1 alebo 2 pre stanice nastavené na „Aktivovať Master 1/2 programom“.

### Hlavná stanica
Výber prvej hlavnej stanice, napríklad čerpadla alebo hlavného ventilu.

### Druhá hlavná stanica
Výber druhej hlavnej stanice, napríklad druhého čerpadla alebo iného zdroja vody.

### Aktivovať relé
Ak je začiarknuté, relé bude tiež aktivované ako hlavný výstup.

### Posun štartu hlavnej stanice
Časový posun zapnutia hlavnej stanice 1 voči štartu stanice, v sekundách medzi -1800 a +1800. Záporné hodnoty spustia hlavnú stanicu skôr, kladné hodnoty neskôr.

Príklad: `-10` spustí hlavnú stanicu 10 sekúnd pred stanicou. `+10` ju spustí 10 sekúnd po stanici.

### Posun vypnutia hlavnej stanice
Časový posun vypnutia hlavnej stanice 1 voči koncu stanice, v sekundách medzi -1800 a +1800. Záporné hodnoty vypnú hlavnú stanicu skôr, kladné hodnoty ju nechajú bežať dlhšie.

Príklad: `-5` vypne hlavnú stanicu 5 sekúnd pred koncom stanice. `+20` ju vypne 20 sekúnd po konci stanice.

### Posun štartu hlavnej stanice 2
Časový posun zapnutia hlavnej stanice 2 voči štartu stanice. Funguje rovnako ako posun štartu hlavnej stanice, ale len pre hlavnú stanicu 2.

### Posun vypnutia hlavnej stanice 2
Časový posun vypnutia hlavnej stanice 2 voči koncu stanice. Funguje rovnako ako posun vypnutia hlavnej stanice, ale len pre hlavnú stanicu 2.

## Dažďový senzor
Nastaví typ spínača dažďového senzora. Pokiaľ používate Raspberry Pi a chcete pripojiť senzor dažďa priamo k pinom GPIO, použite piny 8 a 6 (gnd).

### Používať senzor
Zaškrtnutím políčka "Používať senzor" povolíme snímanie dažďa.

### Normálne otvorený
Začiarknite políčko "Normálne otvorený", ak je senzor bez dažďa normálne rozpojený, inak políčko zrušte. Informácie o type spínača nájdete v používateľskej príručke dažďového senzora.

### Nastaviť dažďové oneskorenie
Keď je aktivovaný dažďový snímač, nastaví sa oneskorenie dažďa (to je vhodné napríklad pre blokovanie programov na dlhšiu dobu, než poskytuje dažďový snímač).

### Dážďové oneskorenie
Doba dažďového oneskorenie (v hodinách), medzi 0 a 500.

## Zaznamenávanie udalostí
Zapnite protokolovanie behu a nastavte počet záznamov, ktoré chcete zachovať. Zapnite protokolovanie odoslaných e-mailov a nastavte počet záznamov, ktoré chcete uchovávať.

### Povoliť záznam udalostí
Začiarknite políčko "Povoliť záznam udalostí". Tým sa zapne protokolovanie a zapne sa história zavlažovania na časovej osi na domovskej stránke. Zaznamenávať všetky behy staníc - berte na vedomie, že opakujúce sa písanie na SD kartu môže skrátiť jej životnosť.

### Max položiek
Zadajte počet záznamov, ktoré chcete uložiť do protokolu. Nastavte počet, ktorý pokryje primeranú dobu, napríklad týždeň alebo mesiac. To bude závisieť od počtu programov a staníc, ktoré máte. Pri každom spustení stanice bude existovať jeden záznam. 0 = bez obmedzenia.

### Povoliť zasielanie udalostí e-mailom
Začiarknite políčko "Povoliť zasielanie udalostí e-mailom". Tým sa zapne protokolovanie a povolí sa história zavlažovania prostredníctvom E-mailu.

### Max položiek
Zadajte počet záznamov, ktoré chcete uložiť do protokolu. Nastavte počet, ktorý pokryje primeranú dobu, napríklad týždeň alebo mesiac. To bude závisieť od počtu programov a staníc, ktoré máte. Pre každý E-mail bude existovať jeden záznam. 0 = bez obmedzenia.

### Povoliť protokol udalostí
Povoliť protokol udalostí (dažďový senzor, oneskorenie dažďa, server, internetová externá IP ...)

### Max položiek
Počet záznamov udalostí na uloženie na disk, 0 = bez obmedzenia.

### Povoliť protokol ladenia
Kliknutím na "Povoliť protokol ladenia" uložíte všetky interné operácie v OSPy do súboru pre lepšie ladenie. * Poznámka: * príliš časté ukladanie dát do súboru môže po dlhšej dobe poškodiť SD kartu alebo znížiť kapacitu SD karty (úložisko). Vypisujú sa všetky operácie (aj zo všetkých rozšírení).

## Reštartovať systém
Sekcia "Reštart systému" obsahuje tlačidlá pre reštartovanie softvéru, pre reštartovanie hardvéru, pre vypnutie hardvéru a vymazanie všetkých nastavení na predvolené hodnoty.

### Reštart OSPy
Tlačidlo "Reštart OSPy" reštartuje iba softvér. Je to rýchly vynútený spôsob, ako implementovať zmeny v softvéri.

### Reštart HW
Tlačidlo "Reštart HW" reštartuje Raspberry Pi. To trvá dlhšie, ale vykoná úplný reštart systému.

### Vypnúť
Tlačidlo "Vypnúť" vypína napájanie Raspberry Pri hardvéri.

### Predvolené nastavenia
Tlačidlo "Predvolené nastavenia" vymaže všetky užívateľské nastavenia do východiskovej čistej inštalácie OSPy.
* Všetky nastavenia sa dajú v OSPy zmazať aj ručne (v systéme nájdeme zložky ospy/data av zložke zmažeme všetky súbory).

## Záloha a obnovenie
Ak chceme zálohovať všetky nastavenia nášho OSPy zavlažovacieho systému alebo preniesť nastavenia do iného OSPy systému, použijeme tlačidlo "Stiahnuť" a následne "Nahrať".

### Stiahnuť
Tlačidlo "Stiahnuť" sa používa na stiahnutie konfiguračného súboru do počítača pre neskoršie použitie alebo na obnovenie systému OSPy. Uloží sa nielen súbor databázy (options.db), ale aj priečinok staníc, kde sú uložené obrázky staníc. Súčasne sa uloží súbor denníka events.log (ak existuje). Všetko je uložené v súbore zip (príklad: ospy_backup_systemname_4.12.2020_18-40-20.zip). Môžeme ľahko identifikovať, z ktorého systému OSPy záloha pochádza. Zložka SSL, kde je certifikát, nie je z bezpečnostných dôvodov uložená do záložného súboru zips!

### Nahrať
Tlačidlo Nahrať vám umožní vložiť a obnoviť systém OSPy (napríklad pri opätovnej inštalácii systému Linux). Nahraný súbor musí byť súbor zips! Nasledujúce cesty a súbory musia byť v súbore.

```bash
*.zip folder:
ospy-backup.json
ospy/data/default/options.db.*
ospy/data/backup/options.db.*
ospy/data/events.log
ospy/images/stations/station1.png
ospy/images/stations/station1_thumbnail.png
```
Alebo iné obrázky staníc v rovnakom formáte.

Nové zálohy obsahujú súbor `ospy-backup.json`, v ktorom je uvedený formát zálohy, verzia OSPy, čas vytvorenia a veľkosť aj kontrolný súčet SHA-256 každého súboru. Archív obsahuje databázu nastavení OSPy, údaje systémového záznamu a obrázky staníc. Súkromné kľúče SSL, kód pluginov a vyrovnávacia pamäť Pythonu sú zámerne vynechané; dátové adresáre pluginov naďalej zálohuje samostatný plugin OSPy package Backup. Pred obnovou OSPy odmietne nebezpečné cesty v ZIPe, odkazy, šifrované alebo duplicitné položky, nadmernú veľkosť či kompresiu a každý súbor mimo `ospy/data/` a `ospy/images/stations/`. Limit je 50 000 položiek a 512 MB po rozbalení; súbor väčší ako 1 MB nesmie prekročiť kompresný pomer 200:1 a nastavený limit nahrávania môže byť nižší. Každý súbor sa overí podľa manifestu a rozbalí do prípravného adresára. OSPy potom automaticky vytvorí bezpečnostnú zálohu súčasného stavu, atomicky vymení údaje a reštartuje sa. Staršie zálohy OSPy bez manifestu zostávajú podporované ako pôvodný formát iba s údajmi a prechádzajú rovnakou kontrolou ciest a veľkosti ZIPu.

Formát zálohy 2 zapisuje hlavné úložisko nastavení, režim ukladania a schému SQLite. Pred archiváciou živých nastavení OSPy uloží čakajúce zmeny a zablokuje súbežné zápisy nastavení. Databázu SQLite skopíruje transakčne pomocou SQLite Backup API a snímku nezávisle overí kontrolou integrity, schémy, manifestu záznamov a kontrolných súčtov hodnôt. Obnova túto logickú kontrolu po rozbalení zopakuje a odmietne snímku, ktorej deklarovaný režim, schéma alebo počet nastavení nesúhlasí. Zálohy s manifestom formátu 1 aj staršie zálohy bez manifestu zostávajú obnoviteľné.
Aktívne webové relácie sa nezálohujú ani neobnovujú; po obnovení je potrebné sa znova prihlásiť.
OSPy uchováva v zariadení desať najnovších bezpečnostných systémových záloh. Ich zoznam je v Možnostiach, odkiaľ možno vybraný archív stiahnuť a potom obnoviť pomocou tlačidla Nahrať.
Systémová záloha obsahuje prihlasovacie a bezpečnostné nastavenia, preto musia byť stiahnuté archívy bezpečne uložené.

## Certifikát SSL
Pokiaľ máme svoj vlastný certifikát pre SSL (https) zabezpečenie (fullchain.pem a privkey.pem) môžeme ho tu pomocou formulára nahrať.

## Generovať
Ak chceme vygenerovať SSL certifikát, stlačíme tlačidlo "generovať". Do adresára ssl sa vygeneruje certifikát. Následne v nastavení/bezpečnosť zaškrtneme možnosť "vlastnej HTTPS" a následne reštartujeme OSPy.

### Nahrať
Tlačidlo "Nahrať" odošle do priečinka ssl v adresári OSPy priložené súbory (fullchain.pem a privkey.pem).

----

# Stanica
Na stránke "Stanica" nastavujeme nazvy staníc, vlastnosti okolo využívania množstva vody, ovládanie hlavných staníc.

## Stanica
Automatické číslovanie na označenie staníc. Napríklad 1 = stanica 1, 2 = stanica 2...

## Názov
Užívateľské pomenovanie staníc pre lepšiu identifikáciu v systéme, napríklad "trávnik".

## Využitie
Nastavenie súbehu (0), alebo sekvencie (>=1) pre určité stanice. Viac o súbehu, alebo sekvencii v texte vyššie v sekcii "Nastavenia/O sekvenčných a súbežných režimoch".

## Závlaha
Množstvo vody za hodinu v mm, ktoré rozpráši rozstrekovače na danej stanici. Používa sa pre programy založené na počasí. Pre zmeranie tejto hodnoty je vhodné si zaobstarať napríklad plastový zrážkomer.

* Vzťahuje sa na čas potrebný na infiltráciu daného množstva vody do konkrétneho typu pôdy. Vo všeobecnosti je rýchlosť príjmu ľahšej textúrovanej (piesočnatej) pôdy vyššia ako rýchlosť ťažšej textúrovanej (ílovitej) pôdy. Zavlažovanie postrekovačov veľkým množstvom vody však môže viesť k povrchovému odtoku aj na piesočnatých pôdach. Rýchlosť príjmu pôdy pod zavlažovaním je ovplyvnená mnohými faktormi, ako je štruktúra pôdy, štruktúra pôdy, zhutnenie, organická hmota, stratifikované pôdy, soli v pôde, kvalita vody, sedimenty v zavlažovacej vode atď.

## Zásoba
Množstvo vody, ktoré môže pôda uložiť nad úroveň 0. Používa sa pre programy založené na počasí.

* Vzťahuje sa na množstvo pôdnej vlhkosti alebo obsahu vody zadržanej v pôde po odtoku prebytočnej vody a zníženie rýchlosti pohybu dole. K tomu obvykle dochádza 2–3 dni po daždi alebo zavlažovaní v predchádzajúcich pôdach s jednotnou štruktúrou a štruktúrou.

## ETo faktor
Faktor použitý na násobenie faktora ETo pre programy založené na počasí. Použite hodnotu nad 1 v prípade slnečnej/suchej pôdy, použite hodnotu nižšiu ako 1 pre tieň/mokrú pôdu.

* Typ pôdy

Pôdy majú rôzne vlastnosti, vďaka ktorým sú jedinečné. Poznať druh pôdy, ktorú máte, vám pomôže určiť jej silné a slabé stránky. Zatiaľ čo pôda sa skladá z mnohých prvkov, miesto, kde začať, je s vašim typom pôdy. Musíte iba sledovať zloženie pôdnych častíc. OSPy umožňuje používateľom určiť typ pôdy pre každú zónu (stanicu), čo umožňuje presnejšie a efektívnejšie výpočty zalievanie. Rôzne typy pôdy reagujú odlišne na vodu; ílovité pôdy majú sklon k odtoku, zatiaľ čo hlinité pôdy môžu zadržiavať vodu po dlhú dobu atď. Množstvo vody obsiahnutej v pôde po odtoku prebytočnej vody a schopnosť pôdy zadržiavať vodu sa označuje ako kapacita poľa (merané v palcoch alebo milimetroch).

### Test pomocou fľaše
Ako nájsť približné proporcie piesku, bahna a ílu? Toto je jednoduchý test, ktorý vám dá všeobecnú predstavu o podieloch piesku, bahna a ílu prítomného v pôde. Vložte 5 cm pôdy do fľaše a naplňte ju vodou.
Vodu a pôdu dobre premiešajte, odložte fľašu a nedotýkajte sa jej hodinu. Po hodine sa voda vyčerí a uvidíte, že sa väčšie častice usadili:

- Na hladine vody sa môžu vznášať kúsky organickej hmoty
- Hore je vrstva hliny.
Ak voda stále nie je číra, je to preto, že niektoré z najjemnejších ílov sú stále zmiešané s vodou
- Uprostred je vrstva bahna
- V spodnej časti je vrstva piesku

* Zmerajte hĺbku piesku, bahna a ílu a odhadnite ich približný pomer.

Nasledujúce tri typy častíc môžu tvoriť vašu pôdu: íl, piesok a bahno. Väčšina pôd je kombináciou týchto troch častíc, ale typ častíc, ktorý dominuje, diktuje mnoho vlastností vašej pôdy. Pomer týchto veľkostí určuje typ pôdy: íl, hlina, ílovitá hlina, bahno-hlina atď.

* Ideálna pôda je 40% piesku, 40% bahna a 20% ílu. Táto zmes sa označuje ako hlinitá. To berie to najlepšie z každého typu častíc pôdy. Má dobrú drenáž vody a umožňuje vzduchu preniknúť do pôdy ako piesok, ale tiež dobre udržuje vlhkosť a je úrodná ako bahno a hlina.

## Zostatok
Zvýšenie alebo zníženie vodnej bilancie pre programy založené na počasí (pokiaľ nie je nastavené na 0).

## Pripojené
Ak máme stanicu zapojenú (je fyzicky pripojená) a chceme ju využívať (je vidieť vo výbere v programoch, na domovskej stránke...), zaškrtneme "Pripojené". Pokiaľ stanicu nevyužívame a nechceme zverejniť v systéme OSPy ponecháme "Pripojené" nezaškrtnuté. Pokiaľ je v systéme použitá niektorá stanica ako "hlavná stanica" alebo "2 hlavné stanice", tak ju v tabuľke nie je možné zaškrtnúť ani odškrtnúť (deaktivovať).
Hlavná stanica sa priraďuje v nastavení systému "Nastavenie / nastavenie hlavnej stanice".

## Ignorovať Dážď
Pokiaľ pri niektorej stanici zaškrtneme "Ignorovať Dážď", tak sa stanica aktivuje podľa programu bez ohľadu či je nastavené dažďové oneskorenie, alebo či dažďový senzor detekuje dážď. Túto možnosť využijeme napríklad v skleníku, do ktorého neprší a potrebujeme zavlažovať pravidelne. alebo napríklad na spúšťanie filtrácie bazéna, ktorý tiež čistíme bez ohľadu či prší.

## ZAP Hlavné?
### Nepoužité
Nebude použitá žiadna hlavná stanica (ak je určitá stanica aktivovaná, hlavná stanica nebude aktivovaná).
### ZAP Hlavné
Ak požadujeme, aby keď sa aktivuje určitá stanica sa aktivovala aj hlavná stanica (napríklad čerpadlo, alebo hlavný ventil s vodou) vyberieme položku "ZAP hlavná?".
### ZAP Hlavné 2
Ak požadujeme, aby keď sa aktivuje určitá stanica sa aktivovala aj druhá hlavná stanica (napríklad druhé čerpadlo, alebo iný zdroj vody) vyberieme položku "ZAP hlavné 2?".
### ZAP Hlavný 1/2 programom
Ak požadujeme aktivovať hlavnú stanicu alebo druhú hlavnú stanicu programom vyberieme položku „Spustiť hlavnú stanicu 1/2 cez program“. Pri programe je potom možné zvoliť, ktorá hlavná stanica sa má pre túto stanicu použiť (príklad: program 1 riadi stanice 1-4 a hlavnú stanicu 5. Program 2 riadi stanice 1-4 a druhú hlavnú stanicu 6).

## Poznámky
Poznámky slúžia na obsluhu systému OSPy. Možno si napríklad poznamenať: aký typ el. ventilu, rozstrekovače atď. máme v systéme použitý.

## Obrázok
Po kliknutí na okienko sa otvorí stránka, na ktorej je možné nahrať vlastný obrázok k stanici.

----

# Senzory
Na stránke „Senzory“ môžeme pridávať alebo mazať snímače, ktoré v systéme OSPy plnia rôzne funkcie. V systéme OSPy je možné aktuálne používať snímače od výrobcu pihrt.com a shelly.com.

## Pridať nový snímač (od Pihrt.com)
Tlačidlo „Pridať nový senzor“ pridá do systému nový snímač. Nastavenie snímačov je uvedené nižšie v časti „Parametre snímačov“.

## Parametre snímačov
Pre snímače sa používajú dva druhy komunikácie:
* Bezdrôtová (rádio) - ID rádio snímača
* Sieťová (Wi-Fi/LAN) - MAC adresa, IP adresa
Možno si vybrať z rôznych typov snímačov:
* Kontakt
* Detektor úniku
* Vlhkosť
* Pohyb
* Teplota
* Multisnímač kontakt
* Multisnímač detektor úniku
* Multisnímač vlhkosť
* Multisnímač pohyb
* Multisnímač teplota
* Multisnímač ultrazvuk
* Multisnímač vlhkosť pôdy

### Povoliť senzor
Aktivácia alebo deaktivácia tohto snímača.

### Názov senzora
Zadajte názov snímača. Názvy snímačov musia byť nenulové a jedinečné.

### Typ senzora
Vyberte typ senzora.

#### Kontakt
* Otvorený program(y) Označte požadované programy, ktoré chcete spustiť.
* Alebo zastaviť tieto spustené stanice v plánovači.
* Zatvorený program(y) Označte požadované programy, ktoré chcete spustiť.
* Alebo zastaviť tieto spustené stanice v plánovači.

#### Detektor úniku
* Citlivosť (0-100%) Pri prekročení tejto úrovne sa aktivuje(í) vysoký(é) program(y).
* Doba stabilizácie (mm:ss) Po túto nastavenú dobu nebude detektor reagovať na zmenu.
* Nízky program(y) Označte požadované programy, ktoré chcete spustiť.
* Vysoký program(y) Označte požadované programy, ktoré chcete spustiť.

#### Vlhkosť
* Nízka úroveň (0-100%) Pri prekročení tejto úrovne sa aktivuje(í) nízky(é) program(y).
* Nízky program(y) Označte požadované programy, ktoré chcete spustiť.
* Vysoká úroveň (0-100%) Pri prekročení tejto úrovne sa aktivuje(í) vysoký(é) program(y).
* Vysoký program(y) Označte požadované programy, ktoré chcete spustiť.

#### Pohyb
* Program(y) Označte požadované programy, ktoré chcete spustiť.

#### Teplota
* Nízka úroveň (0-100 °C/°F) Pri prekročení tejto úrovne sa aktivuje(í) nízky(é) program(y).
* Nízky program(y) Označte požadované programy, ktoré chcete spustiť.
* Vysoká úroveň (0-100 °C/°F) Pri prekročení tejto úrovne sa aktivuje(í) vysoký(é) program(y).
* Vysoký program(y) Označte požadované programy, ktoré chcete spustiť.
Pri teplote sa zobrazujú stupne Celzia, alebo stupne Fahrenheita podľa toho, ako máme na titulnej stránke (v pravo dole) nastavenú teplotu (kliknutím na teplotu je možné zmeniť jednotky).

#### Ultrazvuk
* Vzdialenosť od ultrazvukového snímača (zhora) k minimálnej hladine vody v nádrži.
* Vzdialenosť od ultrazvukového snímača (zhora) k maximálnej hladine vody v nádrži.
* Minimálna hladina vody v nádrži (odo dna nádrže) pre report.
* Priemer valca na výpočet objemu.
* Zobrazovať v litroch alebo m3.
* Zastaviť stanice, ak je minimálna hladina vody.
* Čas oneskorenia (hodiny).
* Zastaviť stanice, ak má ultrazvukový snímač poruchu.
* Zastaviť tieto stanice v plánovači.
* Regulácia maximálnej hladiny vody.
* Maximálna udržiavaná hladina vody.
* Maximálna doba behu v aktivácii.
* Minimálna udržiavaná hladina vody.
* Výstup pre reguláciu.

#### Vlhkosť pôdy
* Sonda xx riadi program (zvoľte v zozname programov program, ktorý chcete sondou 1-16 ovplyvňovať).
* Kalibrácia xx sondy pre 100% (zadajte úroveň napätia vo voltoch pre kalibráciu sondy pri vlhkosti 100%).
* Kalibrácia xx sondy pre 0% (zadajte úroveň napätia vo voltoch pre kalibráciu sondy pri vlhkosti 0%).

### Typ komunikácie
Vyberte typ komunikácie so senzorom.
#### Rádio
Zadajte ID snímača pre váš rádiový snímač. ID snímača musí byť nenulové a jedinečné.

#### Wi-Fi / LAN
* Zadajte MAC adresu snímača. Príklad: aa: bb: cc: dd: ee: ff
* Zadajte IP adresu snímača. Príklad: 192.168.88.10

### Vzorkovacia frekvencia
Zadajte čas vzorkovania v minútach a sekundách (mm:ss).

### Záznam vzorky
Povoliť protokolovanie vzoriek.

### Denník udalostí
Povoliť protokolovanie udalostí.

### Text/E-mail udalosť
Povoliť odosielanie E-mailov, keď dôjde k udalosti. Pre túto funkciu je vyžadované rozšírenie e-mail notification!

### Poznámky
Tu si môžeme písať poznámky.

## Odstrániť všetky senzory
Tlačidlo „Odstrániť všetky snímače“ vymaže všetky pridané snímače v systéme.

----

## Pridať nový snímač (od shelly.com)
Snímače Shelly je možné integrovať do OSPy pomocou rozšírenia "shelly cloud integrator" v ktorom pripojíme dostupné zariadenia (buď cez cloud shelly.com, alebo v miestnej sieti).
Tieto zariadenia môžeme následne vyhľadať v OSPy v časti snímača/vyhľadávania. V OSPy môžeme využívať merania napríklad spotreby, napätia, stavu výstupov atď...

----

#  Pomocník
Na stránke "Pomocník" nájdeme dokumentáciu ku všetkým rozšíreniam, OSPy systému, zmeny v systéme, prístup pomocou API, webové rozhranie.
Plávajúca ikona PDF otvorí tlačovú verziu práve zobrazeného článku bez navigácie OSPy. V tlačovom dialógu prehliadača možno článok uložiť ako súbor PDF.

## OSPy
### Readme
Hlavná dokumentácia k OSPy, inštalácia systému, prepojenie dosky, licencie.

### Changelog
Zmeny v systéme OSPy, alebo v rozšíreniach

### Programs
Interne všetky programy udržujú plán, ktorý je možné priamo upraviť (rovnako ako vlastný program).
Pre ľahšiu manipuláciu boli vytvorené nasledujúce typy programov.
Každý program môže byť jedným z týchto typov. Nakoniec je možné každý program napísať aj ako vlastný program.<br/>

Prog/type_data  |             0                |     1          |      2         |     3         |      4         |     5
             --:|:--                           |:--             |:--             |:--            |:--             |
DAYS_SIMPLE     |start_time                    |duration        |repeat pause    |repeat times   |list days to run|
REPEAT_SIMPLE   |start_time                    |duration        |repeat pause    |repeat times   |repeat days     |start_date
DAYS_ADVANCED   |list of intervals [start, end]|list days to run|                |               |                |
REPEAT_ADVANCED |list of intervals [start, end]|repeat days     |                |               |                |
WEEKLY_ADVANCED |list of intervals [start, end]|                |                |               |                |
CUSTOM          |list of intervals [start, end]|                |                |               |                |
WEEKLY_WEATHER  |                              |                |                |               |                |

set_days_simple start_min, duration_min, pause_min, repeat_times, [days]
set_repeat_simple start_min, duration_min, pause_min, repeat_times, repeat_days, start_date
set_days_advanced [schedule], [days]
set_repeat_advanced [schedule], repeat_days, start_date
set_weekly_advanced [schedule]
set_weekly_weather  irrigation_min, irrigation_max, run_max, pause_min, pems

### Web Interface Guide - Czech
Pomocník k webovému rozhraniu v slovenčine.

### Web Interface Guide - English
Pomocník k webovému rozhraniu v angličtine.

### Web Interface Guide - German
Pomocník k webovému rozhraniu v nemčine.

### Web Interface Guide - Polish
Pomocník k webovému rozhraniu v poľštine.

### Web Interface Guide - Russian
Pomocník k webovému rozhraniu v ruštine.

### Web Interface Guide - Serbian
Pomocník k webovému rozhraniu v srbčine.

### Web Interface Guide - Slovak
Pomocník k webovému rozhraniu v slovenčine.

## API
### Readme
Pre moderné webové prehliadače sa odporúča, aby rozhranie API bolo postavené na princípe CRUD pomocou formátu JSON ako formátu dátových kontajnerov.

### Podrobnosti
Mapovanie metód HTTP/s.

## Doplnky
Základná štruktúra všetkých rozšírení je nasledovná:

plugins
+ plugin_name
  + data
  + docs
  + static
  + script
  + templates
  + __init__.py
  \ README.md

Statické súbory budú automaticky sprístupnené na nasledujúcom mieste: /plugins/názov_pluginu/static/...
Všetky * .md súbory v adresári docs budú viditeľné na stránke "Pomocník". *

### Dostupné rozšírenia:

* Usage Statistics (anonymné štatistiky o používaní OSPy systému)
* LCD Display (LCD displej 16x2 znakov pripojený pomocou I2C zbernice)
* Pressure Monitor (stráženie tlaku v potrubí - ochrana čerpadla)
* Voice Notification (zvukové upozornenia - prehrávanie súborov mp3)
* Pulse Output Test (test výstupov - slúži na nájdenie určitého ventilu v krajine)
* Button Control (ovládanie systému OSPy pomocou 8 tlačidiel - slúži na ručné spúšťanie programov)
* CLI Control (vzdialené ovládanie periférií pomocou URL príkazov - napríklad RF zásuvky)
* System Watchdog (strážny pes systému Raspberry Pi, ak systém zamrzne, dôjde k reštartu systému)
* Voltage and Temperature Monitor (meranie napätia a teploty pomocou I2C zbernice)
* Remote Notifications (odosielanie dát na vzdialený server pomocou PHP)
* System Information (systémové informácie OSPy a systém Linux)
* Air Temperature and Humidity Monitor (meranie teploty 6x DS18B20 a vlhkosti DHT11 pomocou I2C zbernice)
* Wind Speed Monitor (meranie rýchlosti vetra pomocou I2C zbernice)
* Weather-based Rain Delay (dažďové oneskorenie založené na predpovedi počasia)
* Relay Test (testuje relé pre hlavné čerpadlo)
* UPS Monitor (stráži výpadok napájania systému, odosiela email a ukončuje Linux systém)
* Water Consumption Counter (virtuálny merač prietoku vody založený na výpočte behu hlavnej stanice)
* SMS Modem (vzdialené ovládanie pomocou SMS a USB modemu)
* Signaling Examples (príklad notifikácií tupu "signal" v systéme OSPy)
* E-mail Notifications (odosielanie E-mailov zo systému - toto rozšírenie využívajú aj niektoré iné rozšírenia, napríklad: Wind Speed Monitor, Pressure Monitor, Air Temperature and Humidity Monitor...)
* Remote FTP Control (zjednodušené vzdialené ovládanie OSPy pomocou servera s PHP a FTP)
* System Update (pomocou tohto rozšírenia je možné jednoducho aktualizovať systém OSPy z GIThubu namiesto systémových príkazov)
* Water Meter (meranie prietoku pomocou vodomeru s pulzným výstupom pomocou I2C zbernice)
* Webcam Monitor (vytvára fotografie z USB webkamery)
* Weather-based Water Level Netatmo (nastavenie množstva vody na zavlažovanie z meteostanice Netatmo)
* Direct 16 Relay Outputs (pomocou tohto rozšírenia môžeme ovládať 16 relé (staníc) pripojených priamo k Raspberry Pi, avšak niektoré ostatné rozšírenia nebudú dostupné)
* MQTT (hlásenie stavu OSPy pomocou MQTT protokolu, ovládanie staníc cez MQTT...)
* System Debug Information (informácie o dianí v systéme OSPy, ak máme v nastavení povolený debug "Povoliť ladenie", tak tu v rozšírení sa zobrazuje uložený záznam)
* Weather-based Water Level (nastavenie množstva vody na zavlažovanie založený na predpovedi počasia)
* Real Time and NTP time (rozšírenie, ktoré nastavuje systémový čas - Linux a HW RTC čas z NTP servera, HW RTC používa I2C zbernicu)
* Water Tank (meranie hladiny vody pomocou ultrazvuku - napríklad v studni pomocou I2C zbernice)
* Monthly Water Level (nastavenie množstva vody pre jednotlivé mesiace)
* Pressurizer (tlakovanie čerpadla pred spustením programov)
* Ping monitor (meranie výpadkov siete)
* Temperature Switch (regulátor teploty, ktorý umožnuje 3 nezávislé zóny)
* Pool Heating (regulácia teploty bazéna podľa solárneho ohrevu)
* E-mail reader (ovládanie OSPy pomocou E-mailových správ)
* Weather Stations (zobrazenie hodnôt z ostatných rozšírení v štýle ručičkových budíkov) verzia 1.0
* Telegram Bot (komunikácia s OSPy pomocou telegram.org app)
* Door Opening (otvorenie zámku dverí, alebo posuvnej brány)
* Voice Station (zvukové upozornenia na základe udalosti staníc- prehrávanie súborov wav a mp3)
* Ovládanie žalúzií (toto rozšírenie odosiela cez REST API príklazy do Wi-Fi relátok firmy Shelly, alebo podobných relé)
* Monitor rýchlosti Internetového pripojenia (odozva, sťahovanie, nahrávanie)
* E-mail Notifications SSL (odosielanie E-mailov zo systému - toto rozšírenie využívajú aj niektoré iné rozšírenia, napríklad: Wind Speed Monitor, Pressure Monitor, Air Temperature and Humidity Monitor...) Toto rozšírenie je modernejším variantom pôvodného rozšírenia E-mailové oznámenia (Pripojenie cez vrstvu SSL.
* Sunrise and Sunset (výpočet astronomických dát ako je východ a západ slnka. Podľa týchto výpočtov umožňuje následne spúšťať programy).
* FVE bojler (nahrievanie bojlera z distribučnej siete, alebo FVE elektrárne).
* IP kamery (umožňuje sledovanie z IP kamier. Ako JPEG náhľad, alebo GIF obrázok, alebo MJPEG stream z kamery).
* CHMI (umožňuje z meteoradaru ČHMI načítať aktuálne počasie a podľa neho nastavovať časové oneskorenie. Zároveň zobrazovať RGB stav počasia na HW mape).
* Preto (predvolený plugin pre tvorbu ďalších nových pluginov. Plugin nič závratné nerobí, ale vysvetľuje ako pracuje).
* Label Maker (vytváranie EAN a QR kódov).
* IP Scanner (hľadanie IP a MAC v sieti).
* Database Connector (prepojenie do databázy pre ukladanie dát z čidiel a senzorov).
* OSPy Backup (zálohovanie adresára dáta zo všetkých rozšírení do súborov zip).
* MQTT Home Assistant (integrácia do HASS pomocou MQTT).
* Shelly Cloud Integration (načítanie stavov z cloudu výrobcu zariadenia Shelly).
* Current Loop Tanks Mmonitor (meranie hladiny zo 4 snímačov).
* Network Ping Monitor (monitoring dostupnosti 3 zariadení v sieti).
* Weather Dashboard (zobrazenie hodnôt z ostatných rozšírení v štýle ručičkových budíkov) verzia 2.0
* Termostat
----

# Odhlásiť sa
Po kliknutí na tlačidlo "Odhlásiť sa" sa užívateľ odhlási zo systému.
