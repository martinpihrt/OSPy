OSPy vodic za web interfejs na srpskom
====

    Instalacija OSPy
    Prijava
    Pocetna strana
    Programi
    Jednokratno pokretanje
    Dodaci
    Dnevnik
    Podesavanja
    Stanice
    Senzori
    Pomoc
    Odjava

----

# Instalacija OSPy
Preporucuje se cista instalacija sa aktuelnom verzijom Python 3. Pri prvom pokretanju OSPy generise podatke za prijavu. Posle prve prijave potrebno je promeniti lozinku i po potrebi korisnicko ime u podesavanjima.

## Instalacioni skript
Prijavite se na Raspberry Pi preko SSH i pokrenite:

```bash
wget https://raw.githubusercontent.com/martinpihrt/OSPy/master/ospy_setup.sh
sudo bash ospy_setup.sh
```

Posle instalacije Raspberry Pi se restartuje i OSPy je spreman za podesavanje kroz web pregledač.

----

# Prijava
Strana za prijavu sadrzi polja za korisnicko ime i lozinku. Podrazumevani korisnik je `admin`. Kod nove instalacije generise se nasumicna lozinka koju treba zameniti.

----

# Pocetna strana
Pocetna strana je glavni kontrolni centar. Prikazuje sat, navigaciju, globalne komande, vremensku liniju, grafikone, sistemske informacije i elemente koje dodaju dodaci.

## Normalno - nivo vode
Podesava globalni procenat vode koji menja vreme rada programa.

## Aktivno - odlaganje zbog kise
Privremeno zaustavlja zalivanje za stanice koje ne ignorisu kisu.

## Raspored - rucno
Prebacuje sistem izmedju automatskog rasporeda i rucnog upravljanja stanicama.

## Omoguceno - onemoguceno
Upravlja ukupnim radom OSPy softvera.

## Zaustavi sve stanice
Odmah zaustavlja pokrenut program ili stanicu.

## Grafikon bilansa vode
Prikazuje kolicinu vode isporucenu po stanicama ili programima.

## Odlaganje zbog kise / detektovana kisa
Kada su odlaganje ili senzor kise aktivni, odgovarajuce stanice su blokirane.

## Sistemske informacije
Podnozje prikazuje temperaturu CPU, opterecenje CPU, verziju softvera, spoljasnju IP adresu i vreme rada.

----

# Programi
Strana Programi sluzi za kreiranje, organizovanje i upravljanje rasporedima zalivanja.

## Dodaj novi program
Kreira novi program rasporeda.

## Grupe programa
Programi mogu biti organizovani u sklopive grupe, na primer letnji i zimski programi.

## Dodaj grupu
Kreira novu grupu programa.

## Preimenuj grupu
Menja samo naziv grupe. Programi u grupi ostaju isti.

## Omoguci ili onemoguci grupu
Ukljucuje ili iskljucuje sve programe u grupi odjednom.

## Kopiraj grupu
Kreira kopiju grupe i njenih programa. Kopirani programi su podrazumevano iskljuceni.

## Obrisi grupu
Brisanje trazi potvrdu. Programi iz obrisane grupe premestaju se u podrazumevanu grupu.

## Pokreni sada
Odmah pokrece program, bez obzira na raspored.

## Izmeni
Otvara parametre postojeceg programa.

## Kopiraj
Kreira iskljucenu kopiju programa za bezbednu izmenu.

## Premesti u grupu
Dodeljuje program izabranoj grupi.

## Obrisi sve
Posle potvrde brise sve programe.

## Omoguci ili onemoguci program
ON/OFF prekidac ukljucuje ili iskljucuje pojedinacni program.

## Upozorenja o konfliktima
Prilikom cuvanja OSPy proverava da li se ukljuceni programi vremenski preklapaju na istoj stanici ili izlazu. Upozorenje ne blokira program automatski.

## Tip rasporeda
Dostupni su izabrani dani, ponavljanje, nedeljni rezim, prilagodjeni rezim i programi zasnovani na vremenskoj prognozi.

## Bez korekcija
Za ovaj program se ne primenjuju automatske izmene vremena rada.

## Granica skracivanja
Ako je korigovano vreme rada krace od zadate granice, program se preskace.

## Aktiviraj master
Stanice podesene na master po programu koriste master stanicu izabranu u programu.

----

# Jednokratno pokretanje
Ova strana sluzi za testiranje ili jednokratno zalivanje. Za svaku stanicu mogu se podesiti minuti i sekunde.

## Pokreni sada
Pokrece izabrane stanice.

## Resetuj vreme
Brise zadata vremena.

----

# Dodaci
Strana dodataka sluzi za upravljanje pluginima.

## Upravljanje
Otvara menadzer dodataka gde se pluginovi ukljucuju, iskljucuju, instaliraju i azuriraju.

## Instaliraj novi dodatak
Prikazuje dostupne dodatke iz repozitorijuma.

## Sopstveni plugin ZIP
Instalira plugin iz ZIP datoteke. Datoteka mora sadrzati kompletnu strukturu plugina.

## Iskljuci sve / Ukljuci sve
Upravlja svim instaliranim dodacima odjednom.

## Provera azuriranja
Automatski proverava da li postoje nove verzije pluginova.

## Ucitaj izmene / Izmene
Ucitajte i prikazite najnovije izmene iz repozitorijuma pluginova.

## Automatska azuriranja
Ako je ukljuceno, pluginovi se automatski azuriraju. Prvo treba azurirati OSPy, zatim dodatke.

----

# Dnevnik
Strana dnevnika prikazuje zapise zalivanja, e-mailova i dogadjaja. Zapisi se mogu preuzeti kao CSV ili obrisati. Brisanje je nepovratno.

----

# Podesavanja
Podesavanja su podeljena na sekcije: sistem, vreme, korisnici, bezbednost, senzori, stanice, master stanice, senzor kise, logovanje, restart, backup i SSL.

## Sistem
Naziv sistema, tema, format sata, HTTP/S adresa i port, jezik, slike stanica i prikaz dodataka ili senzora na pocetnoj strani.

## Vreme
Ukljucuje vremenske funkcije, API kljuc i lokaciju.

## Korisnici
Upravlja prijavom, lozinkom i dodatnim korisnicima.

## Bezbednost
Obuhvata zastitu formulara, HTTPS, ime domena i sopstvene sertifikate.

## Senzori
Postavlja lozinku za slanje firmware-a na senzore.

## Obrada stanica
Podesava maksimalnu upotrebu, broj izlaza, kasnjenje stanica i minimalno vreme rada.

## Master stanice
Konfigurise prvu i drugu master stanicu i kasnjenja ukljucenja ili iskljucenja.

## Senzor kise
Ukljucuje senzor kise, tip kontakta i odlaganje posle kise.

## Logovanje
Ukljucuje logove rada, e-mailova, dogadjaja i debug log.

## Restart sistema
Omogucava restart softvera, restart Raspberry Pi, gasenje ili vracanje podrazumevanih podesavanja.

## Backup sistema
Omogucava preuzimanje i ucitavanje kopije konfiguracije.

## SSL sertifikat
Omogucava ucitavanje ili generisanje HTTPS sertifikata.

----

# Stanice
Strana stanica podesava naziv, upotrebu, padavine, kapacitet zemljista, ETo faktor, korekciju bilansa, povezivanje, ignorisanje kise, master, napomene i sliku.

----

# Senzori
Na strani senzora mogu se dodavati i brisati senzori. Podrzani su radio i mrezni senzori i tipovi kao sto su suvi kontakt, curenje, vlaznost, pokret, temperatura, ultrazvuk i vlaznost zemljista.

## Shelly senzori
Shelly uredjaji mogu se povezati preko Shelly Cloud Integration plugina i koristiti u OSPy.

----

# Pomoc
Strana pomoci sadrzi dokumentaciju za OSPy, API, hardver i pluginove. Markdown datoteke iz dokumentacionih foldera prikazuju se automatski.

----

# Odjava
Dugme za odjavu zavrsava trenutnu web sesiju.

----
