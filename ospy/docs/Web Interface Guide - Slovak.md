OSPy Web Interface Guide in Slovak
====

    Inštalácia OSPy
    Prihlásenie
    Domovská stránka
    Programy
        Pridať nový program
        Skupiny programov
        Spustiť teraz
        Upraviť
        Kopírovať
        Vymazať všetko
        Zap/Vyp program
        Upozornenia na kolízie
        Typ plánovača
    Jednorazovo
    Rozšírenia
        Spravovať
        Inštalovať nové rozšírenie
        Vypnúť všetko
        Zapnúť všetko
        Povoliť kontrolu aktualizácií
        Načítať zmeny
        Zmeny
        Automatické aktualizácie
    Záznam
    Nastavenia
        Systém
        Počasie
        Používatelia
        Bezpečnosť
        Snímače
        Stanice
        Hlavná stanica
        Dažďový senzor
        Protokolovanie
        Reštart systému
        Záloha a obnovenie
        SSL certifikát
    Stanice
    Snímače
    Nápoveda
    Odhlásenie

----

# Inštalácia OSPy

OSPy je možné nainštalovať podľa hlavného súboru Readme. Odporúčaný spôsob je použiť inštalačný skript pre Raspberry Pi a po inštalácii skontrolovať nastavenie siete, používateľa a hesla.

## Pomocou inštalačného skriptu

Postup inštalácie, zapojenie dosiek a ďalšie technické informácie sú popísané v hlavnej dokumentácii OSPy.

----

# Prihlásenie

Po otvorení webového rozhrania zadajte používateľské meno a heslo. Pri novej inštalácii je predvolené meno a heslo `admin`. Z bezpečnostných dôvodov odporúčame predvolené prihlasovacie údaje zmeniť.

----

# Domovská stránka

Domovská stránka zobrazuje aktuálny stav systému, stav plánovača, dažďové oneskorenie, informácie o staniciach, senzory, grafy a základné systémové údaje.

## Normálne - stav vody

Zobrazuje aktuálnu úpravu zavlažovania podľa nastavení, počasia alebo rozšírení.

## Aktívne - oneskorenie dažďom

Informuje, či je aktívne oneskorenie spôsobené dažďom.

## Plánovač - ručne

Ukazuje, či je plánovač spustený automaticky alebo či je systém v ručnom režime.

## Povolené - zakázané

Zobrazuje celkový stav systému. Ak je systém zakázaný, plánované programy sa nespúšťajú.

## Zastaviť všetky stanice

Tlačidlo zastaví všetky aktuálne bežiace stanice.

## Graf vodnej bilancie

Graf zobrazuje vývoj vodnej bilancie podľa nastavení staníc a použitých dát.

## Systémové informácie

Domovská stránka môže zobrazovať teplotu CPU, využitie CPU, verziu softvéru, externú IP adresu a dobu behu systému.

----

# Programy

Stránka Programy slúži na vytváranie, úpravu, spúšťanie a organizovanie zavlažovacích programov.

## Pridať nový program

Tlačidlom "Pridať nový program" vytvoríte nový program plánovača.

## Skupiny programov

Programy je možné usporiadať do rozbaľovacích skupín. Skupiny sú vhodné napríklad na oddelenie letných a zimných programov alebo na rozdelenie podľa častí záhrady.

## Pridať skupinu

Tlačidlom "Pridať skupinu" vytvoríte novú skupinu programov.

## Premenovať skupinu

Premenovanie zmení iba názov skupiny. Programy priradené do skupiny zostanú zachované.

## Zap/Vyp skupinu

Akcia ZAP/VYP pri skupine povolí alebo zakáže všetky programy v danej skupine naraz. Je vhodná na sezónne prepínanie väčšieho počtu programov.

## Kopírovať skupinu

Kopírovanie vytvorí novú skupinu a skopíruje do nej programy z pôvodnej skupiny. Skopírované programy sú vytvorené ako zakázané, aby sa nespustili skôr, než ich skontrolujete.

## Vymazať skupinu

Vymazanie skupiny vyžaduje potvrdenie. Programy zo zmazanej skupiny sa presunú do predvolenej skupiny.

## Spustiť teraz

Tlačidlo "Spustiť teraz" spustí vybraný program okamžite, bez ohľadu na dátum a čas plánovača.

## Upraviť

Tlačidlo "Upraviť" otvorí nastavenia existujúceho programu.

## Kopírovať

Tlačidlo "Kopírovať" vytvorí kópiu vybraného programu. Kópia je predvolene zakázaná, takže ju môžete pred použitím bezpečne upraviť.

## Presunúť do skupiny

Program je možné priradiť do skupiny na stránke úpravy programu. Tým sa zmení iba jeho umiestnenie na stránke Programy.

## Vymazať všetko

Tlačidlo "Vymazať všetko" odstráni po potvrdení všetky existujúce programy.

## Zap/Vyp program

Prepínač "ZAP/VYP" povolí alebo zakáže konkrétny program v plánovači.

## Upozornenia na kolízie

Pri uložení programu OSPy kontroluje povolené programy a hľadá prekryvy plánovaného behu na rovnakej stanici/výstupe. Ak je v rovnakom čase naplánovaný iný program, stránka Programy zobrazí upozornenie s dobou prekryvu. Je to iba upozornenie; program sa automaticky nezablokuje ani neupraví.

## Typ plánovača

Typ plánovača určuje spôsob spúšťania programu. Dostupné režimy zahŕňajú vybrané dni, opakovanie, týždenný plán, vlastný plán a programy založené na predpovedi počasia.

### Vybrané dni

Program sa spúšťa vo vybraných dňoch podľa nastaveného času, trvania a prípadného opakovania.

### Opakovanie

Program sa opakuje podľa intervalu zavlažovania a počiatočného dňa.

### Týždenný plán

Program používa samostatné nastavenie pre dni v týždni.

### Vlastný plán

Vlastný plán umožňuje pokročilé nastavenie dní a behov programu.

### Týždenný plán podľa počasia

Program môže upravovať zavlažovanie podľa údajov z predpovede počasia a nastavených limitov.

## Bez úprav

Na program sa nepoužijú žiadne dodatočné úpravy času behu.

## Odrezať

Ak by upravený čas behu programu bol kratší než nastavený limit, program sa preskočí. Hodnota sa nastavuje v percentách.

## Aktivovať hlavnú stanicu

Stanice, ktoré majú nastavenú možnosť "Aktivovať Master 1/2 programom", aktivujú hlavnú stanicu podľa priradenia v programe.

----

# Jednorazovo

Stránka Jednorazovo umožňuje spustiť vybrané stanice na zadaný čas mimo plánovača. Je vhodná na testovanie alebo dodatočné zavlažovanie.

## Spustiť teraz

Spustí všetky stanice, pri ktorých je zadaný čas.

## Vymazať čas

Odstráni prednastavené časy pre všetky stanice.

----

# Rozšírenia

Stránka Rozšírenia slúži na správu doplnkov systému OSPy.

## Spravovať

Otvorí správcu rozšírení, kde je možné rozšírenia zapínať, vypínať, inštalovať a aktualizovať.

## Inštalovať nové rozšírenie

Otvorí zoznam dostupných rozšírení zo vzdialeného repozitára.

### Vlastné rozšírenie (ZIP)

Umožňuje nainštalovať vlastné rozšírenie zo súboru ZIP. Súbor musí obsahovať kompletnú štruktúru rozšírenia.

### Github

Predvolený repozitár rozšírení je `https://github.com/martinpihrt/OSPy-plugins/archive/master.zip`.

## Vypnúť všetko

Zakáže všetky nainštalované rozšírenia.

## Zapnúť všetko

Povolí všetky nainštalované rozšírenia.

## Povoliť kontrolu aktualizácií

Ak je voľba aktívna, OSPy pravidelne kontroluje dostupnosť nových verzií rozšírení.

## Načítať zmeny

Načíta najnovší zoznam dostupných zmien zo vzdialeného repozitára rozšírení.

## Zmeny

Otvorí prehľad dostupných zmien rozšírení a informácií k aktualizáciám.

## Automatické aktualizácie

Ak je voľba aktívna, dostupné nové verzie rozšírení sa aktualizujú automaticky. Odporúča sa najskôr aktualizovať OSPy a až potom rozšírenia.

----

# Záznam

Stránka Záznam zobrazuje protokoly systému. Počet záznamov sa nastavuje na stránke Nastavenia.

## Stiahnuť záznam ako

Umožňuje stiahnuť záznam zavlažovania ako súbor CSV.

## Vymazať záznam

Vymaže záznam po potvrdení.

## Vymazať záznam e-mailov

Vymaže e-mailový záznam po potvrdení.

----

# Nastavenia

Stránka Nastavenia obsahuje hlavné nastavenia systému OSPy.

## Systém

V tejto sekcii sa nastavuje názov systému, téma webu, formát času, jazyk, HTTP/S adresa, port a zobrazenie doplnkov alebo snímačov na domovskej stránke.

## Počasie

Sekcia počasia nastavuje použitie služby Stormglass, API kľúč a polohu.

## Používatelia

Z bezpečnostných dôvodov odporúčame zmeniť predvolené používateľské meno a heslo. Prístup bez hesla povoľte iba vtedy, keď je systém chránený iným bezpečným spôsobom.

## Bezpečnosť

Sekcia Bezpečnosť obsahuje nastavenia HTTPS a certifikátov.

### Ochrana formulárov

Akcie, ktoré menia nastavenia alebo stav systému, sú vo webovom rozhraní chránené tokenom formulára. Ak je stránka otvorená dlho alebo vyprší relácia v prehliadači, načítajte stránku znova a akciu zopakujte.

### Použiť HTTPS

Ak je server správne pripravený na HTTPS, táto voľba zapne zabezpečený prístup.

### Doménové meno

Doménové meno sa používa pri certifikáte vytvorenom pomocou Certbotu.

### Použiť vlastné HTTPS

Pri vlastnom certifikáte vložte súbory `fullchain.pem` a `privkey.pem` do priečinka `ssl` v inštalácii OSPy a reštartujte OSPy.

## Snímače

Sekcia obsahuje heslo používané pri nahrávaní firmvéru do snímačov.

## Stanice

Nastavuje maximálne využitie, počet výstupov, pauzu medzi stanicami a minimálny čas behu. Maximálne využitie určuje, či môžu stanice bežať súčasne. Hodnota `0` znamená bez obmedzenia, hodnota `1` znamená jednu stanicu naraz, ak má každá stanica využitie `1`.

Pauza medzi stanicami je čas vložený medzi postupne spúšťané stanice, keď ich plánovač nemôže spustiť súčasne. Neposúva stanicu voči hlavnej stanici. Príklad: pri maximálnom využití `1` a využití stanice `1` hodnota `30` spustí ďalšiu stanicu 30 sekúnd po skončení predchádzajúcej stanice.

Minimálny čas behu môže túto pauzu preskočiť, ak predchádzajúci beh trval kratšie. Príklad: pri pauze `30` a minimálnom čase behu `10` stanica, ktorá bežala iba 5 sekúnd, nevynúti 30-sekundovú pauzu.

## Hlavná stanica

Nastavuje hlavnú stanicu 1, hlavnú stanicu 2 a časové posuny ich zapnutia alebo vypnutia. Hlavná stanica je zvyčajne čerpadlo alebo hlavný ventil vody a použije sa iba pri staniciach, ktoré ju majú priradenú.

Posun štartu hlavnej stanice je relatívny k štartu stanice. Záporná hodnota spustí hlavnú stanicu skôr, kladná neskôr. Príklad: `-10` spustí hlavnú stanicu 10 sekúnd pred stanicou, `+10` ju spustí 10 sekúnd po stanici.

Posun vypnutia hlavnej stanice je relatívny ku koncu stanice. Záporná hodnota vypne hlavnú stanicu skôr, kladná ju nechá bežať dlhšie. Príklad: `-5` vypne hlavnú stanicu 5 sekúnd pred koncom stanice, `+20` ju vypne 20 sekúnd po konci stanice.

Rovnaká logika platí aj pre hlavnú stanicu 2, ktorá má vlastné nastavenia posunu štartu a vypnutia.

## Dažďový senzor

Nastavuje použitie dažďového senzora, jeho stav v pokoji a oneskorenie po daždi.

## Protokolovanie

Nastavuje záznam behov, e-mailov, udalostí a ladenia.

## Reštart systému

Obsahuje akcie na reštart OSPy, reštart hardvéru, vypnutie systému a obnovenie predvolených nastavení.

## Záloha a obnovenie

Umožňuje stiahnuť alebo nahrať zálohu nastavení.

## SSL certifikát

Umožňuje vygenerovať alebo nahrať súbory certifikátu.

----

# Stanice

Stránka Stanice slúži na pomenovanie a nastavenie jednotlivých výstupov. Pre každú stanicu je možné nastaviť využitie, zrážky, kapacitu, ETo faktor, vodnú bilanciu, pripojenie, ignorovanie dažďa, použitie hlavnej stanice, poznámku a obrázok.

----

# Snímače

Stránka Snímače umožňuje pridať, nastaviť a odstrániť snímače používané systémom OSPy. Pri snímači je možné nastaviť názov, typ, komunikáciu, frekvenciu vzorkovania, záznam vzoriek, záznam udalostí a notifikácie.

----

# Nápoveda

Stránka Nápoveda obsahuje dokumentáciu systému OSPy, API a rozšírení.

## OSPy

### Readme

Hlavná dokumentácia k systému OSPy, inštalácii, zapojeniu a licencii.

### Changelog

Prehľad zmien systému OSPy a rozšírení.

### Programs

Technická dokumentácia k programom a plánovaču.

### Web Interface Guide - Czech

Nápoveda k webovému rozhraniu v češtine.

### Web Interface Guide - English

Nápoveda k webovému rozhraniu v angličtine.

### Web Interface Guide - German

Nápoveda k webovému rozhraniu v nemčine.

### Web Interface Guide - Polish

Nápoveda k webovému rozhraniu v poľštine.

### Web Interface Guide - Russian

Nápoveda k webovému rozhraniu v ruštine.

### Web Interface Guide - Serbian

Nápoveda k webovému rozhraniu v srbčine.

### Web Interface Guide - Slovak

Nápoveda k webovému rozhraniu v slovenčine.

## API

Dokumentácia k API popisuje rozhranie pre komunikáciu so systémom OSPy.

## Rozšírenia

Dokumentácia rozšírení popisuje dostupné doplnky, ich nastavenie a použitie.

----

# Odhlásenie

Tlačidlo na odhlásenie ukončí aktuálnu používateľskú reláciu vo webovom rozhraní.
