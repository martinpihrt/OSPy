OSPy Průvodce webovým rozhraním v češtině
====

    Přihlásit se
    Domácí stránka
        Normální - % doby programu
        Aktivní - Zpoždění při dešti
        Plánovač - Ručně
        Povoleno - Zakázáno
        Zastavit všechny stanice
        Statistika zavlažování (graf)
        Potlačeno zpožděním při dešti 
        Detekován déšť
        Teplota CPU
        Využití CPU
        Program OSPy verze
        Vnější IP adresa
        V provozu
    Programy
        Přidat nový program
        Spustit nyní
        Úprava 
        Smazat vše 
        Zap/Vyp program
        Typ plánovače
            Vybrané dny (Jednoduchý)
                Čas startu
                Trvání
                Opakovat
                Opakování
                Pauza
            Vybrané dny (Rozšířené)
                Plánovač
            Opakování (Jednoduché)
                Interval zavlažování
                Start ve dni
                Čas startu
                Trvání
                Opakovat
                Opakování
                Pauza
            Opakování (Rozšířené)
                Interval zavlažování
                Start ve dni
                Plánovač
            Týdenní (Rozšířené)
                Pondělí-Neděle
            Vlastní
                Interval zavlažování
                Start ve dni
                Den 1 - Den 7
            Týdenní (Předpověď počasí)
                Minimální zavlažování
                Maximální zavlažování
                Maximální dávka
                Poměr pauzy
                Upřednostnění okamžiku provedení
                    Den
                    Čas startu
                    Přednost
                    Přidat - Smazat
        Žádné úpravy
        Odříznout
    Jednorázový
        Spustit nyní
        Smazat čas
    Rozšíření
        Spravovat
        Instalovat nové rozšíření
            Vlastní rozšíření (ZIP)
            Github (https://github.com/martinpihrt/OSPy-plugins/archive/master.zip)  
        Vypnout vše
        Zapnout vše 
        Povolit kontrolu aktualizací
        Auto aktualizace
    Záznam
        Stáhnout záznam jako
        Smazat záznam
        Smazat záznam Email
    Nastavení
        Systém
            Zobrazit nápovědu
            Název systému
            Šablona webu
            24-hodinový čas
            HTTP IP adresa
                O čísle portu 
            HTTP/S port 
            Zobrazit rozšíření na home
            Jazyk          
        Počasí
            Použít počasí
            Dark Sky API klíč
            Umístění
            Nadmořská výška
        Uživatelé
            Bez hesla
            Jméno správce
            Aktuální heslo
            Nové heslo
            Potvrďte heslo 
            Další uživatelé
        Bezpečnost            
            Použít HTTPS
            Jméno domény
            Použít vlastní HTTPS          
        Nastavení stanic
            Maximální využití
                O sekvenčních a souběžných režimech
            Počet výstupů
            Zpoždění stanice
            Min čas běhu
        Nastavení hl. stanice
            Hlavní stanice
            Hlavní stanice 2
            Aktivovat relé
            T zapnutí
            T vypnutí
            T2 zapnutí
            T2 vypnutí 
        Dešťový senzor
            Používat senzor
            V klidu rozpojen
        Protokolování
            Aktivovat záznam
            Max záznamů
            Aktivovat záznam Emailů
            Max záznamů
            Povolit ladění
        Restartovat systém
            Restart OSPy
            Restart HW
            Vypnout
            Smazat nastavení 
        Záloha a obnovení
            Stáhnout
            Nahrát
        Certifikát SSL
            Nahrát  
            Generovat          
    Stanice
        Stanice 
        Jméno
        Využití
        Závlaha
        Zásoba
        ETo faktor
        Zůstatek
        Připojeno
        Ignorovat Déšť
        ZAP Hlavní
        ZAP Hlavní 2
        Poznámky  
    Nápověda
        OSPy
            Readme
            Changelog
            Programs
            Web Interface Guide - Czech
            Web Interface Guide - English
        API
            Readme
            Details
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
    Odhlásit se

----

# Přihlásit se
<a href="https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Web%20Interface%20Guide%20-%20Czech/login.png" rel="Přihlásit se" target="_blank">![Přihlásit se - obrázek](https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Web%20Interface%20Guide%20-%20Czech/login.png)</a>

Přihlašovací stránka představuje textové pole pro zadání hesla. Výchozí heslo je ** opendoor **.
Na stránce - záložce "Nastavení" se doporučuje změnit si heslo na Vaše nové heslo.
Zadejte heslo a klikněte na tlačítko **PŘIHLÁSIT SE**.


----

# Domácí stránka
<a href="https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Web%20Interface%20Guide%20-%20Czech/home.png" rel="Domácí stránka" target="_blank">![Domácí stránka - obrázek](https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Web%20Interface%20Guide%20-%20Czech/home.png)</a>

Domovská stránka je hlavním ovládacím centrem webového rozhraní. To zahrnuje:

* Hodiny zobrazující aktuální čas Na všech stránkách.
* Navigační lišta v horní části pro pohyb mezi stránkami. Rozhraní se také nachází na ostatních stránkách kromě přihlašovací stránky.
* Sada tlačítek pro provádění globálních změn chování systému.
* Časová osa, která poskytuje informace o dokončených a naplánovaných zavlažovacích událostech.
* Graf, který poskytuje informace o zavlažovacích událostech.
* Zápatí, které je přítomno na všech stránkách (pokud je přihlášený uživatel). Zápatí obsahuje: Teplota procesoru, Využití procesoru, Verze softwaru, Externí IP adresa, Doba provozu OS.


## Normální - % doby programu
Tlačítko, které umožňuje nastavit „hladinu vody“ jako celkové procento doby běhu pro všechny zavlažovací programy (u programů prodloužit, nebo zkrátit jejich nastavenou dobu).

## Aktivní - Zpoždění při dešti
Zpoždění při dešti. Tlačítko, které umožňuje na zadanou dobu pozastavení zavlažování pro všechny stanice kromě těch, které byly nastaveny tak, aby ignorovaly déšť na stránce Stanice.

## Plánovač - Ručně
Plánovač - Ručně. Tlačítko, které přepíná systém mezi plánem (automatickým režimem) a manuálním režimem, který umožňuje přímé ovládání stanic.

## Povoleno - Zakázáno
Tlačítko pro povolení, nebo zakázání běhu OSPy programu (při zakázáno nepoběží plánovač).

## Zastavit všechny stanice
Tlačítko „Zastavit všechny stanice“ slouží pro okamžité zrušení spuštěného zavlažovacího programu nebo aktivní stanice.

## Statistika zavlažování (graf)
Pokud je v plánovači nastaven alespoň jeden program, ve spodní části obrazovky bude nakreslen graf s množstvím vody dodané pro každou stanici (programy).

## Potlačeno zpožděním při dešti 
Je-li aktivováno zpoždění při dešti, zobrazí se „Potlačeno dešťovým zpožděním“ a všechny stanice (kromě těch, které byly nastaveny tak, aby ignorovaly déšť na stránce Stanice) budou po určitou dobu blokovány.
  
## Detekován déšť
Pokud je aktivován dešťový senzor, zobrazí se „Potlačeno dešťovým senzorem“ a všechny stanice (kromě těch, které byly nastaveny tak, aby ignorovaly déšť na stránce Stanice) budou blokovány.

## Teplota CPU
Teplota procesoru Raspberry pi. Zobrazenou teplotu lze přepínat mezi C a F.

## Využití CPU
Využití procesoru Raspberry pi. Využití je zobrazené v %.

## Program OSPy verze
Odkaz na úložiště softwaru projektu a číslo revize nainstalovaného softwaru.

## Vnější IP adresa
Externí IP adresa pro systém OSPy (adresa vašeho poskytovatele připojení - routeru). Testováno prostřednictvím služby bot.whatismyipaddress.com.

## V provozu
Doba běhu systému Raspberry pi od zapnutí (nebo restartu).

----

# Programy
<a href="https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Web%20Interface%20Guide%20-%20Czech/programy.png" rel="Programy" target="_blank">![Programy - obrázek](https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Web%20Interface%20Guide%20-%20Czech/programy.png)</a>

## Přidat nový program

## Spustit nyní

## Úprava 

## Smazat vše 

## Zap/Vyp program

## Typ plánovače

### Vybrané dny (Jednoduchý)
<a href="https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Web%20Interface%20Guide%20-%20Czech/dny%20jednoduchy.png" rel="Vybrané dny (Jednoduchý)" target="_blank">![Vybrané dny (Jednoduchý) - obrázek](https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Web%20Interface%20Guide%20-%20Czech/dny%20jednoduchy.png)</a>
   
#### Čas startu
    
#### Trvání
 
#### Opakovat
    
#### Opakování
    
#### Pauza

### Vybrané dny (Rozšířené)
<a href="https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Web%20Interface%20Guide%20-%20Czech/dny%20rozsireny.png" rel="Vybrané dny (Rozšířené)" target="_blank">![Vybrané dny (Rozšířené) - obrázek](https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Web%20Interface%20Guide%20-%20Czech/dny%20rozsireny.png)</a>
    
#### Plánovač

### Opakování (Jednoduché)
<a href="https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Web%20Interface%20Guide%20-%20Czech/opak%20jednoduchy.png" rel="Opakování (Jednoduché)" target="_blank">![Opakování (Jednoduché) - obrázek](https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Web%20Interface%20Guide%20-%20Czech/opak%20jednoduchy.png)</a>
    
#### Interval zavlažování

#### Start ve dni

#### Čas startu

#### Trvání

#### Opakovat

#### Opakování

#### Pauza
    
### Opakování (Rozšířené)
<a href="https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Web%20Interface%20Guide%20-%20Czech/opak%20rozsireny.png" rel="Opakování (Rozšířené)" target="_blank">![Opakování (Rozšířené) - obrázek](https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Web%20Interface%20Guide%20-%20Czech/opak%20rozsireny.png)</a>
    
#### Interval zavlažování
  
#### Start ve dni

#### Plánovač
    
### Týdenní (Rozšířené)
<a href="https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Web%20Interface%20Guide%20-%20Czech/tyden%20rozsireny.png" rel="Týdenní (Rozšířené)" target="_blank">![Týdenní (Rozšířené) - obrázek](https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Web%20Interface%20Guide%20-%20Czech/tyden%20rozsireny.png)</a>

#### Pondělí-Neděle

### Vlastní

#### Interval zavlažování

#### Start ve dni

#### Den 1 - Den 7

### Týdenní (Předpověď počasí)
<a href="https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Web%20Interface%20Guide%20-%20Czech/tyden%20predpoved.png" rel="Týdenní (Předpověď počasí)" target="_blank">![Týdenní (Předpověď počasí) - obrázek](https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Web%20Interface%20Guide%20-%20Czech/tyden%20predpoved.png)</a>
    
#### Minimální zavlažování

#### Maximální zavlažování

#### Maximální dávka

#### Poměr pauzy

#### Upřednostnění okamžiku provedení

#### Den

#### Čas startu

#### Přednost

#### Přidat - Smazat

## Žádné úpravy
    
## Odříznout

----

# Jednorázový
<a href="https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Web%20Interface%20Guide%20-%20Czech/jednorazovy.png" rel="Jednorázový" target="_blank">![Jednorázový - obrázek](https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Web%20Interface%20Guide%20-%20Czech/jednorazovy.png)</a>

Stránka "Jednorázový" představuje seznam povolených stanic s polem minuty a sekundy pro každou z nich. Tato stránka může být použita pro testování a poskytnutí dodatečného zavlažování jednorázově.

## Spustit nyní
Tlačítko aktivuje všechny vybrané předvolené stanice.
   
## Smazat čas
Tlačítko odstraní veškeré přednastavené časy u všech stanic.

----

# Rozšíření
<a href="https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Web%20Interface%20Guide%20-%20Czech/rozsireni.png" rel="Rozšíření" target="_blank">![Rozšíření - obrázek](https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Web%20Interface%20Guide%20-%20Czech/rozsireni.png)</a>

Na stránce "Rozšíření" můžeme nakonfigurovat nebo ovládat všechna rozšíření v systému OSPy.

## Spravovat
<a href="https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Web%20Interface%20Guide%20-%20Czech/rozsireni%20seznam.png" rel="Spravovat" target="_blank">![Spravovat - obrázek](https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Web%20Interface%20Guide%20-%20Czech/rozsireni%20seznam.png)</a>

Po kliknutí na tlačítko "Spravovat" se otevře okno správce rozšíření v systému OSPy. Všechna dostupná rozšíření lze zapínat, vypínat, instalovat z repozitáře atd...
  
## Instalovat nové rozšíření
<a href="https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Web%20Interface%20Guide%20-%20Czech/rozsireni%20instal.png" rel="Instalovat" target="_blank">![Instalovat - obrázek](https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Web%20Interface%20Guide%20-%20Czech/rozsireni%20instal.png)</a>

Po kliknutí na tlačítko "Instalovat nové rozšíření" se otevře okno se vzdáleným repozitářem, kde si můžeme vybrat dostupná rozšíření pro instalaci do systému OSPy a přečíst si všeobecné informace k rozšířením.
  
### Vlastní rozšíření (ZIP)
Správce rozšíření umožňuje do systému OSPy nainstalovat i vlastní rozšíření, které není zveřejněné ve vzdáleném repozitáři (například vaše nějaké osobní rozšíření). Pomocí tlačítka "procházet" zvolíme požadovaný soubor v našem počítači k instalaci do systému OSPy. Soubor rozšíření (zip) musí obsahovat kompletní strukturu rozšíření (init, templates, i18n, readme atd).

### Github (https://github.com/martinpihrt/OSPy-plugins/archive/master.zip)  
Na výše uvedeném umístění se nachází repozitář s dostupnými rozšířeními pro systém OSPy.

## Vypnout vše
Tlačítko zakáže všechna nainstalovaná rozšíření.
   
## Zapnout vše 
Tlačítko povolí všechna nainstalovaná rozšíření.
  
## Povolit kontrolu aktualizací
Když je tlačítko aktivní, tak se automaticky po hodině kontroluje ve vzdáleném repozitáři dostupnost nové verze rozšíření. Při dostupnosti nové verze se u rozšíření zobrazí hláška "aktualizovat".
  
## Auto aktualizace
Když je tlačítko aktivní, tak se při dostupnosti nové verze rozšíření automaticky provede aktualizace tohoto rozšíření. Upozornění: systém OSPy se neustále vyvíjí a pokud dojde k zásadní změně v systému OSPy a uživatel systém OSPy nebude aktualizovat, může dojít k tomu, že rozšíření po aktualizaci nebude pracovat. Vždy nejprve aktualizujte systém OSPy a následně všechna rozšíření!

----

# Záznam
<a href="https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Web%20Interface%20Guide%20-%20Czech/zaznam.png" rel="Programy" target="_blank">![Záznam - obrázek](https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Web%20Interface%20Guide%20-%20Czech/zaznam.png)</a>

Pomocí stránky "Záznam" můžeme zobrazit veškeré protokoly zaznamenané v systému OSPy. Počet záznamů se nastavuje na stránce "Nastavení".
    
## Stáhnout záznam jako
Odkaz "Stáhnout záznam jako Excel log.csv" umožní uložit do počítače záznam o běhu zavlažování jako soubor csv (program Excel).
* Struktura tabulky je: Date, Start Time, Zone, Duration, Program. Data jsou oddělena čárkou.
* Příklad: 2019-08-12 	05:00:00 	Filtrace 	60:00 	Filtrace

Odkaz "Stáhnout záznam jako Excel log email.csv." umožní uložit do počítače záznam o odeslaných emailech jako soubor csv (program Excel).
* Struktura tabulky je: Date, Time, Subject, Body, Status. Data jsou oddělena čárkou.
* Příklad: 2019-08-12 	06:00:04 	Odesláno 	CHATA SYSTÉM 	Ukončené zalévání-> Program: Filtrace , Stanice: Filtrace , Začátek: 2019-08-12 05:00:00 , Trvání: 60:00 , Water-> Množství vody v zásobníku: Level: 170 cm (90 %), Ping: 95 cm, Volume: 1.28 m3 , Temperature DS1-DS6-> SKLEP: 21.1 ℃ ČERPADLO: 33.5 ℃ BOJLER: 26.6 ℃ UVNITŘ: 22.1 ℃ STUDNA: 12.2 ℃ 
   
## Smazat záznam
Po stisknutí tlačítka "Smazat záznam" dojde k vymazání všechn záznamů o běhu zavlažování. Akce je nevratná.

## Smazat záznam Email
Po stisknutí tlačítka "Smazat záznam Email" dojde k vymazání všechn záznamů o odeslaných emailech ze systému. Akce je nevratná.

----

# Nastavení
<a href="https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Web%20Interface%20Guide%20-%20Czech/nastaveni%201.png" rel="Nastavení" target="_blank">![Nastavení - obrázek 1](https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Web%20Interface%20Guide%20-%20Czech/nastaveni%201.png)</a>

<a href="https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Web%20Interface%20Guide%20-%20Czech/nastaveni%202.png" rel="Nastavení" target="_blank">![Nastavení - obrázek 2](https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Web%20Interface%20Guide%20-%20Czech/nastaveni%202.png)</a>

Na stránce "Nastavení" můžeme upravovat nastavení celého OSPy systému.
Stránka obsahuje několik skládacích oddílů. Kliknutím na pruh otevřeme nebo zavřeme požadovanou část.

### Zobrazit nápovědu

* Kliknutím na tlačítko "Zobrazit nápovědu" zobrazíme, nebo skryjeme informace o každé možnosti.

### Název systému
Pojmenování systému je užitečné při práci s několika OSPy systémy.

* Zadejte jedinečný popisný název systému.
* Klepnutím na tlačítko "Potvrdit změny" ve spodní části stránky uložte změny.

Název systému je ve výchozím stavu "OpenSprinkler Pi" a bude zobrazen v záhlaví každé stránky pro snadnou identifikaci systému.

### Šablona webu
Určuje vzhled GUI. V seznamu je k dispozici několik témat (zelený režim, černobílý režim...)

### 24-hodinový čas
Volba 24-hodinový čas vybírá mezi mezinárodním formátem 24 hodin, někdy označovaným jako vojenský čas, a formátem 12 hodin-AM / PM.

* Zrušte zaškrtnutí políčka a vyberte 12 hodinový formát AM/PM.
* Klepnutím na tlačítko "Potvrdit změny" ve spodní části stránky uložte změny.

Budete přesměrováni na domovskou stránku a hodiny budou ve vybraném formátu.

### HTTP IP adresa
IP adresa pro HTTP/S server. IPv4 nebo IPv6 adresa (projeví se až po restartu.) Výchozí je 0.0.0.0.

#### O čísle portu 
Číslo portu HTTP/S je součástí webové adresy.
Port 80 je výchozí číslo pro webové stránky a jako takové nemusí být zahrnuto, když je adresa URL zadána do adresního řádku prohlížeče. Mnoho webových serverů standardně používá port 80.
Pokud provozujete jiný server na stejném Raspberry Pi jako OSPy a používáte stejné číslo portu, dojde ke konfliktu a OSPy se nemusí spustit.
Konfliktu se můžete vyhnout změnou čísla portu OSPy na stránce Možnosti na něco jiného například 8080. Pokud změníte číslo portu, které OSPy používá, budete muset zahrnout toto číslo, kterému předchází dvojtečka, do adresy URL pro webové rozhraní OSPy. Například:
[URL Raspberry pi]: 8080

### HTTP/S port
Číslo portu HTTP/S je součástí webové adresy. Port 80 je výchozí číslo pro webové stránky.

* Klikněte do textového pole vedle možnosti HTTP/ S port.
* Zadejte číslo portu, který chcete použít, např. 8080.
* Klikněte na tlačítko "Potvrdit změny" ve spodní části stránky.

Vrátíte se na domovskou stránku. Systém se restartuje, ale ve webovém rozhraní není viditelná indikace restartu. Počkejte alespoň 60 sekund, poté přidejte nové číslo portu do adresy URL Pi, před kterým je dvojtečka (:), a zkuste se znovu připojit k OSPy.

### Zobrazit rozšíření na home
Pokud chceme na úvodní (domácí stránce) zobrazovat pod grafem naměřená data z rozšíření (vítr, teplota, hladina...) zaškrtneme políčko. V případě, že nechceme zobrazovat data z rozšíření zrušíme zaškrtnutí.
* Upozornění: aby se data zobrazovala v pořádku je nezbytné mít rozšíření povolené a správně nastavené.

### Jazyk  
Volbou jazyka můžeme změnit jazyk používaný ve webovém rozhraní.

* Klepnutím na šipku dolů napravo od pole jazyka zobrazíte seznam dostupných jazyků.
* Klikněte na jazyk, který chcete použít v rozhraní.
* Klikněte na tlačítko "Potvrdit změny" ve spodní části stránky.

Software se restartuje a po několika sekundách se rozhraní zobrazí ve zvoleném jazyce.
        
## Počasí
Sekce počasí umožňuje přístup ke službě předpovědi počasí pro vaši polohu. Musíte se zaregistrovat pro tuto funkci na webu (https://darksky.net/dev).
Podle předpovědi počasí lze zavlažovací cyklus automaticky upravit (pokud zvolíme rozšíření, které používá předpověď počasí).
* Registrace a použití služby není pro běžné použití zpoplatněno.

### Použít počasí
Povolení nebo zakázání připojení ke službě Dark Sky.

### Dark Sky API klíč
K využití místních povětrnostních podmínek je nutný klíč rozhraní Dark Sky API.

### Umístění
Název města nebo PSČ. Slouží k určení polohy pomocí OpenStreetMap pro informace o počasí ze služby Dark Sky.

### Nadmořská výška
Nadmořská výška místa v metrech, kde je umístěn zavlažovací systém (nemusí být vyplněno).

## Uživatelé
Pro zvýšení bezpečnosti doporučujeme změnit systémové heslo pro OSPy z výchozího "opendoor" a uživatelské jméno z výchozího "admin". V případě potřeby můžete také požadavek na heslo deaktivovat.

* Klepnutím na trojúhelník nalevo od lišty s popiskem "Uživatelé" rozbalte sekci.
* Označte zaškrtnutím políčko "Bez hesla", pokud máte velmi dobrý důvod k deaktivaci ochrany heslem a jménem. Systém již nebude vyžadovat přihlášení uživatele. Bude umožnen přístup do všech sekcí.
* Zadejte Vaše uživatelské jméno (výchozí "admin").
* Zadejte Vaše aktuální heslo (výchozí "opendoor". 
* Zadejte nové heslo do polí označených "Nové heslo" a "Potvrďte heslo".
* Klikněte na tlačítko "Potvrdit změny" ve spodní části stránky.

Vrátíte se na domovskou stránku. Vaše nové heslo s jméno bude vyžadováno při příštím přihlášení.

### Bez hesla
Pokud je zaškrtnuté políčko "Bez hesla" povolíme přístup do systému anonymním uživatelům bez hesla.

### Uživatelské jméno
Do textového pole zadejte uživatelské jméno. To je při nové instalaci "admin".

### Aktuální heslo
Do textového pole zadejte aktuální heslo. To je při nové instalaci "opendoor".

### Nové heslo
Zadejte nové heslo do pole označeného "Nové heslo".

### Potvrďte heslo           
Do pole označeného "Potvrďte heslo" zadejte stejné nové heslo jak v poli "Nové heslo".

### Další uživatelé
Po kliknutí na tlačítko se otevře stránka, kde můžeme vytvářet a případně upravovat nové uživatele pro přístup do systému.

## Bezpečnost

### Použít HTTPS 
V případě, že jsme nakonfigurovali server OSPy pro vyšší zabezpečení přenosu dat pomocí certifikátu SSL, zaškrtněte políčko "Použít HTTPS". Pokud je zaškrtnuta volba "Použít HTTPS" a server není správně nastaven, OSPy se spustí jako http server bez zabezpečení.

### Jméno domény
Certifikát je umístěn v systému v adresáři '/etc/letsencrypt/live/' jméno domény '/fullchain.pem' a '/etc/letsencrypt/live/' jméno domény '/privkey.pem'. Certifikát je nutné pomocí nástroje "Certbot" nainstalovat do systému (Linux) ručně (použití https se projeví v OSPy až po restartu OSPy).
* Postup pro instalaci Certifikační služby nalezneme v souboru "Readme" nápovědy, nebo na Githubu.

### Použít HTTPS pomocí Certbot
SSL certifikát pomocí Let’s Encrypt certifikační autority.
Certbot (https://certbot.eff.org/) a Let’s Encrypt (https://letsencrypt.org/).

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

### Použít vlastní HTTPS
Pokud je v nastavení OSPy vybrána možnost „Použít vlastní přístup HTTPS“, musíte do adresáře ssl v umístění OSPy vložit soubor: fullchain.pem a privkey.pem. Varování: OSPy musí být znovu restartováno.
```bash
sudo openssl req -new -newkey rsa:4096 -x509 -sha256 -days 3650 -nodes -out fullchain.pem -keyout privkey.pem  
```
Druhý způsob je pomocí tlačítka "generovat" v záložce SSL certifikát.

## Nastavení stanic
Sekce "Nastavení stanic" obsahuje všeobecná nastavení pro všechny stanice.

### Maximální využití
Určuje, jak se jednotlivé stanice kombinují. Souběh 0 nebo sekvence 1 (2, 3...) V případě, že všechny stanice mají nastavené sekvenční použití­.

#### O sekvenčních a souběžných režimech
* Při nastavení sekvence (Maximální využití >= 1) se vždy spustí pouze jedna (případně více stanic pokud nastavíme >= 1) stanice (výstup) - například hlavní stanice 1 a stanice 3 záhony. Po uplynutí doby programu se vypne hlavní stanice 1 a stanice 3 záhony. Spustí se hlavní stanice 1 a stanice 4 trávník. Nikdy se spolu nesepnou dvě stanice (například záhony a trávník uvedený v našem příkladu). Sekvenční režim má význam v případě, že nemáme dostupný takový zdroj vody (tlak a množství vody) na pokrytí všech stanic současně
* Při nastavení souběhu (Maximální využití = 0) se vždy spustí neomezené množství stanic v danou dobu nastavenou programy. Například sepne hlavní stanice 1 (čerpadlo) a stanice 2, 3, 4. Souběžné zavlažování zkracuje dobu nutnou k zavlažování, ale vyžaduje větší zdroj vody.

### Počet výstupů
Celkový počet dostupných výstupů je (8 výstupů + x rozšiřujících desek.) Počet výstupů lze nastavit vyšší, než kolik skutečně máme fyzických výstupů (vytváříme virtuální výstupy).

### Zpoždění stanice
Zadejte počet sekund pro zpoždění mezi operacemi stanic. Čas v sekundách mezi 0 a 3600.

### Min čas běhu
Přeskočit zpoždění stanice, pokud by doba běhu byla menší než tato hodnota (v sekundách), mezi 0 a 86400.

## Nastavení hl. stanice
Sekce "Nastavení hl. stanice" obsahuje nastavení pro všechny hlavní stanice. Hlavní stanice se aktivuje, když se aktivuje libovolná stanice.
* Za hlavní stanici můžeme považovat například čerpadlo, hlavní ventil s vodou jako přívod vody do systému.

### Hlavní stanice
Výběr první hlavní stanice (pro čerpadlo nebo hlavní ventil). Určete, který výstup by měl být použit jako hlavní stanice.

### Hlavní stanice 2
Výběr druhé hlavní stanice (pro čerpadlo nebo hlavní ventil). Určete, který výstup by měl být použit jako vedlejší hlavní stanice.

### Aktivovat relé
Pokud je zaškrtnuto, relé bude také aktivováno spolu s 1 (nebo 2) hlavním výstupem.

### T zapnutí
Zpožděné ZAPnutí pro hlavní stanici (v sekundách), mezi -1800 a +1800.

### T vypnutí
Zpožděné VYPnutí pro hlavní stanici (v sekundách), mezi -1800 a +1800.

### T2 zapnutí
Zpožděné ZAPnutí pro 2 hlavní stanici (v sekundách), mezi -1800 a +1800.

### T vypnutí 
Zpožděné VYPnutí pro 2 hlavní stanici (v sekundách), mezi -1800 a +1800.

## Dešťový senzor
Nastaví typ spínače dešťového senzoru. Pokud používáte Raspberry Pi a chcete připojit senzor deště přímo k pinům GPIO, použijte piny 8 a 6 (gnd).

### Používat senzor
Zaškrtnutím políčka "Používat senzor" povolíme snímání deště.

### V klidu rozpojen
Zaškrtněte políčko "V klidu rozpojen", pokud je senzor bez deště normálně rozpojený, jinak políčko zrušte. Informace o typu spínače najdete v uživatelské příručce dešťového senzoru.

## Protokolování
Zapněte protokolování běhu a nastavte počet záznamů, které chcete zachovat. Zapněte protokolování odeslaných e-mailů a nastavte počet záznamů, které chcete uchovávat.
  
### Aktivovat záznam
Zaškrtněte políčko "Aktivovat záznam". Tím se zapne protokolování a zapne se historie zavlažování na časové ose na domovské stránce. Zaznamenávat všechny běhy stanic - berte na vědomí, že opakující se psaní na SD kartu může zkrátit její životnost.

### Max záznamů
Zadejte počet záznamů, které chcete uložit do protokolu. Nastavte počet, který pokryje přiměřenou dobu, například týden nebo měsíc. To bude záviset na počtu programů a stanic, které máte. Při každém spuštění stanice bude existovat jeden záznam. 0 = bez omezení.

### Aktivovat záznam E-mailů
Zaškrtněte políčko "Aktivovat záznam E-mailů". Tím se zapne protokolování a povolí se historie zavlažování prostřednictvím E-mailu.

### Max záznamů
Zadejte počet záznamů, které chcete uložit do protokolu. Nastavte počet, který pokryje přiměřenou dobu, například týden nebo měsíc. To bude záviset na počtu programů a stanic, které máte. Pro každý E-mail bude existovat jeden záznam. 0 = bez omezení.

### Povolit ladění
Klepnutím na "Povolit ladění" uložíte veškeré interní operace v OSPy do souboru pro lepší ladění. * Poznámka: * příliš časté ukládání dat do souboru může po delší době poškodit SD kartu nebo snížit kapacitu SD karty (úložiště). Vypisují se veškeré operace (i ze všech rozšíření).

## Restartovat systém
Sekce "Restart systému" obsahuje tlačítka pro restartování softwaru, pro restartování hardwaru, pro vypnutí hardwaru a vymazání všech nastavení na výchozí hodnoty.

### Restart OSPy
Tlačítko "Restart OSPy" restartuje pouze software. Je to rychlý vynucený způsob, jak implementovat změny v softwaru.

### Restart HW
Tlačítko "Restart HW" restartuje Raspberry Pi. To trvá déle, ale provede úplný restart systému.

### Vypnout
Tlačítko "Vypnout" vypíná napájení Raspberry Pi hardwaru.

### Smazat nastavení 
Tlačítko "Smazat nastavení" vymaže všechna uživatelská nastavení do výchozí čisté instalace OSPy. 
* Veškerá nastavení se dají v OSPy smazat i ručně (v systému nalezneme složky ospy/data a ve složce smažeme všechny soubory).

## Záloha a obnovení
Pokud chceme zálohovat všechna nastavení našeho OSPy zavlažovacího systému nebo přenést nastavení do jiného OSPy systému, použijeme tlačítko "Stáhnout" a následně "Nahrát".

### Stáhnout
Tlačítko "Stáhnout" se používá ke stažení konfiguračního souboru do počítače pro pozdější použití nebo k obnovení systému OSPy. Stažený název souboru je "options.db". Toto jméno neměňte!

### Nahrát 
Tlačítko "Nahrát" umožňuje vložit a obnovit systém OSPy ze zálohy, nebo jiného OSPy systému (například při přeinstalování systému Linux). Nahraný soubor s názvem "options.db". Toto jméno neměňte!

## Certifikát SSL
Pokud máme svůj vlastní certifikát pro SSL (https) zabezpečení (fullchain.pem a privkey.pem) můžeme ho zde pomocí formuláře nahrát.

## Generovat
Pokud chceme vygenerovat SSL certifikát, stiskneme tlačítko "generovat". Do adresáře ssl se vygeneruje certifikát. Následně v nastavení/bezpečnost zaškrtneme možnost "vlastní HTTPS" a následně restartujeme OSPy.

### Nahrát
Tlačítko "Nahrát" odešle do složky ssl v adresáři OSPy přiložené soubory (fullchain.pem a privkey.pem).

----

# Stanice
<a href="https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Web%20Interface%20Guide%20-%20Czech/stanice.png" rel="Stanice" target="_blank">![Stanice - obrázek](https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Web%20Interface%20Guide%20-%20Czech/stanice.png)</a>

Na stránce "Stanice" nastavujeme nazvy stanic, vlastnosti okolo využívání množství vody, ovládání hlavních stanic.

## Stanice 
Automatické číslování k označení stanic. Například 1 = stanice 1, 2 = stanice 2...

## Jméno
Uživatelské pojmenování stanic pro lepší identifikaci v systému, například "trávník".

## Využití
Nastavení souběhu (0), nebo sekvence (>=1) pro určité stanice. Více o souběhu, nebo sekvenci v textu výše v sekci "Nastavení / O sekvenčních a souběžných režimech".

## Závlaha
Množství vody za hodinu v mm, které rozpráší rozstřikovače na dané stanici. Používá se pro programy založené na počasí. Pro změření této hodnoty je vhodné si pořídit například plastový srážkoměr.
<a href="https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Web%20Interface%20Guide%20-%20Czech/srazkomer.png" rel="plastový srážkoměr" target="_blank">![plastový srážkoměr - obrázek](https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Web%20Interface%20Guide%20-%20Czech/srazkomer.png)</a>

* Vztahuje se na čas potřebný k infiltraci daného množství vody do konkrétního typu půdy. Obecně je rychlost příjmu lehčí texturované (písčité) půdy vyšší než rychlost těžší texturované (jílovité) půdy. Zavlažování postřikovačů velkým množstvím vody však může vést k povrchovému odtoku i na písčitých půdách. Rychlost příjmu půdy pod zavlažováním je ovlivněna mnoha faktory, jako je struktura půdy, struktura půdy, zhutnění, organická hmota, stratifikované půdy, soli v půdě, kvalita vody, sedimenty ve zavlažovací vodě atd.

## Zásoba
Množství vody, které může půda uložit nad úroveň 0. Používá se pro programy založené na počasí.

* Vztahuje se na množství půdní vlhkosti nebo obsahu vody zadržené v půdě po odtoku přebytečné vody a snížení rychlosti pohybu dolů. K tomu obvykle dochází 2–3 dny po dešti nebo zavlažování v předchozích půdách s jednotnou strukturou a strukturou.

## ETo faktor
Faktor používaný k násobení faktoru ETo pro programy založené na počasí. Použijte hodnotu vyšší než 1 v případě slunečné/suché půdy, použijte hodnotu nižší než 1 pro stín/vlhkou půdu.

* Typ půdy

Půdy mají různé vlastnosti, díky nimž jsou jedinečné. Znát druh půdy, kterou máte, vám pomůže určit její silné a slabé stránky. Zatímco půda se skládá z mnoha prvků, místo, kde začít, je s vaším typem půdy. Musíte pouze sledovat složení půdních částic. OSPy umožňuje uživatelům určit typ půdy pro každou zónu (stanici), což umožňuje přesnější a efektivnější výpočty zalévání. Různé typy půdy reagují odlišně na vodu; jílovité půdy mají sklon k odtoku, zatímco hlinité půdy mohou zadržovat vodu po dlouhou dobu atd. Množství vody obsažené v půdě po odtoku přebytečné vody a schopnost půdy zadržovat vodu se označuje jako kapacita pole (měřeno v palcích nebo milimetrech).

### Test pomocí láhve
Jak najít přibližné proporce písku, bahna a jílu? Toto je jednoduchý test, který vám dá obecnou představu o podílech písku, bahna a jílu přítomného v půdě. Vložte 5 cm půdy do láhve a naplňte ji vodou. 	
Vodu a půdu dobře promíchejte, odložte láhev a nedotýkejte se jí hodinu. Po hodině se voda vyčeří a uvidíte, že se větší částice usadily: 	

- Na hladině vody se mohou vznášet kousky organické hmoty
- Nahoře je vrstva hlíny.
Pokud voda stále není čirá, je to proto, že některé z nejjemnějších jílů jsou stále smíchány s vodou
- Uprostřed je vrstva bahna
- Ve spodní části je vrstva písku

* Změřte hloubku písku, bahna a jílu a odhadněte jejich přibližný poměr.

Následující tři typy částic mohou tvořit vaši půdu: jíl, písek a bahno. Většina půd je kombinací těchto tří částic, ale typ částic, který dominuje, diktuje mnoho vlastností vaší půdy. Poměr těchto velikostí určuje typ půdy: jíl, hlína, jílovitá hlína, bahno-hlína atd.

* Ideální půda je 40% písku, 40% bahna a 20% jílu. Tato směs se označuje jako hlinitá. To bere to nejlepší z každého typu částic půdy. Má dobrou drenáž vody a umožňuje vzduchu proniknout do půdy jako písek, ale také dobře udržuje vlhkost a je úrodná jako bahno a hlína. 

## Zůstatek
Zvýšení nebo snížení vodní bilance pro programy založené na počasí (pokud není nastaveno na 0).

## Připojeno
Pokud máme stanici zapojenou (je fyzicky připojena) a chceme ji využívat (je vidět ve výběru v programech, na domovské stránce...), zaškrtneme "Připojeno". Pokud stanici nevyužíváme a nechceme zveřejnit v systému OSPy ponecháme "Připojeno" nezaškrtlé. Pokud je v systému použita některá stanice jako "hlavní stanice" nebo "2 hlavní stanice", tak ji v tabulce nelze zaškrtnout ani odškrtnout (deaktivovat). 
Hlavní stanice se přiřazuje v nastavení systému "Nastavení / nastavení hlavní stanice".

## Ignorovat Déšť
Pokud u některé stanice zaškrtneme "Ignorovat Déšť", tak se stanice aktivuje dle programu bez ohledu zda je nastaveno dešťové zpoždění, nebo zda dešťový senzor detekuje déšť. Tuto možnost využijeme například ve skleníku, do kterého neprší a potřebujeme zavlažovat pravidelně. nebo například ke spouštění filtrace bazénu, který také čistíme bez ohledu zda prší.

## ZAP Hlavní
Pokud požadujeme, aby když se aktivuje určitá stanice se aktivovala i hlavní stanice (například čerpadlo, nebo hlavní ventil s vodou) zaškrtneme okénko "ZAP hlavní?".

## ZAP Hlavní 2
Pokud požadujeme, aby když se aktivuje určitá stanice se aktivovala i druhá hlavní stanice (například druhé čerpadlo, nebo jiný zdroj vody) zaškrtneme okénko "ZAP hlavní 2?".

## Poznámky  
Poznámky slouží pro obsluhu systému OSPy. Lze si například poznamenat: jaký typ el. ventilu, rozstřikovače atd. máme v systému použitý.

----

#  Nápověda
<a href="https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Web%20Interface%20Guide%20-%20Czech/napoveda.png" rel="Nápověda" target="_blank">![Nápověda - obrázek](https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Web%20Interface%20Guide%20-%20Czech/napoveda.png)</a>

Na stránce "Nápověda" nalezneme dokumentaci ke všem rozšířením, OSPy systému, změny v systému, přístup pomocí API, webové rozhraní.

## OSPy
### Readme
Hlavní dokumentace k OSPy, instalace systému, propojení desky, licence.

### Changelog
Změny v systému OSPy, nebo v rozšířeních

### Programs
Interně všechny programy udržují plán, který lze přímo upravit (stejně jako vlastní program).
Pro snadnější manipulaci byly vytvořeny následující typy programů.
Každý program může být jedním z těchto typů. Nakonec lze každý program napsat také jako vlastní program.<br/>

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
Nápověda k webovému rozhraní v češtině.

### Web Interface Guide - English
Nápověda k webovému rozhraní v angličtině.

## API
### Readme
Pro moderní webové prohlížeče se doporučuje, aby rozhraní API bylo postaveno na principu CRUD pomocí formátu JSON jako formátu datových kontejnerů.

### Details
Mapování metod HTTP/s.

## Rozšíření
Základní struktura všech rozšíření je následující:

plugins
+ plugin_name
  + data
  + docs
  + static
  + templates
  + __init__.py
  \ README.md

Statické soubory budou automaticky zpřístupněny na následujícím místě: /plugins/název_pluginu/static/...
Všechny * .md soubory v adresáři docs budou viditelné na stránce "Nápověda". *

### Dostupná rozšíření:

* Usage Statistics (anonymní statistiky o používání OSPy systému)
* LCD Display (LCD displej 16x2 znaků připojený pomocí I2C sběrnice)
* Pressure Monitor (hlídání tlaku v potrubí - ochrana čerpadla)
* Voice Notification (zvuková upozornění - přehrávání souborů mp3)
* Pulse Output Test (test výstupů - slouží k nalezení určitého ventilu v zemi)
* Button Control (ovládání systému OSPy pomocí 8 tlačítek - slouží pro ruční spouštění programů)
* CLI Control (vzdálené ovládání periferií pomocí URL příkazů - například RF zásuvky)
* System Watchdog (hlídací pes systému Raspberry Pi, pokud systém zamrzne, dojde k restartu systému)
* Voltage and Temperature Monitor (měření napětí a teploty pomocí I2C sběrnice)
* Remote Notifications (odesílání dat na vzdálený server pomocí PHP)
* System Information (systémové informace OSPy a systém Linux)
* MQTT (hlášení stavu OSPy pomocí MQTT protokolu - toto rozšíření využívají i některá jiná rozšíření, například: MQTT Zone Broadcaster)
* Air Temperature and Humidity Monitor (měření teploty 6x DS18B20 a vlhkosti DHT11 pomocí I2C sběrnice)
* Wind Speed Monitor (měření rychlosti větru pomocí I2C sběrnice)
* Weather-based Rain Delay (dešťové zpoždění založené na předpovědi počasí)
* Relay Test (testuje relé pro hlavní čerpadlo)
* UPS Monitor (hlídá výpadek napájení systému, odesílá email a ukončuje Linux systém)
* Water Consumption Counter (virtuální měřič průtoku vody založený na výpočtu běhu hlavní stanice)
* SMS Modem (vzdálené ovládání pomocí SMS a USB modemu)
* Signaling Examples (příklad notifikací tupu "signal" v systému OSPy)
* E-mail Notifications (odesílání E-mailů ze systému - toto rozšíření využívají i některá jiná rozšíření, například: Wind Speed Monitor, Pressure Monitor, Air Temperature and Humidity Monitor...)
* Remote FTP Control (zjednodušené vzdálené ovládání OSPy pomocí serveru s PHP a FTP)
* System Update (pomocí tohoto rozšíření lze jednoduše aktualizovat systém OSPy z GIThubu namísto systémových příkazů)
* Water Meter (měření průtoku pomocí vodoměru s pulsním výstupem pomocí I2C sběrnice)
* Webcam Monitor (pořizuje fotografie z USB webkamery)
* Weather-based Water Level Netatmo (nastavení množství vody pro zavlažování z meteostanice Netatmo)
* Direct 16 Relay Outputs (pomocí tohoto rozšíření můžeme ovládat 16 relé (stanic) připojených přímo k Raspberry Pi, ovšem některá ostatní rozšíření nebudou dostupná)
* MQTT Zone Broadcaster (hlášení stavů stanic pomocí MQTT protokolu)
* MQTT Slave (vzdálené ovládání podřízených zalévačů přes MQTT protokol)
* System Debug Information (informace o dění v systému OSPy, pokud máme v nastavení povolen debug "Povolit ladění", tak zde v rozšíření se zobrazuje uložený záznam)
* Weather-based Water Level (nastavení množství vody pro zavlažování založený na předpovědi počasí)
* Real Time and NTP time (rozšíření, které nastavuje systémový čas - Linux a HW RTC čas z NTP serveru, HW RTC používá I2C sběrnici)
* Water Tank (měření hladiny vody pomocí ultrazvuku - například ve studni pomocí I2C sběrnice)
* Humidity Monitor (měření vlhkosti půdy, používá I2C sběrnici)
* Monthly Water Level (nastavení množství vody pro jednotlivé měsíce)
* Pressurizer (tlakování čerpadla před spuštěním programů)
* Ping monitor (měření výpadků sítě)
* Temperature Switch (regulátor teploty, který umožnuje 3 nezávislé zóny)
* Pool Heating (regulace teploty bazénu dle solárního ohřevu)
* E-mail reader (ovládání OSPy pomocí E-mailových zpráv)

----

# Odhlásit se
Po kliknutí na tlačítko "Odhlásit se" se uživatel odhlásí ze systému.
