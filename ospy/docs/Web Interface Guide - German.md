OSPy Webinterface-Anleitung auf Deutsch
====

    OSPy-Installation
    Anmelden
    Startseite
        Normal – % der Programmzeit
        Aktiv – Regenverzögerung
        Planer – Handbuch
        Aktiviert – Deaktiviert
        Stoppen Sie alle Stationen
        Bewässerungsstatistik (Grafik)
        Unterdrückt durch Regenverzögerung
        Regen erkannt
        CPU Temp
        CPU Nutzung
        Softwareversion
        Externe IP
        Betriebszeit
        Diagnose
    Feedback
    Programme
        Fügen Sie ein neues Programm hinzu
        Programmgruppen
        Gruppe hinzufügen
        Gruppe umbenennen
        Gruppe aktivieren oder deaktivieren
        Gruppe kopieren
        Gruppe löschen
        Jetzt ausführen
        Bearbeiten
        Kopieren
        In die Gruppe verschieben
        Alle löschen
        Programm aktivieren oder deaktivieren
        Kollisionswarnung
        Zeitplantyp
            Ausgewählte Tage (einfach)
                Startzeit
                Dauer
                Wiederholen
                Wiederholungen
                Pause
            Ausgewählte Tage (verlängert)
                Planer
            Wiederholen (einfach)
                Wasserintervall
                Beginnend in
                Startzeit
                Dauer
                Wiederholen
                Wiederholungen
                Pause
            Wiederholen (erweitert)
                Wasserintervall
                Beginnend in
                Planer
            Wöchentlich (erweitert)
                Montag-Sonntag
            Benutzerdefiniert
                Wasserintervall
                Beginnend in
                Tag 1 - Tag 7
            Wöchentlich (Wettervorhersage)
                Bewässerung min
                Bewässerung max
                Lauf max
                Pausenverhältnis
                Bevorzugte Ausführungsmomente
                    Tag
                    Startzeit
                    Priorität
                    Hinzufügen – Löschen
        Keine Anpassungen
        Abgeschnitten
        Master aktivieren
    Einmal ausführen
        Jetzt ausführen
        Zeit zurücksetzen
    Plugins
        Verwalten
        Neues Plugin installieren
            Benutzerdefiniertes Plug-in (ZIP)
            Github (https://github.com/martinpihrt/OSPy-plugins/archive/master.zip)
        Alle deaktivieren
        Alle aktivieren
        Aktivieren Sie die Überprüfung auf Updates
        Änderungen laden
        Änderungen
        Automatische Updates
    Protokoll
        Ereignisprotokoll
        Protokoll herunterladen als
        Protokoll löschen
        Datensatz E-Mail löschen
    Einstellungen
        System
            Tooltips anzeigen
            Systemname
            Systemthema
            24-Stunden-Uhr
            HTTP IP-Adresse
                Über die Portnummer
            HTTP/S port
            Plugins auf der Startseite anzeigen
            Sensoren zu Hause anzeigen
            Systemsprache
            Zeigen Sie Bilder an Stationen
        Wetter
            Verwenden Sie Wetter
            Stormglass-API-Schlüssel
            Standort
        Benutzer
            Deaktivieren Sie die Sicherheit
            Administratorname
            Aktuelles Passwort
            Neues Passwort
            Passwort bestätigen
            Zusätzliche Benutzer
        Sicherheit
            Formularschutz
            Verwenden Sie den Zugang HTTPS
            Domainname
            Verwenden Sie den eigenen HTTPS-Zugang
            API CORS-aktivierter Ursprung
            API JSONP aktivieren
            Browser-Anmeldungen gespeichert
        Sensoren
            Firmware-Upload-Passwort
        Stationen konfigurieren
            Die Verwendung von
                Über sequentielle und gleichzeitige Modi
            Anzahl der Ausgänge
            Pause zwischen Stationen
            Mindestlaufzeit
        Master konfigurieren
            Master-Station
            Master zwei Station
            Relais aktivieren
            Startversatz der Master-Station
            Stoppversatz der Master-Station
            Startversatz der Master-Station 2
            Stoppversatz der Master-Station 2
        Regensensor
            Sensor verwenden
            Normalerweise geöffnet
            Regenverzögerung einstellen
            Regenverzögerungszeit
        Protokollierung
            Laufprotokoll aktivieren
            Max. Laufeinträge
            E-Mail-Aufzeichnung aktivieren
            Max. Laufeinträge
            Ereignisprotokoll aktivieren
            Max. Laufeinträge
            Debug-Protokoll aktivieren
        Systemneustart
            Neustart
            Neustart
            Herunterfahren
            Standard
        Systemsicherung
            Herunterladen
            Hochladen
        SSL Zertifikat
            Hochladen
            Generieren
    Bahnhof
        Bahnhof
        Name
        Nutzung
        Bewässerung
        Lagerbestand
        ETo-Faktor
        Balance-Anpassung
        Verbunden
        Regen ignorieren
        ON Haupt?
            Nicht-Verwendung
            ON Haupt
            EIN Haupt 2
            EIN Hauptprogramm 1/2
        Notizen
        Bild
    Sensoren
        Fügen Sie einen neuen Sensor hinzu
            Eigenschaften von Sensoren
        Alle Sensoren löschen
    Hilfe
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

# OSPy-Installation
Wir empfehlen eine Neuinstallation mit der neuesten Version von Python 3+. Beim ersten Start von OSPy (Anmeldeseite) werden die Zugangsdaten (Passwort) für die Anmeldung am OSPy-System generiert. Nach der Anmeldung ist es notwendig, die Anmeldedaten in den Einstellungen (Optionsseite) zu ändern. Diese generierten Anmeldeinformationen werden auch im OSPy-System als Ihre Anmeldeinformationen gespeichert. Bei der nächsten Anmeldung erscheint das Fenster mit den generierten Anmeldedaten nicht mehr.

## VERWENDUNG DES INSTALLATIONSSKRIPTS
Melden Sie sich über SSH beim Pi an. Geben Sie den folgenden Befehl ein oder kopieren Sie ihn und fügen Sie ihn ein:
Denken Sie daran: Bei Raspberry Pi-Befehlen muss die Groß-/Kleinschreibung beachtet werden.
*wget https://raw.githubusercontent.com/martinpihrt/OSPy/master/ospy_setup.sh*
Und mehr

*sudo bash ospy_setup.sh*

Das OSPy-Einstellungsmenü wird angezeigt. Optional: Verwenden Sie die Pfeiltasten, um zwischen den Optionen zu wechseln. Tippen Sie auf die Leertaste, um eine Option auszuwählen oder die Auswahl aufzuheben. In den meisten Fällen werden die Standardoptionen empfohlen. Tippen Sie auf die Tabulatortaste, um zu zu wechseln. Drücken Sie die Eingabetaste und wählen Sie dann mit den Pfeiltasten den Ort aus, an dem OSPy installiert werden soll. Drücken Sie erneut die Eingabetaste, um OSPy zu installieren. Abhängig von den ausgewählten Optionen kann der Installationsvorgang mehrere Minuten dauern. Nach der Installation von OSPy erscheint ein Dialogfeld. Drücken Sie die Eingabetaste, um den Pi neu zu starten. Nach dem Neustart des Pi ist OSPy betriebsbereit und bereit, sich mit Ihrem OSPy-Bewässerungssystem zu verbinden und es gemäß Ihren Bewässerungsplänen zu programmieren. Beginnen Sie im Abschnitt „Öffnen der OSPy-Webschnittstelle“.

----

# Abmelden
Nach dem Klicken auf die Schaltfläche „Abmelden“ meldet sich der Benutzer vom System ab.

----

# Zwei-Faktor-Sicherheit (2FA)
Die Zwei-Faktor-Authentifizierung schützt das Hauptadministratorkonto durch einen zweiten Prüfschritt nach dem Passwort. Öffnen Sie **Optionen → Zwei-Faktor-Sicherheit → Konfigurieren** und wählen Sie genau eine Methode: **Authentifizierungs-App (TOTP)**, **Code per E-Mail** oder **Deaktiviert**. Beide Methoden können nicht gleichzeitig aktiv sein.

Führen Sie für TOTP einmal `python setup.py install` aus, falls die QR-Unterstützung fehlt. Scannen Sie den QR-Code mit Google Authenticator, Microsoft Authenticator, 2FAS, Aegis oder einer anderen TOTP-App und geben Sie den aktuellen sechsstelligen Code ein. OSPy aktiviert das Geheimnis erst nach dieser Bestätigung. TOTP benötigt eine korrekte Systemzeit.

Die E-Mail-Prüfung ist nur verfügbar, wenn **E-mail Notifications SSL** installiert ist, läuft und SMTP-Server, Konto, Passwort und Empfänger konfiguriert sind. Beim Aktivieren sendet OSPy sofort einen Bestätigungscode. Anmeldecodes gelten fünf Minuten und werden nie in die Wiederholungswarteschlange des Plug-ins gestellt.

Speichern Sie nach der Aktivierung die angezeigten einmaligen Sicherungscodes sicher. Jeder Code ersetzt den zweiten Faktor genau einmal und wird danach gelöscht; er wird nicht erneut angezeigt. Eine Änderung oder Deaktivierung von 2FA widerruft alle gemerkten Browseranmeldungen. Bei Verlust des Telefons oder Ausfall der E-Mail verwenden Sie einen Sicherungscode; andernfalls muss eine Konfigurationssicherung wiederhergestellt oder 2FA lokal am OSPy-Gerät zurückgesetzt werden.
    Abmelden

----

# Anmelden
Die Anmeldeseite enthält ein Textfeld zur Eingabe eines Namens und eines Passworts. Der Standardname ist **admin**. Bei der ersten Installation wird ein zufälliges Passwort generiert (dieses Passwort muss dann in den Einstellungen in ein anderes Passwort geändert werden! Auf der Seite - Reiter „Einstellungen“ empfiehlt es sich, das Passwort (oder auch den Namen) in ein eigenes neues Passwort zu ändern.
Geben Sie Namen und Passwort ein und klicken Sie auf die Schaltfläche **ANMELDEN**.


----

# Homepage
Die Homepage ist das Hauptkontrollzentrum der Weboberfläche. Dazu gehört:

* Uhr zeigt die aktuelle Uhrzeit auf allen Seiten an.
* Navigationsleiste oben zum Wechseln zwischen den Seiten. Die Schnittstelle ist neben der Anmeldeseite auch auf anderen Seiten zu finden.
* Eine Reihe von Schaltflächen zum Vornehmen globaler Änderungen am Systemverhalten.
* Eine Zeitleiste, die Informationen zu abgeschlossenen und geplanten Bewässerungsereignissen bereitstellt.
* Ein Diagramm, das Informationen über Bewässerungsereignisse liefert.
* Eine Fußzeile, die auf allen Seiten vorhanden ist (sofern der Benutzer angemeldet ist). Die Fußzeile enthält: CPU-Temperatur, CPU-Auslastung, Softwareversion, externe IP-Adresse, Betriebszeit des Betriebssystems.
* Einige Erweiterungen können eine Homepage einfügen und andere Elemente hinzufügen. Beispielsweise fügt die Astral-Erweiterung der Zeitleiste grafische Darstellungen von Sonnenaufgang und Sonnenuntergang hinzu. Grafische Spalte zur Überwachung des Erweiterungstanks mit Volumen und Wassermenge.


## Normal – % der Programmzeit
Eine Schaltfläche, mit der Sie den „Wasserstand“ als Prozentsatz der Gesamtlaufzeit für alle Bewässerungsprogramme einstellen können (bei Programmen können Sie deren eingestellte Zeit erhöhen oder verringern).

## Aktiv – Regenverzögerung
Regenverzögerung. Eine Schaltfläche, mit der die Bewässerung für alle Stationen für einen bestimmten Zeitraum angehalten werden kann, mit Ausnahme derjenigen, die auf der Seite „Stationen“ so eingestellt sind, dass Regen ignoriert wird.

## Scheduler - Handbuch
Scheduler – Handbuch. Eine Taste, die das System zwischen Zeitplan (automatischer Modus) und manuellem Modus umschaltet, was eine direkte Steuerung von Stationen ermöglicht.

## Aktiviert – Deaktiviert
Schaltfläche zum Aktivieren oder Deaktivieren der Ausführung des OSPy-Programms (wenn deaktiviert, wird der Scheduler nicht ausgeführt).

## Stoppen Sie alle Stationen
Mit der Taste „Stoppen Sie alle Stationen“ können Sie ein laufendes Bewässerungsprogramm oder eine aktive Station sofort abbrechen.

## Bewässerungsstatistik (Grafik)
Wenn mindestens ein Programm im Zeitplaner eingestellt ist, wird am unteren Bildschirmrand eine Grafik mit der für jede Station (Programme) gelieferten Wassermenge gezeichnet.

## Unterdrückt durch Regenverzögerung
Wenn die Regenverzögerung aktiviert ist, wird „Unterdrückt durch Regenverzögerung“ angezeigt und alle Stationen (außer denen, die auf der Seite „Stationen“ so eingestellt sind, dass sie Regen ignorieren) werden für einen bestimmten Zeitraum gesperrt.

## Regen erkannt
Wenn der Regensensor aktiviert ist, wird „Unterdrückt durch Regensensor“ angezeigt und alle Stationen (außer denen, die auf der Seite „Stationen“ so eingestellt sind, dass Regen ignoriert wird) werden blockiert.

## CPU Temp
Temperatur des Raspberry-Pi-Prozessors. Die angezeigte Temperatur kann zwischen C und F umgeschaltet werden.

## CPU Nutzung
Verwendung des Raspberry Pi-Prozessors. Der Verbrauch wird in % angezeigt.

## Softwareversion
Link zum Software-Repository des Projekts und zur Revisionsnummer der installierten Software.

## Externe IP
Externe IP-Adresse für das OSPy-System (Adresse Ihres Verbindungsanbieters – Router). Getestet über pihrt.com.

## Betriebszeit
Die Zeit, die der Raspberry Pi seit dem Einschalten (oder Neustart) in Betrieb war.

## Diagnose
Die Schaltfläche **Diagnose** in der Fußzeile öffnet eine Administratorseite, auf der geprüft werden kann, wie OSPy und seine Plug-ins das System belasten.

Die Seite ist in die Registerkarten **Systemstatus** und **Leistung und Prozesse** unterteilt. **Systemstatus** weist jedem Betriebsbereich den Zustand OK, Warnung, Fehler oder nicht konfiguriert zu. Überwacht werden der Heartbeat des Schedulers, die letzte erfolgreiche Zeitplanberechnung und der nächste Lauf, Ausgabebefehle, Sensorkommunikation, der Zugriff auf die Einstellungsdatenbank, freier Speicherplatz, Fehler aktivierter Plug-ins, E-Mail-Bereitschaft, Wetter, Internetverbindung und die neueste verfügbare Sicherung. Ein erfolgreicher Ausgabeschreibvorgang bestätigt nur, dass OSPy den angeforderten Zustand an den Treiber übergeben hat; ohne Hardware-Rückmeldung wird kein physisches Schalten des Relais bestätigt.

Die Systemübersicht zeigt die aktuelle CPU-Auslastung, CPU-Temperatur, Systemlaufzeit, Load Average, CPU-Auslastung des OSPy-Prozesses, Speicherverbrauch von OSPy, Anzahl der Threads, Plattforminformationen und die Zeit der letzten Aktualisierung.

Die Plug-in-Tabelle zeigt alle verfügbaren Plug-ins, ob sie laufen und aktiviert sind, ihren eigenen Betriebszustand, die aktuelle CPU-Last, die gesamte CPU-Zeit, die Anzahl der Threads, die Startzeit, die Anzahl der Neustarts und verfügbare Aktionen. Ein Plug-in kann optional eine Funktion `health()` bereitstellen, die zum Beispiel `{'status': 'ok', 'summary': '...', 'details': '...'}` zurückgibt; zulässige Zustände sind `ok`, `warning`, `error` und `unknown`. Ältere Plug-ins ohne diese Funktion bleiben vollständig kompatibel und zeigen „nicht gemeldet“. Eine fehlgeschlagene oder zu lange Zustandsprüfung stoppt weder das Plug-in noch die Diagnoseseite. Die Daten werden automatisch aktualisiert, sodass die Seite geöffnet bleiben kann, während die Systemlast beobachtet wird.

Standardmäßig werden Plug-ins nach aktueller CPU-Last von hoch nach niedrig sortiert. Mit **Plug-ins sortieren** kann nach Plug-in-Name oder gesamter CPU-Zeit sortiert werden, wenn eine stabile Liste benötigt wird oder langfristige CPU-Verbraucher gesucht werden.

Die Aktion **Öffnen** öffnet die Plug-in-Seite. **Restart plugin** startet nur das ausgewählte laufende Plug-in neu; OSPy wird dadurch nicht vollständig neu gestartet.

Wenn eine Aktualisierungswarnung angezeigt wird, ist das letzte automatische Lesen der Diagnose-API fehlgeschlagen oder hat einen kontrollierten Fehler zurückgegeben. Vorhandene Daten können bis zur nächsten erfolgreichen Aktualisierung sichtbar bleiben, und die Warnung wird nach einer erfolgreichen Aktualisierung automatisch gelöscht.

----

# Feedback
Die Schaltfläche **Feedback** in der Kopfzeile links neben dem Systemnamen öffnet eine Seite zum Melden von Fehlern, Vorschlagen von Verbesserungen und Stellen von Fragen. Die Seite ist für angemeldete Administratoren und Benutzer verfügbar; auf der Anmeldeseite wird die Schaltfläche nicht angezeigt.

Wählen Sie **Bug report**, **Feature request** oder **Question** und geben Sie anschließend einen kurzen Titel und eine ausführliche Beschreibung ein. **Continue to GitHub** öffnet ein vorausgefülltes neues GitHub Issue. Der Benutzer meldet sich bei GitHub an, prüft den Inhalt und sendet ihn dort ab. OSPy speichert kein GitHub-Zugriffstoken und erstellt vor dieser Bestätigung kein Issue.

Die Option zum Einfügen von Systeminformationen ist standardmäßig aktiviert und zeigt vor dem Absenden eine genaue Vorschau: OSPy-Version und -Datum, Architektur, Distribution und Betriebssystemversion sowie Python-Version. Der OSPy-Systemname, der Name des Bedieners, IP-Adressen und die eindeutige Kennung der Nutzungsstatistik werden nicht eingefügt. Deaktivieren Sie die Option, um nur den eigenen Text zu senden.

**View existing reports** öffnet die GitHub Issues des Projekts. **GitHub Discussions** öffnet direkt die Projektdiskussionen und eignet sich für allgemeine Fragen und gemeinsame Ideen. Screenshots und andere Dateien können nach dem Öffnen von GitHub angehängt werden.

Das Formular verwendet die bestehende OSPy-Anmeldung und den CSRF-Schutz. Beim Wechsel zu GitHub wird die Adresse der geöffneten OSPy-Seite nicht als HTTP-Referrer übertragen.

----

# Programme
## Fügen Sie ein neues Programm hinzu
Mit dem Button „Fügen Sie ein neues Programm hinzu“ erstellen wir ein neues Scheduler-Programm.

## Programmgruppen
Programme können in Dropdown-Gruppen organisiert werden. Gruppen eignen sich beispielsweise zur Trennung von Sommer- und Winterprogrammen oder zur klaren Aufteilung nach Gartenteilen.

## Gruppe hinzufügen
Über die Schaltfläche „Gruppe hinzufügen“ können Sie eine neue Gruppe von Programmen erstellen.

## Gruppe umbenennen
Die Aktion zum Umbenennen einer Gruppe ändert nur den Gruppennamen. Der Gruppe zugewiesene Programme bleiben erhalten.

## Gruppe aktivieren oder deaktivieren
Eine Gruppen-EIN/AUS-Aktion aktiviert oder deaktiviert alle Programme in dieser Gruppe gleichzeitig. Es eignet sich beispielsweise zur saisonalen Umschaltung mehrerer Programme.

## Gruppe kopieren
Die Kopieraktion erstellt eine neue Gruppe und kopiert alle Programme aus der ursprünglichen Gruppe hinein. Die kopierten Programme werden deaktiviert, sodass sie erst dann ausgeführt werden können, wenn wir sie überprüfen.

## Gruppe löschen
Das Löschen der Gruppe erfordert eine Bestätigung. Programme aus der gelöschten Gruppe werden in die Standardgruppe verschoben.

## Gruppe verschieben
Die Schaltfläche „Gruppe verschieben“ neben „Neues Programm hinzufügen“ verschiebt einmalig den nächsten geplanten Lauf der gesamten Gruppe. Wählen Sie ein neues Datum und eine neue Startzeit für das erste Programm; vor der Bestätigung wird eine Vorschau des ursprünglichen und des neuen Zeitbereichs angezeigt. Der neue Start muss nach dem ursprünglichen Start und in der Zukunft liegen und darf höchstens 30 Tage im Voraus eingestellt werden.

OSPy sucht den nächsten zukünftigen Lauf jedes aktivierten Programms in der Gruppe und verschiebt alle diese Läufe um dieselbe Zeitdifferenz. Reihenfolge, Laufzeiten und relative Abstände der Programme bleiben erhalten. Eine heute von 18:00 bis 22:00 geplante Gruppe kann beispielsweise auf morgen 07:00 verschoben werden; der verschobene Lauf endet dann ungefähr um 11:00.

Die Verschiebung ändert weder die normalen Programmdefinitionen noch die später geplanten Tage. Nur der nächste ursprüngliche Lauf wird einmal übersprungen und zum neuen Zeitpunkt ersetzt. Die verschobenen Programme berücksichtigen weiterhin den Zustand des Zeitplaners, Regensperren, den Regensensor, Ausgangslimits und Stationsverzögerungen. Die Verschiebung wird in den Einstellungen gespeichert und bleibt nach einem Neustart des OSPy-Dienstes erhalten. Pro Gruppe ist nur eine aktive Verschiebung zulässig.

Eine aktive Verschiebung wird bei der Gruppe mit ursprünglicher Zeit, Pfeil und neuer Zeit angezeigt. Mit „Verschiebung abbrechen“ kann sie entfernt werden. Wenn der ursprüngliche Zeitpunkt noch nicht erreicht ist, wird der normale ursprüngliche Lauf wiederhergestellt. Ist der ursprüngliche Zeitpunkt bereits erreicht, wird er aus Sicherheitsgründen nicht erneut gestartet; nur der Ersatzlauf wird abgebrochen. Eine Gruppe mit aktiver Verschiebung kann nicht gelöscht werden; brechen Sie zuerst die Verschiebung ab. Das Erstellen und Abbrechen ist nur für Administratoren verfügbar und durch Anmeldung sowie CSRF-Prüfung geschützt.

## Jetzt ausführen
Mit dem Button „Jetzt ausführen“ starten wir das Programm sofort unabhängig von Uhrzeit und Datum des Planers.

## Bearbeiten
Mit der Schaltfläche „Bearbeiten“ können Sie die Parameter eines bereits erstellten Programms ändern.

## Kopieren
Die Schaltfläche „Kopieren“ erstellt eine Kopie des ausgewählten Programms. Das Kopieren ist standardmäßig deaktiviert, sodass wir es sicher ändern können, bevor wir es im Planer verwenden.

## In die Gruppe verschieben
Ein Programm kann auf der Programmbearbeitungsseite einer Gruppe zugewiesen werden. Dadurch ändert sich lediglich die Position auf der Seite „Programme“.

## Alle löschen
Die Schaltfläche „Alle löschen“ entfernt nach Bestätigung alle vorhandenen Programme.

## Programm aktivieren oder deaktivieren
Der „ON/OFF“-Schalter ermöglicht die Aktivierung/Deaktivierung des erstellten Programms im Scheduler.

## Kollisionswarnung
Beim Speichern eines Programms prüft OSPy die erlaubten Programme und sucht nach Überschneidungen der geplanten Ausführung auf derselben Station/Ausgabe. Wenn gleichzeitig ein anderes Programm geplant ist, wird auf der Seite „Programme“ eine Benachrichtigung mit der Überlappungszeit angezeigt. Dies ist nur eine Warnung, das Programm wird nicht automatisch blockiert oder geändert.

## Zeitplantyp
Der Zeitplanertyp ermöglicht die Auswahl des geeigneten Programmtyps entsprechend unseren Anforderungen (ausgewählte Tage, Wiederholung, wöchentlich, benutzerdefiniert und Programme basierend auf der Wettervorhersage).

### Ausgewählte Tage (einfach)

#### Startzeit

#### Dauer

#### Wiederholen

#### Wiederholungen

#### Pause

### Ausgewählte Tage (verlängert)

#### Planer

### Wiederholen (einfach)

#### Wasserintervall

#### Beginnend in

#### Startzeit

#### Dauer

#### Wiederholen

#### Wiederholungen

#### Pause

### Wiederholen (erweitert)

#### Wasserintervall

#### Beginnend in

#### Planer

### Wöchentlich (erweitert)

#### Montag-Sonntag

### Benutzerdefiniert

#### Wasserintervall

#### Beginnend in

#### Tag 1 - Tag 7

### Wöchentlich (Wettervorhersage)

#### Bewässerung min

#### Bewässerung max

#### Lauf max

#### Pausenverhältnis

#### Bevorzugte Ausführungsmomente

#### Tag

#### Startzeit

#### Priorität

#### Hinzufügen – Löschen

## Keine Anpassungen
An diesem Programm werden keine Änderungen vorgenommen (z. B. Verkürzung oder Verlängerung der Zeit).

## Abgeschnitten
Wäre die angepasste Laufzeit des Programms kürzer als diese eingestellte Zeit, wird das Programm übersprungen (z. B. die angepasste Laufzeit aus der Wettervorhersageverlängerung, oder die monatliche Anpassung der Wassermenge und andere Verlängerungen). Die Zeit wird in Prozent angegeben.

## Master aktivieren
Alle Stationen, bei denen die Option „Master 1/2 per Programm aktivieren“ aktiviert ist, aktivieren die Master Station 1/2 gemäß dieser Zuordnung im Programm. Benachrichtigung! Bei Stationen, bei denen die Option „Haupt 1/2 per Programm aktivieren“ eingestellt ist, können die Steuerungsoptionen „Einmal ausführen“ und „manuell_on“ nicht verwendet werden. Es startet nur die Station, nicht die Hauptstation (1 oder 2)! Diese Einstellung ist nur verfügbar, wenn Sie beide Masterstationen nutzen!

----

# Einmal ausführen

Die Seite „Einmal ausführen“ zeigt eine Liste der zulässigen Sender mit jeweils einem Minuten- und Sekundenfeld. Auf diesem Gelände kann einmalig eine zusätzliche Bewässerung getestet und bereitgestellt werden.

## Jetzt ausführen
Die Taste aktiviert alle ausgewählten voreingestellten Sender.

## Zeit zurücksetzen
Die Schaltfläche löscht alle voreingestellten Zeiten für alle Sender.

----

# Plugins

Auf der Seite „Plugins“ können wir alle Erweiterungen im OSPy-System konfigurieren bzw. steuern.

## Verwalten

Durch Klicken auf die Schaltfläche „Verwalten“ wird das Erweiterungsmanagerfenster in OSPy geöffnet. Alle verfügbaren Erweiterungen können aktiviert, deaktiviert, aus dem Repository installiert usw. werden.

Ein Plug-in kann optional eine Datei `plugin.json` mit Name, Version, Beschreibung, Autor, Homepage und Lizenz enthalten. Der Manager zeigt diese Metadaten an, wenn sie verfügbar sind. Ältere Plug-ins ohne Manifest bleiben kompatibel und OSPy liest ihren Namen aus `__init__.py`; ein ungültiges Manifest wird sicher ignoriert.

Vor der Aktivierung prüft OSPy die angegebenen OSPy- und Python-Versionen, erforderliche Python-Module, unterstützte Plattformen, die Verfügbarkeit von GPIO/I²C sowie Konflikte mit aktivierten Plug-ins, GPIO-Pins oder I²C-Adressen. Ein blockierendes Problem verhindert die Aktivierung, und „Alle aktivieren“ überspringt das betroffene Plug-in. Plug-in-Verwaltung und Diagnose zeigen Details sowie deklarierte Berechtigungen für Netzwerk, Dateien, I²C, GPIO, E-Mail, Unterprozesse oder System an. Berechtigungen informieren den Administrator; sie sind keine isolierte Betriebssystem-Sandbox.

Neue Plug-ins können die gemeinsame Thread-Lebenszyklusverwaltung und das OSPy-Stoppsignal verwenden. Beim Deaktivieren sendet OSPy zuerst das Stoppsignal, ruft die vorhandene Funktion `stop()` auf und wartet bis zu fünf Sekunden auf registrierte Threads. Threads, die weiterlaufen, werden in der Diagnose als Fehler gemeldet und verhindern den Start einer zweiten Plug-in-Instanz. Bestehende Plug-ins ohne diese Schnittstelle bleiben kompatibel.

## Neues Plugin installieren

Nach dem Klicken auf die Schaltfläche „Neues Plugin installieren“ öffnet sich ein Remote-Repository-Fenster, in dem wir verfügbare Erweiterungen zur Installation auf dem OSPy-System auswählen und allgemeine Informationen zu den Erweiterungen lesen können.

### Benutzerdefiniertes Plug-in (ZIP)
Mit dem Erweiterungsmanager können Sie Ihre eigene Erweiterung im OSPy-System installieren, die nicht im Remote-Repository veröffentlicht wird (z. B. Ihre persönliche Erweiterung). Über die Schaltfläche „Durchsuchen“ wählen wir die gewünschte Datei auf unserem Computer aus, um sie im OSPy-System zu installieren. Die Erweiterungsdatei (zip) muss die vollständige Struktur der Erweiterung enthalten (Init, Templates, i18n, Readme usw.).

### Github (https://github.com/martinpihrt/OSPy-plugins/archive/master.zip)
Am oben genannten Speicherort befindet sich ein Repository mit verfügbaren Erweiterungen für das OSPy-System.

Beim Installieren oder Aktualisieren einer Erweiterung wird Code aus der ausgewählten Quelle ausgeführt. OSPy zeigt die Repository-URL an und fordert vor der Installation oder Aktualisierung eine Bestätigung an. Die Aktion „Änderungen abrufen“ zeigt beim Kontaktieren des Remote-Repositorys eine Meldung über den laufenden Check an.

## Alle deaktivieren
Die Schaltfläche deaktiviert alle installierten Erweiterungen.

## Alle aktivieren
Die Schaltfläche aktiviert alle installierten Erweiterungen.

## Aktivieren Sie die Überprüfung auf Updates
Wenn die Schaltfläche aktiv ist, wird nach einer Stunde automatisch die Verfügbarkeit einer neuen Version der Erweiterung im Remote-Repository überprüft. Wenn eine neue Version verfügbar ist, wird neben der Erweiterung eine „Update“-Meldung angezeigt.

## Änderungen laden
Die Schaltfläche ruft die neueste Liste der verfügbaren Änderungen aus dem Remote-Erweiterungs-Repository ab.

## Änderungen
Die Schaltfläche öffnet eine Übersicht der verfügbaren Erweiterungsänderungen und Update-Informationen.

## Automatische Updates
Wenn die Schaltfläche aktiv ist, wird diese Erweiterung automatisch aktualisiert, wenn eine neue Version der Erweiterung verfügbar ist. Warnung: OSPy wird ständig weiterentwickelt und wenn es zu einer größeren Änderung in OSPy kommt und der Benutzer OSPy nicht aktualisiert, funktioniert die Erweiterung nach dem Update möglicherweise nicht mehr. Aktualisieren Sie immer zuerst OSPy und dann alle Erweiterungen!

----

# Protokoll
Über die Seite „Protokoll“ können wir alle im OSPy-System aufgezeichneten Protokolle einsehen. Die Anzahl der Datensätze wird auf der Seite „Einstellungen“ eingestellt.

## Ereignisprotokoll
Das Ereignisprotokoll ist eine Betriebs- und Audit-Historie, die sowohl vom Stationslaufprotokoll als auch vom technischen Debug-Protokoll getrennt ist. Es erfasst Eingriffe in die Bewässerung und blockierte Läufe, Konfigurationsänderungen, Benutzer- und Sicherheitsereignisse, System- und Plug-in-Vorgänge sowie Sensorereignisse oder -zustände. Jeder Eintrag zeigt Datum, Uhrzeit, Schweregrad, Kategorie, Betreff und Details. Der Schweregrad wird zusätzlich farblich dargestellt: Information blau, Erfolg grün, Warnung orange, Fehler rot und kritisch dunkelrot. Mit der Auswahl **Ereigniskategorie** können alle Ereignisse oder eine einzelne Kategorie angezeigt werden. Der Export `events.csv` enthält Date, Time, Level, Category, Subject und Status. Die bestehende Debug-Protokollierung und ihre Datei `events.log` werden von diesen Bedienelementen nicht beeinflusst.

Dasselbe Audit-Protokoll erfasst auch zustandsändernde Vorgänge über die authentifizierte API, darunter die Steuerung von Stationen und Programmen, Konfigurationsänderungen, das Löschen von Protokollen und Systemaktionen. Fehlgeschlagene API-Authentifizierungen und temporäre Sperren bei Brute-Force-Versuchen erscheinen unter **Benutzer und Sicherheit**. Normale API-Lesezugriffe und jede erfolgreiche Basic-Authentifizierung werden nicht protokolliert, damit häufiger API-Verkehr das Protokoll nicht füllt.

## Protokoll herunterladen als
Über den Link „Datensatz als Excel log.csv herunterladen“ können Sie den Datensatz des Bewässerungslaufs als CSV-Datei (Excel-Programm) auf Ihrem Computer speichern.
* Die Struktur der Tabelle ist: Datum, Startzeit, Zone, Dauer, Programm. Datumsangaben werden durch ein Komma getrennt.
* Beispiel: 2019-08-12 05:00:00 Filterung 60:00 Filterung

Link „Protokoll als Excel-Protokoll email.csv herunterladen.“ ermöglicht es Ihnen, eine Aufzeichnung der gesendeten E-Mails als CSV-Datei (Excel-Programm) auf Ihrem Computer zu speichern.
* Die Struktur der Tabelle ist: Datum, Uhrzeit, Betreff, Text, Status. Datumsangaben werden durch ein Komma getrennt.
* Beispiel: 12.08.2019 06:00:04 Gesendet COTTAGE SYSTEM Bewässerung beendet -> Programm: Filtration, Station: Filtration, Start: 12.08.2019 05:00:00, Dauer: 60:00, Wasser -> Wassermenge im Tank: Füllstand: 170 cm (90 %), Ping: 95 cm, Volumen: 1,28 m3, Temperatur DS1-DS6-> KELLER: 21,1 ℃ PUMPE: 33,5 ℃ KESSEL: 26,6 ℃ INNEN: 22,1 ℃ BRUNNEN: 12,2 ℃

## Protokoll löschen
Durch Drücken der Schaltfläche „Protokoll löschen“ werden alle Aufzeichnungen des Bewässerungslaufs gelöscht. Die Aktion ist nicht erstattungsfähig.

## Datensatz E-Mail löschen
Nach dem Klicken auf die Schaltfläche „E-Mail-Datensatz löschen“ werden alle Datensätze gesendeter E-Mails aus dem System gelöscht. Die Aktion ist nicht erstattungsfähig.

----

# Einstellungen
Auf der Seite „Einstellungen“ können wir die Einstellungen des gesamten OSPy-Systems ändern.
Die Seite enthält mehrere ausblendbare Abschnitte. Klicken Sie auf die Leiste, um den gewünschten Abschnitt zu öffnen oder zu schließen.

### Tooltips anzeigen

* Klicken Sie auf die Schaltfläche „Hilfe anzeigen“, um Informationen zu den einzelnen Optionen anzuzeigen oder auszublenden.

### Systemname
Die Systembenennung ist nützlich, wenn Sie mit mehreren OSPy-Systemen arbeiten.

* Geben Sie einen eindeutigen, beschreibenden Namen für das System ein.
* Klicken Sie unten auf der Seite auf die Schaltfläche „Änderungen bestätigen“, um Ihre Änderungen zu speichern.

Der Systemname lautet standardmäßig „OpenSprinkler Pi“ und wird zur einfachen Identifizierung des Systems in der Kopfzeile jeder Seite angezeigt.

### Systemthema
Bestimmt das Erscheinungsbild der GUI. In der Liste sind mehrere Themen verfügbar (grüner Modus, schwarz-weißer Modus ...)

### 24-Stunden-Uhr
Die 24-Stunden-Zeitoption wählt zwischen dem internationalen 24-Stunden-Format, manchmal auch als Militärzeit bezeichnet, und dem 12-Stunden-AM/PM-Format.

* Deaktivieren Sie das Kontrollkästchen und wählen Sie das 12-Stunden-AM/PM-Format.
* Klicken Sie unten auf der Seite auf die Schaltfläche „Änderungen bestätigen“, um Ihre Änderungen zu speichern.

Sie werden zur Startseite weitergeleitet und die Uhr wird im ausgewählten Format angezeigt.

### HTTP IP-Adresse
IP-Adresse für den HTTP/S-Server. IPv4- oder IPv6-Adresse (wird erst nach dem Neustart angezeigt.) Der Standardwert ist 0.0.0.0.

#### Über die Portnummer
Die HTTP/S-Portnummer ist Teil der Webadresse.
Port 80 ist die Standardnummer für Webseiten und wird daher möglicherweise nicht einbezogen, wenn eine URL in die Adressleiste des Browsers eingegeben wird. Viele Webserver verwenden standardmäßig Port 80.
Wenn Sie einen anderen Server auf demselben Raspberry Pi wie OSPy betreiben und dieselbe Portnummer verwenden, tritt ein Konflikt auf und OSPy startet möglicherweise nicht.
Sie können den Konflikt vermeiden, indem Sie die OSPy-Portnummer auf der Seite „Optionen“ in etwas anderes ändern, z. B. 8080. Wenn Sie die von OSPy verwendete Portnummer ändern, müssen Sie diese Nummer mit vorangestelltem Doppelpunkt in die URL für die OSPy-Webschnittstelle einfügen. Zum Beispiel:
[URL Raspberry pi]: 8080

### HTTP/S port
Die HTTP/S-Portnummer ist Teil der Webadresse. Port 80 ist die Standardnummer für Websites.

* Klicken Sie in das Textfeld neben der Option HTTP/S-Port.
* Geben Sie die Portnummer ein, die Sie verwenden möchten, z. B. 8080.
* Klicken Sie unten auf der Seite auf die Schaltfläche „Änderungen bestätigen“.

Sie werden zur Startseite zurückgeleitet. Das System startet neu, in der Weboberfläche ist jedoch keine Neustartanzeige sichtbar. Warten Sie mindestens 60 Sekunden, fügen Sie dann die neue Portnummer mit vorangestelltem Doppelpunkt (:) zur Pi-URL hinzu und versuchen Sie erneut, eine Verbindung zu OSPy herzustellen.

### Plugins auf der Startseite anzeigen
Wenn wir Messdaten der Erweiterung (Wind, Temperatur, Pegel...) unter der Grafik auf der Startseite (Startseite) anzeigen möchten, aktivieren Sie das Kontrollkästchen. Wenn wir die Daten der Erweiterung nicht anzeigen möchten, deaktivieren wir das Kontrollkästchen.
* Achtung: Damit die Daten korrekt angezeigt werden, muss die Erweiterung aktiviert und richtig eingestellt sein.

### Sensoren zu Hause anzeigen
Wenn wir die Messdaten der Sensoren unter der Grafik auf der Startseite (Startseite) anzeigen möchten, aktivieren wir das Kontrollkästchen. Wenn wir die Daten der Sensoren nicht anzeigen möchten, deaktivieren wir das Kontrollkästchen.
* Achtung: Damit die Daten korrekt angezeigt werden, müssen die Sensoren aktiviert und richtig eingestellt sein.

### Systemsprache
Durch Auswahl der Sprache können wir die in der Weboberfläche verwendete Sprache ändern.

* Klicken Sie auf den Abwärtspfeil rechts neben dem Sprachfeld, um eine Liste der verfügbaren Sprachen anzuzeigen.
* Klicken Sie auf die Sprache, die Sie in der Benutzeroberfläche verwenden möchten.
* Klicken Sie unten auf der Seite auf die Schaltfläche „Änderungen bestätigen“.

Die Software wird neu gestartet und nach einigen Sekunden wird die Benutzeroberfläche in der ausgewählten Sprache angezeigt.

### Zeigen Sie Bilder an Stationen
Aktivieren Sie dieses Kontrollkästchen, um Senderbilder auf der Startseite und der Senderseite anzuzeigen.

## Wetter
Der Wetterbereich bietet Zugriff auf einen Wettervorhersagedienst für Ihren Standort. Für diese Funktion müssen Sie sich auf der Website (https://stormglass.io/) registrieren.
Je nach Wettervorhersage kann der Bewässerungszyklus automatisch angepasst werden (wenn wir eine Erweiterung wählen, die die Wettervorhersage nutzt).
* Für die Registrierung und Nutzung des Dienstes fallen bei normaler Nutzung keine Gebühren an.

### Verwenden Sie Wetter
Verbindung zum Stormglass-Dienst aktivieren oder deaktivieren.

### Storm Glass API-Schlüssel
Zur Nutzung lokaler Wetterbedingungen ist ein Storm Glass-API-Schlüssel erforderlich.

### Standort
Name der Stadt oder Postleitzahl. Wird zur Ortung mithilfe von OpenStreetMap für Wetterinformationen von Storm Glass verwendet.

Mit **Auf Karte auswählen** öffnen Sie eine berührungsfreundliche Karte, klicken auf den genauen Wetterpunkt und bestätigen ihn. **Gerätestandort verwenden** kann nach Zustimmung des Benutzers die Browserposition einsetzen. Nach dem Speichern sind Breiten- und Längengrad der maßgebliche Stormglass-Standort; eine Änderung des Textfelds Standort schaltet zurück zur Namenssuche über OpenStreetMap. Die Startseite zeigt eine kompakte Standortkarte, öffnet dieselbe Karte schreibgeschützt und zeigt technische Koordinaten unter Details.

## Benutzer
Um die Sicherheit zu erhöhen, empfehlen wir, das OSPy-Systemkennwort und den Benutzernamen vom Standardwert „admin“ zu ändern. Bei Bedarf können Sie die Passwortanforderung auch deaktivieren.

* Klicken Sie auf das Dreieck links neben der Leiste mit der Bezeichnung „Benutzer“, um den Abschnitt zu erweitern.
* Aktivieren Sie das Kontrollkästchen „Kein Passwort“, wenn Sie einen sehr guten Grund haben, den Passwort- und Namensschutz zu deaktivieren. Das System erfordert keine Benutzeranmeldung mehr. Alle Abschnitte werden zugänglich sein.
* Geben Sie Ihren Benutzernamen ein.
* Geben Sie Ihr aktuelles Passwort ein.
* Geben Sie Ihr neues Passwort in die Felder „Neues Passwort“ und „Passwort bestätigen“ ein.
* Klicken Sie unten auf der Seite auf die Schaltfläche „Änderungen bestätigen“.

Sie werden zur Startseite zurückgeleitet. Bei der nächsten Anmeldung werden Ihr neues Passwort und Ihr neuer Name benötigt.

### Deaktivieren Sie die Sicherheit
Wenn das Kästchen „Deaktivieren Sie die Sicherheit“ aktiviert ist, erlauben wir anonymen Benutzern ohne Passwort den Zugriff auf das System.

### Benutzername
Geben Sie Ihren Benutzernamen in das Textfeld ein. Dies ist „admin“ bei einer Neuinstallation.

### Aktuelles Passwort
Geben Sie Ihr aktuelles Passwort in das Textfeld ein.

### Neues Passwort
Geben Sie das neue Passwort in das mit „Neues Passwort“ gekennzeichnete Feld ein.

### Passwort bestätigen
Geben Sie im mit „Passwort bestätigen“ gekennzeichneten Feld das gleiche neue Passwort ein wie im Feld „Neues Passwort“.

### Zusätzliche Benutzer
Nach dem Klicken auf die Schaltfläche öffnet sich eine Seite, auf der wir neue Benutzer für den Zugriff auf das System erstellen und ggf. bearbeiten können.

## Sicherheit

### Formularschutz
Aktionen, die Systemeinstellungen oder -status ändern, befinden sich in der durch ein Formulartoken geschützten Weboberfläche. Wenn die Seite längere Zeit geöffnet ist oder die Browsersitzung abbricht, laden Sie die Seite neu und versuchen Sie es erneut.

### Verwenden Sie den Zugang HTTPS
Falls wir den OSPy-Server für eine höhere Datenübertragungssicherheit mithilfe eines SSL-Zertifikats konfiguriert haben, aktivieren Sie das Kontrollkästchen „Verwenden Sie den Zugang HTTPS“. Wenn die Option „Verwenden Sie den Zugang HTTPS“ aktiviert ist und der Server nicht richtig eingestellt ist, startet OSPy als ungesicherter http-Server.

Die serverseitige HTTPS-Auswahl ist jetzt eindeutig: Das eigene Zertifikat hat Priorität, andernfalls wird Let’s Encrypt verwendet; das Aktivieren beider Optionen führt nicht mehr zu einem stillen HTTP-Fallback.

### Domainname
Das Zertifikat befindet sich auf dem System im Verzeichnis „/etc/letsencrypt/live/“ Domänenname „/fullchain.pem“ und „/etc/letsencrypt/live/“ Domänenname „/privkey.pem“. Das Zertifikat muss manuell mit dem Tool „Certbot“ im System (Linux) installiert werden (die Verwendung von https wird in OSPy erst nach einem Neustart von OSPy berücksichtigt).
* Das Verfahren zur Installation des Zertifizierungsdienstes finden Sie in der „Readme“-Hilfedatei oder auf Github.

### Verwenden Sie HTTPS mit Certbot
SSL-Zertifikat mit Let's Encrypt-Zertifizierungsstelle.
Certbot (https://certbot.eff.org/) und Let's Encrypt (https://letsencrypt.org/).

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

### Verwenden Sie den eigenen HTTPS-Zugang
Wenn in den OSPy-Einstellungen „Benutzerdefinierten HTTPS-Zugriff verwenden“ ausgewählt ist, müssen Sie die Dateien „fullchain.pem“ und „privkey.pem“ im SSL-Verzeichnis am OSPy-Speicherort ablegen. Warnung: OSPy muss neu gestartet werden.
```bash
sudo openssl req -new -newkey rsa:4096 -x509 -sha256 -days 3650 -nodes -out fullchain.pem -keyout privkey.pem
```
Die zweite Möglichkeit besteht darin, die Schaltfläche „Generieren“ auf der Registerkarte „SSL-Zertifikat“ zu verwenden.

### API CORS-aktivierter Ursprung
Diese Option legt den Header „Access-Control-Allow-Origin“ fest, den die API für Clients verwendet, die in einem Browser ausgeführt werden. Der Wert „*“ erlaubt jeden Ursprung, ein Ursprung kann angegeben werden, zum Beispiel „https://example.com“, mehrere Ursprünge durch ein Komma getrennt, oder lassen Sie das Feld leer und CORS-Header werden nicht gesendet. Es ersetzt nicht die API-Authentifizierung; Es bestimmt nur, welche Web-Ursprünge API-Antworten lesen dürfen.

### API JSONP aktivieren
Diese Option aktiviert den alten „Callback“-Parameter für JSONP-API-Antworten. Lassen Sie es deaktiviert, es sei denn, die alte Integration erfordert es. Gängige API-Clients sollen JSON mit CORS verwenden.

### Browser-Anmeldungen gespeichert
Die Anmeldeseite kann sich den Browser mithilfe eines langfristigen Zufallstokens merken, das in einem sicheren Cookie gespeichert wird. OSPy speichert nur den Hash dieses Tokens, nicht das Passwort des Benutzers. Verwenden Sie die Schaltfläche „Abbrechen“, um alle in Browsern gespeicherten Anmeldungen zu löschen. Betroffene Browser müssen sich erneut mit einem Passwort anmelden.

## Sensoren
Der Sensorbereich enthält Einstellungen zur Sensorsicherheit.

### Firmware-Upload-Passwort
Passwort zum Hochladen der Firmware von OSPy auf den Sensor (für alle verwendeten Sensoren – in den Sensoroptionen muss das gleiche Passwort verwendet werden.)

## Stationen konfigurieren
Der Abschnitt „Stationen konfigurieren“ enthält allgemeine Einstellungen, die sich auf die Stationsplanung und -kombination auswirken.

### Die Verwendung von
Gibt an, wie sich Stationsläufe überlappen können. „0“ bedeutet keine Nutzungsbeschränkung, sodass Stationen gleichzeitig laufen können, wenn sich ihre Programme überschneiden. „1“ bedeutet immer jeweils eine Station, wenn jede Station die Nutzung „1“ hat. Ein höherer Wert ermöglicht den gleichzeitigen Betrieb mehrerer Stationen, sofern die Summe ihrer Nutzung das festgelegte Limit nicht überschreitet.

Diese Einstellung wirkt sich auch auf das Einfügen der Pause zwischen den Sendern aus.

#### Über sequentielle und gleichzeitige Modi
* Der sequentielle Modus wird hauptsächlich verwendet, wenn die Wasserquelle nicht mehrere Zweige gleichzeitig versorgen kann. Beispiel: Bei maximaler Auslastung „1“ und Stationsauslastung „1“ muss Station 3 fertig sein, bevor Station 4 starten kann.
* Der gleichzeitige Modus wird verwendet, wenn eine Wasserquelle mehrere Zweige gleichzeitig verarbeiten kann. Beispiel: Bei maximaler Auslastung „0“ können die Stationen 2, 3 und 4 gleichzeitig laufen, wenn sich ihre Programme überschneiden.

### Anzahl der Ausgänge
Die Gesamtzahl der verfügbaren Ausgänge beträgt 8 Ausgänge plus Ausgänge von Erweiterungskarten. Die Anzahl der Ausgänge kann höher eingestellt werden als die tatsächliche Anzahl der physischen Ausgänge, wodurch virtuelle Ausgänge entstehen.

### Pause zwischen Stationen
Eine Pause, die zwischen nacheinander gestarteten Stationen eingefügt wird, wenn der Scheduler sie nicht gleichzeitig starten kann, in Sekunden zwischen 0 und 3600. Dadurch wird die Station relativ zur Master-Station nicht weitergeschaltet.

Beispiel: Bei maximaler Nutzung „1“ und Stationsnutzung „1“ startet ein Wert von „30“ die nächste Station 30 Sekunden nach dem Ende der vorherigen Station.

### Mindestlaufzeit
Überspringt die Pause zwischen den Stationen, wenn der vorherige Lauf kürzer als dieser Wert war, in Sekunden zwischen 0 und 86400.

Beispiel: Bei einer Pause von „30“ und einer Mindestlaufzeit von „10“ erzwingt eine Station, die nur 5 Sekunden lief, keine Pause von 30 Sekunden.

## Master konfigurieren
Der Abschnitt „Master konfigurieren“ wählt Master-Station 1, Master-Station 2 und die Zeitversätze aus, die bei der Aktivierung der Master-Station verwendet werden. Die Hauptstation ist normalerweise eine Pumpe oder ein Hauptwasserversorgungsventil.

Die Master-Station wird nur für Stationen verwendet, bei denen sie auf der Seite „Stationen“ eingestellt ist, oder für Programme, die Master-Station 1 oder 2 für Stationen auswählen, die auf „Master 1/2 durch Programm aktivieren“ eingestellt sind.

### Master-Station
Auswahl der ersten Masterstation, z. B. einer Pumpe oder eines Masterventils.

### Master zwei Station
Auswahl einer zweiten Masterstation, zum Beispiel einer zweiten Pumpe oder einer anderen Wasserquelle.

### Relais aktivieren
Wenn aktiviert, wird das Relais auch als Hauptausgang aktiviert.

### Startversatz der Master-Station
Einschaltzeitversatz der Master-Station 1 vom Stationsstart, in Sekunden zwischen -1800 und +1800. Negative Werte starten den Master früher, positive Werte später.

Beispiel: „-10“ startet die Master-Station 10 Sekunden vor der Station. „+10“ startet es 10 Sekunden nach dem Sender.

### Stoppversatz der Master-Station
Abschaltzeit der Master-Station 1 vom Ende der Station, in Sekunden zwischen -1800 und +1800. Bei negativen Werten wird der Hauptbahnhof früher abgeschaltet, bei positiven Werten bleibt er länger in Betrieb.

Beispiel: „-5“ schaltet die Master-Station 5 Sekunden vor Stationsende aus. „+20“ schaltet es 20 Sekunden nach Ende des Senders aus.

### Startversatz der Master-Station 2
Zeitliche Verschiebung des Einschaltens der Hauptstation 2 gegenüber dem Start der Station. Es funktioniert genauso wie die Startschicht der Hauptstation, jedoch nur für Hauptstation 2.

### Stoppversatz der Master-Station 2
Abschaltzeitversatz Hauptstation 2 relativ zum Stationsende. Es funktioniert genauso wie die Shutdown-Schicht der Master-Station, jedoch nur für Master-Station 2.

## Regensensor
Legt den Schaltertyp des Regensensors fest. Wenn Sie einen Raspberry Pi verwenden und den Regensensor direkt an die GPIO-Pins anschließen möchten, verwenden Sie die Pins 8 und 6 (GND).

### Sensor verwenden
Aktivieren Sie das Kontrollkästchen „Sensor verwenden“, um die Regenerkennung zu aktivieren.

### Normalerweise geöffnet
Aktivieren Sie das Kontrollkästchen „Normalerweise geöffnet“, wenn der Sensor normalerweise ohne Regen geöffnet ist. Andernfalls deaktivieren Sie das Kontrollkästchen. Informationen zum Schaltertyp finden Sie in der Bedienungsanleitung des Regensensors.

### Regenverzögerung einstellen
Bei Aktivierung des Regensensors wird eine Regenverzögerung eingestellt (dies eignet sich beispielsweise, um Programme für eine längere Zeit zu sperren, als der Regensensor vorsieht).

### Regenverzögerungszeit
Regenverzögerungszeit (in Stunden), zwischen 0 und 500.

## Protokollierung
Aktivieren Sie die Laufprotokollierung und legen Sie die Anzahl der Datensätze fest, die Sie behalten möchten. Aktivieren Sie die Protokollierung gesendeter E-Mails und legen Sie die Anzahl der Datensätze fest, die Sie behalten möchten.

### Laufprotokoll aktivieren
Aktivieren Sie das Kontrollkästchen „Laufprotokoll aktivieren“. Dadurch wird die Protokollierung aktiviert und der Bewässerungsverlauf auf der Zeitleiste auf der Startseite aktiviert. Zeichnen Sie alle Stationsläufe auf. Beachten Sie, dass wiederholtes Schreiben auf die SD-Karte deren Lebensdauer verkürzen kann.

### Max. Laufeinträge
Geben Sie die Anzahl der Einträge ein, die Sie im Protokoll speichern möchten. Legen Sie eine Zahl fest, die einen angemessenen Zeitraum abdeckt, beispielsweise eine Woche oder einen Monat. Dies hängt von der Anzahl der Programme und Sender ab, die Sie haben. Bei jedem Start der Station wird es einen Eintrag geben. 0 = keine Begrenzung.

### E-Mail-Protokoll aktivieren
Aktivieren Sie das Kontrollkästchen „E-Mail-Protokoll aktivieren“. Dadurch wird die Protokollierung aktiviert und der E-Mail-Bewässerungsverlauf aktiviert.

### Max. Laufeinträge
Geben Sie die Anzahl der Einträge ein, die Sie im Protokoll speichern möchten. Legen Sie eine Zahl fest, die einen angemessenen Zeitraum abdeckt, beispielsweise eine Woche oder einen Monat. Dies hängt von der Anzahl der Programme und Sender ab, die Sie haben. Für jede E-Mail wird ein Datensatz erstellt. 0 = keine Begrenzung.

### Ereignisprotokoll aktivieren
Ereignisprotokoll aktivieren (Regensensor, Regenverzögerung, Server, externe Internet-IP ...)

### Max. Laufeinträge
Anzahl der auf der Festplatte zu speichernden Ereignisdatensätze, 0 = keine Begrenzung.

### Debug-Protokoll aktivieren
Klicken Sie auf „Debug-Protokoll aktivieren“, um alle internen Vorgänge in OSPy zum besseren Debuggen in einer Datei zu speichern. * Hinweis: * Das zu häufige Speichern von Daten in einer Datei kann die SD-Karte beschädigen oder die Kapazität der SD-Karte (Speicher) nach längerer Zeit verringern. Alle Vorgänge (auch von allen Erweiterungen) werden aufgelistet.

## Systemneustart
Der Abschnitt „Systemneustart“ enthält Schaltflächen zum Neustarten der Software, zum Neustarten der Hardware, zum Ausschalten der Hardware und zum Zurücksetzen aller Einstellungen auf die Standardwerte.

### Neustart
Die Schaltfläche „Neustart“ startet nur die Software neu. Es handelt sich um eine schnelle, erzwungene Möglichkeit, Änderungen in der Software umzusetzen.

### Neustart
Die Schaltfläche „Neustart“ startet den Raspberry Pi neu. Dies dauert länger, führt jedoch zu einem vollständigen Systemneustart.

### Herunterfahren
Die Schaltfläche „Herunterfahren“ schaltet die Stromversorgung der Raspberry Pi-Hardware aus.

### Standard
Die Schaltfläche „Standard“ löscht alle Benutzereinstellungen auf eine standardmäßige Neuinstallation von OSPy.
* Alle Einstellungen können in OSPy auch manuell gelöscht werden (wir finden den Ordner ospy/data im System und löschen alle Dateien im Ordner).

## Systemsicherung
Wenn wir alle Einstellungen unseres OSPy-Bewässerungssystems sichern oder die Einstellungen auf ein anderes OSPy-System übertragen möchten, verwenden wir die Schaltfläche „Herunterladen“ gefolgt von „Hochladen“.

### Herunterladen
Mit der Schaltfläche „Herunterladen“ können Sie eine Konfigurationsdatei zur späteren Verwendung oder zur Wiederherstellung des OSPy-Systems auf den Computer herunterladen. Es wird nicht nur die Datenbankdatei (options.db) gespeichert, sondern auch der Stationsordner, in dem Stationsbilder gespeichert sind. Gleichzeitig wird die Protokolldatei events.log (falls vorhanden) gespeichert. Alles wird in einer Zip-Datei gespeichert (Beispiel: ospy_backup_systemname_4.12.2020_18-40-20.zip). Wir können leicht erkennen, von welchem ​​OSPy-System das Backup stammt. Der SSL-Ordner, in dem sich das Zertifikat befindet, wird aus Sicherheitsgründen nicht in der Backup-ZIP-Datei gespeichert!

### Hochladen
Mit der Schaltfläche „Hochladen“ können Sie OSPy einfügen und wiederherstellen (z. B. bei der Neuinstallation von Linux). Die hochgeladene Datei muss eine ZIP-Datei sein! Die folgenden Pfade und Dateien müssen in der Datei enthalten sein.

```bash
*.zip folder:
ospy/data/events.log
ospy/data/options.db
ospy/data/options.db.bak
ospy/images/stations/station1.png
ospy/images/stations/station1_thumbnail.png
```
Oder andere Senderbilder im gleichen Format.

## SSL Zertifikat
Wenn wir über ein eigenes Zertifikat für SSL (https)-Sicherheit (fullchain.pem und privkey.pem) verfügen, können wir es hier über das Formular hochladen.

## Generieren
Wenn wir ein SSL-Zertifikat generieren möchten, klicken Sie auf die Schaltfläche „Generieren“. Im SSL-Verzeichnis wird ein Zertifikat generiert. Anschließend aktivieren wir in den Einstellungen/Sicherheit die Option „eigenes HTTPS“ und starten dann OSPy neu.

### Hochladen
Die Schaltfläche „Hochladen“ sendet die angehängten Dateien (fullchain.pem und privkey.pem) an den SSL-Ordner im OSPy-Verzeichnis.

----

# Bahnhof
Auf der Seite „Bahnhof“ legen wir die Stationsnamen, Eigenschaften rund um die Nutzung der Wassermenge, Steuerung der Hauptstationen fest.

## Bahnhof
Automatische Nummerierung zur Markierung von Stationen. Zum Beispiel 1 = Station 1, 2 = Station 2...

## Name
Individuelle Benennung der Stationen zur besseren Identifizierung im System, zum Beispiel „Rasen“.

## Nutzung
Legen Sie für bestimmte Stationen Parallelität (0) oder Reihenfolge (>=1) fest. Mehr zu Parallelität bzw. Sequenz im Text oben im Abschnitt „Einstellungen / Über sequentielle und gleichzeitige Modi“.

## Bewässerung
Die Wassermenge pro Stunde in mm, die von den Sprinklern an dieser Station versprüht wird. Wird für wetterbasierte Programme verwendet. Um diesen Wert zu messen, empfiehlt sich die Anschaffung beispielsweise eines Regenmessers aus Kunststoff.

* Bezieht sich auf die Zeit, die eine bestimmte Wassermenge benötigt, um in einen bestimmten Bodentyp einzudringen. Im Allgemeinen ist die Aufnahmerate eines leichter strukturierten (sandigen) Bodens größer als die eines schwerer strukturierten (Ton-) Bodens. Allerdings kann die Beregnung mit großen Wassermengen auch auf sandigen Böden zu Oberflächenabfluss führen. Die Aufnahmerate des bewässerten Bodens wird durch viele Faktoren beeinflusst, wie z. B. Bodenbeschaffenheit, Bodenstruktur, Verdichtung, organische Substanz, geschichtete Böden, Bodensalze, Wasserqualität, Sedimente im Bewässerungswasser usw.

## Lagerbestand
Wassermenge, die der Boden über dem Niveau 0 speichern kann. Wird für wetterbasierte Programme verwendet.

* Bezieht sich auf die Menge an Bodenfeuchtigkeit oder den Wassergehalt, der im Boden zurückbleibt, nachdem das überschüssige Wasser abfließt und die Geschwindigkeit der Abwärtsbewegung verringert wird. Dies geschieht in der Regel 2-3 Tage nach Regen oder Bewässerung in früheren Böden mit einheitlicher Beschaffenheit und Struktur.

## ETo-Faktor
Faktor zur Multiplikation des ETo-Faktors für wetterbasierte Programme. Verwenden Sie einen Wert über 1 bei sonnigem/trockenem Boden, einen Wert unter 1 für schattigen/nassen Boden.

* Bodentyp

Böden haben verschiedene Eigenschaften, die sie einzigartig machen. Wenn Sie die Art Ihres Bodens kennen, können Sie seine Stärken und Schwächen ermitteln. Obwohl der Boden aus vielen Elementen besteht, müssen Sie mit der Art Ihres Bodens beginnen. Sie müssen lediglich die Zusammensetzung der Bodenpartikel überwachen. Mit OSPy können Benutzer den Bodentyp für jede Zone (Station) angeben, was genauere und effizientere Bewässerungsberechnungen ermöglicht. Verschiedene Bodentypen reagieren unterschiedlich auf Wasser; Tonige Böden neigen dazu, zu entwässern, während lehmige Böden Wasser über lange Zeiträume usw. speichern können. Die im Boden enthaltene Wassermenge, nachdem überschüssiges Wasser abfließt, und die Fähigkeit des Bodens, Wasser zu speichern, werden als Feldkapazität bezeichnet (gemessen in Zoll oder Millimetern).

### Flaschentest
Wie ermittelt man die ungefähren Anteile von Sand, Schluff und Ton? Dies ist ein einfacher Test, der Ihnen einen allgemeinen Überblick über die Anteile von Sand, Schluff und Ton im Boden gibt. Geben Sie 5 cm Erde in die Flasche und füllen Sie diese mit Wasser.
Mischen Sie Wasser und Erde gut, stellen Sie die Flasche beiseite und berühren Sie sie eine Stunde lang nicht. Nach einer Stunde wird das Wasser klar und Sie werden sehen, dass sich die größeren Partikel abgesetzt haben:

- Teile organischer Stoffe können auf der Wasseroberfläche schwimmen
- Darüber liegt eine Schicht Lehm.
Wenn das Wasser immer noch nicht klar ist, liegt das daran, dass einige der feineren Tone noch mit dem Wasser vermischt sind
- In der Mitte liegt eine Schlammschicht
- Am Boden befindet sich eine Sandschicht

* Messen Sie die Tiefe von Sand, Schluff und Ton und schätzen Sie deren ungefähres Verhältnis ab.

Die folgenden drei Arten von Partikeln können aus Ihrem Boden bestehen: Ton, Sand und Schluff. Die meisten Böden sind eine Kombination dieser drei Partikel, aber die Art des vorherrschenden Partikels bestimmt viele Eigenschaften Ihres Bodens. Das Verhältnis dieser Größen bestimmt die Art des Bodens: Ton, Lehm, Ton-Lehm, Schluff-Lehm usw.

* Idealer Boden besteht zu 40 % aus Sand, zu 40 % aus Schluff und zu 20 % aus Ton. Diese Mischung wird als Ton bezeichnet. Dadurch wird das Beste aus jeder Art von Bodenpartikeln herausgeholt. Es verfügt über eine gute Wasserableitung und lässt Luft wie Sand in den Boden eindringen, speichert aber auch Feuchtigkeit gut und ist fruchtbar wie Schluff und Ton.

## Balance-Anpassung
Erhöhen oder verringern Sie den Wasserhaushalt für wetterbasierte Programme (sofern nicht auf 0 eingestellt).

## Verbunden
Wenn wir eine Station angeschlossen haben (sie ist physisch verbunden) und wir sie verwenden möchten (zu sehen in der Auswahl in Programmen, auf der Startseite...), kreuzen wir „Verbunden“ an. Wenn wir die Station nicht nutzen und nicht im OSPy-System veröffentlichen möchten, lassen wir „Verbunden“ deaktiviert. Wenn eine Station als „Hauptstation“ oder „2 Hauptstationen“ im System verwendet wird, kann sie in der Tabelle nicht aktiviert oder deaktiviert (deaktiviert) werden.
Die Zuordnung der Masterstation erfolgt in den Systemeinstellungen „Einstellungen / Masterstationseinstellungen“.

## Regen ignorieren
Wenn wir für eine bestimmte Station „Regen ignorieren“ aktivieren, wird die Station entsprechend dem Programm aktiviert, unabhängig davon, ob eine Regenverzögerung eingestellt ist oder ob der Regensensor Regen erkennt. Wir werden diese Option beispielsweise in einem Gewächshaus nutzen, in dem es nicht regnet und wir es regelmäßig gießen müssen. oder zum Beispiel, um die Filterung des Schwimmbades zu starten, das wir auch unabhängig davon reinigen, ob es regnet.

## ON Haupt?
### Nicht-Verwendung
Es wird keine Master-Station verwendet (wenn eine bestimmte Station aktiviert ist, wird die Master-Station nicht aktiviert).
### ON Haupt
Wenn wir verlangen, dass bei Aktivierung einer bestimmten Station auch die Hauptstation aktiviert wird (z. B. eine Pumpe oder ein Hauptventil mit Wasser), wählen Sie den Punkt „EIN Hauptstation?“.
### EIN Haupt 2
Wenn wir verlangen, dass bei Aktivierung einer bestimmten Station auch die zweite Hauptstation aktiviert wird (z. B. eine zweite Pumpe oder eine andere Wasserquelle), wählen Sie den Punkt „EIN Hauptstation 2?“.
### EIN Hauptprogramm 1/2
Wenn wir die Hauptstation oder die zweite Hauptstation aktivieren möchten, wählen wir im Programm den Punkt „Master 1/2 per Programm aktivieren“ aus. Für das Programm kann dann ausgewählt werden, welche Masterstation für diese Station verwendet werden soll (Beispiel: Programm 1 steuert die Stationen 1-4 und Masterstation 5. Programm 2 steuert die Stationen 1-4 und die zweite Masterstation 6).

## Notizen
Notizen werden für den Betrieb des OSPy-Systems verwendet. Es kann beispielsweise vermerkt werden, welche Art von el. Ventil, Sprinkler usw., die wir im System verwendet haben.

## Bild
Nach einem Klick auf das Fenster öffnet sich eine Seite, auf der Sie Ihr eigenes Bild auf die Station hochladen können.

----

# Sensoren
Auf der Seite „Sensoren“ können wir Sensoren hinzufügen oder löschen, die verschiedene Funktionen im OSPy-System ausführen. OSPy unterstützt derzeit Sensoren von pihrt.com und shelly.com.

## Neuen Sensor hinzufügen (von Pihrt.com)
Mit der Schaltfläche „Fügen Sie einen neuen Sensor hinzu“ wird dem System ein neuer Sensor hinzugefügt. Die Sensoreinstellungen sind unten im Abschnitt „Sensorparameter“ aufgeführt.

## Sensorparameter
Für Sensoren werden zwei Arten der Kommunikation verwendet:
* Wireless (Funk) - ID-Funksensor
* Netzwerk (Wi-Fi/LAN) – MAC-Adresse, IP-Adresse
Sie können aus verschiedenen Sensortypen wählen:
* Trockener Kontakt
* Lecksucher
* Feuchtigkeit
* Bewegung
* Temperatur
* Multisensorkontakt
* Multisensor-Lecksucher
* Multisensor-Luftfeuchtigkeit
* Multisensor-Bewegung
* Multisensor-Temperatur
* Multisensor-Ultraschall
* Multisensor-Bodenfeuchtigkeit

### Sensor aktivieren
Aktivieren oder deaktivieren Sie diesen Sensor.

### Name des Sensors
Geben Sie den Sensornamen ein. Sensornamen müssen ungleich Null und eindeutig sein.

### Sensortyp
Wählen Sie den Sensortyp aus.

#### Trockener Kontakt
* Programme öffnen Markieren Sie die gewünschten Programme, die ausgeführt werden sollen.
* Oder stoppen Sie diese laufenden Stationen im Scheduler.
* Geschlossene(s) Programm(e) Markieren Sie die gewünschten Programme zur Ausführung.
* Oder stoppen Sie diese laufenden Stationen im Scheduler.

#### Lecksucher
* Empfindlichkeit (0-100 %) Das Überschreiten dieser Stufe aktiviert das/die Hochprogramm(e).
* Stabilisierungszeit (mm:ss) Nach dieser eingestellten Zeit reagiert der Melder nicht mehr auf eine Änderung.
* Niedrige(s) Programm(e) Markieren Sie die gewünschten Programme zur Ausführung.
* Hoch Programm(e) Markieren Sie die gewünschten Programme zur Ausführung.

#### Feuchtigkeit
* Niedriges Niveau (0-100 %) Das Überschreiten dieses Niveaus aktiviert das/die niedrige(n) Programm(e).
* Niedrige(s) Programm(e) Markieren Sie die gewünschten Programme zur Ausführung.
* Hochniveau (0-100 %) Wenn dieses Niveau überschritten wird, werden die Hochprogramm(e) aktiviert.
* Hoch Programm(e) Markieren Sie die gewünschten Programme zur Ausführung.

#### Bewegung
* Programm(e) Markieren Sie die gewünschten Programme zur Ausführung.

#### Temperatur
* Niedriges Niveau (0-100 °C/°F) Wenn dieses Niveau überschritten wird, werden das/die niedrige(n) Programm(e) aktiviert.
* Niedrige(s) Programm(e) Markieren Sie die gewünschten Programme zur Ausführung.
* Hoher Wert (0-100 °C/°F) Wenn dieser Wert überschritten wird, werden die hohen Programme aktiviert.
* Hochprogramm(e) Markieren Sie die gewünschten Programme zur Ausführung.
Für die Temperatur werden Grad Celsius oder Grad Fahrenheit angezeigt, je nachdem, wie die Temperatur auf der Titelseite (unten rechts) eingestellt ist (Sie können die Einheiten ändern, indem Sie auf die Temperatur klicken).

#### Ultraschall
* Abstand vom Ultraschallsensor (oben) bis zum minimalen Wasserstand im Tank.
* Abstand vom Ultraschallsensor (oben) bis zum maximalen Wasserstand im Tank.
* Der minimale Wasserstand im Tank (vom Tankboden aus) für den Bericht.
* Zylinderdurchmesser zur Volumenberechnung.
* Display in liters or m3.
* Stoppen Sie die Stationen bei minimalem Wasserstand.
* Verzögerungszeit (Stunden).
* Haltestellen stoppen, wenn der Ultraschallsensor defekt ist.
* Stoppen Sie diese Stationen im Zeitplaner.
* Maximale Wasserstandsregelung.
* Maximaler Wasserstand.
* Maximale Laufzeit bei Aktivierung.
* Minimaler Wasserstand.
* Ausgabe zur Regelung.

#### Bodenfeuchtigkeit
* Sonde xx steuert das Programm (wählen Sie in der Liste der Programme das Programm aus, das Sie mit Sonde 1-16 beeinflussen möchten).
* Kalibrieren Sie die xx-Sonde auf 100 % (geben Sie den Spannungspegel in Volt ein, um die Sonde bei 100 % Luftfeuchtigkeit zu kalibrieren).
* Kalibrieren Sie die xx-Sonde auf 0 % (geben Sie den Spannungspegel in Volt ein, um die Sonde bei 0 % Luftfeuchtigkeit zu kalibrieren).

### Kommunikationstyp
Wählen Sie den Kommunikationstyp für den Sensor aus.
#### Radio
Geben Sie die Sensor-ID für Ihren Funksensor ein. Die Sensor-ID muss ungleich Null und eindeutig sein.

#### Wi-Fi / LAN
* Geben Sie die MAC-Adresse des Sensors ein. Beispiel: aa: bb: cc: dd: ee: ff
* Geben Sie die IP-Adresse des Sensors ein. Beispiel: 192.168.88.10

### Abtastrate
Geben Sie die Probenahmezeit in Minuten und Sekunden (mm:ss) ein.

### Protokollbeispiele
Probenprotokollierung aktivieren.

### Protokollereignisse
Ereignisprotokollierung aktivieren.

### Text-/E-Mail-Ereignisse
Aktivieren Sie das Senden von E-Mails, wenn ein Ereignis eintritt. Für diese Funktion ist die E-Mail-Benachrichtigungserweiterung erforderlich!

### Notizen
Hier können wir unsere Notizen machen.

## Alle Sensoren löschen
Die Schaltfläche „Alle Sensoren entfernen“ löscht alle hinzugefügten Sensoren im System.

----

## Neuen Sensor hinzufügen (von shelly.com)
Shelly-Sensoren können mithilfe der Erweiterung „Shelly Cloud Integrator“ in OSPy integriert werden, in der wir verfügbare Geräte verbinden (entweder über die Shelly.com-Cloud oder im lokalen Netzwerk).
Wir können dann in OSPy im Bereich Sensor/Suche nach diesen Geräten suchen. In OSPy können wir beispielsweise Messungen von Verbrauch, Spannung, Ausgangsstatus usw. verwenden.

----

#  Hilfe
Auf der Seite „Hilfe“ finden wir Dokumentationen zu allen Erweiterungen, System-OSPs, Systemänderungen, API-Zugriff, Webinterface.

## OSPy
### Readme
Haupt-OSPy-Dokumentation, Systeminstallation, Board-Verbindung, Lizenzen.

### Changelog
Änderungen im OSPy-System oder in Erweiterungen

### Programs
Intern verwalten alle Programme einen Zeitplan, der direkt bearbeitet werden kann (genau wie ein benutzerdefiniertes Programm).
Zur einfacheren Handhabung wurden folgende Programmtypen erstellt.
Jedes Programm kann einer dieser Typen sein. Schließlich kann jedes Programm auch als individuelles Programm geschrieben werden.<br/>

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
Hilfe für die Weboberfläche auf Tschechisch.

### Web Interface Guide - English
Hilfe zur Weboberfläche auf Englisch.

### Web Interface Guide - German
Hilfe zur Weboberfläche auf Deutsch.

### Web Interface Guide - Polish
Hilfe zur Weboberfläche auf Polnisch.

### Web Interface Guide - Russian
Hilfe zur Weboberfläche auf Russisch.

### Web Interface Guide - Serbian
Hilfe zur Weboberfläche auf Serbisch.

### Web Interface Guide - Slovak
Hilfe für die Weboberfläche auf Slowakisch.

## API
### Readme
Für moderne Webbrowser wird empfohlen, die API nach dem CRUD-Prinzip mit JSON als Datencontainerformat aufzubauen.

### Details
HTTP/s-Methodenzuordnung.

## Plugins
Der Grundaufbau aller Erweiterungen ist wie folgt:

Plugins
+ Plugin-Name
  + data
  + docs
  + static
  + script
  + templates
  + __init__.py
  \ README.md

Statische Dateien werden automatisch am folgenden Speicherort verfügbar gemacht: /plugins/plugin_name/static/...
Alle *.md-Dateien im docs-Verzeichnis werden auf der Seite „Hilfe“ angezeigt. *

### Verfügbare Erweiterungen:

* Nutzungsstatistik (anonyme Statistiken zur OSPy-Systemnutzung)
* LCD-Display (LCD-Display 16x2 Zeichen, verbunden über I2C-Bus)
* Druckwächter (Überwachung des Drucks in der Rohrleitung – Pumpenschutz)
* Sprachbenachrichtigung (Tonbenachrichtigungen – Wiedergabe von MP3-Dateien)
* Impulsausgangstest (Ausgangstest – wird verwendet, um ein bestimmtes Ventil im Boden zu finden)
* Button Control (Steuerung des OSPy-Systems über 8 Tasten – wird zum manuellen Starten von Programmen verwendet)
* CLI Control (Fernsteuerung von Peripheriegeräten über URL-Befehle – zum Beispiel RF-Sockets)
* Systemüberwachung
* Spannungs- und Temperaturmonitor (Messung von Spannung und Temperatur über den I2C-Bus)
* Remote-Benachrichtigungen (Senden von Daten an einen Remote-Server mithilfe von PHP)
* Systeminformationen (OSPy- und Linux-Systeminformationen)
* Lufttemperatur- und Luftfeuchtigkeitsmonitor (Messung der Temperatur 6x DS18B20 und der Luftfeuchtigkeit DHT11 über I2C-Bus)
* Windgeschwindigkeitsmonitor (Windgeschwindigkeitsmessung über I2C-Bus)
* Wetterbasierte Regenverzögerung
* Relaistest (testet das Relais für die Hauptpumpe)
* UPS Monitor (überwacht den Stromausfall des Systems, sendet E-Mails und fährt das Linux-System herunter)
* Wasserverbrauchszähler (virtueller Wasserdurchflussmesser basierend auf der Betriebsberechnung der Hauptstation)
* SMS Modem (Fernsteuerung per SMS und USB-Modem)
* Signalisierungsbeispiele (Beispiel für Tup-„Signal“-Benachrichtigungen im OSPy-System)
* E-Mail-Benachrichtigungen (Versenden von E-Mails vom System – einige andere Erweiterungen verwenden diese Erweiterung ebenfalls, zum Beispiel: Windgeschwindigkeitsmonitor, Druckmonitor, Lufttemperatur- und Luftfeuchtigkeitsmonitor...)
* Remote FTP Control (vereinfachte Fernsteuerung von OSPy über einen Server mit PHP und FTP)
* Systemaktualisierung (verwenden Sie diese Erweiterung, um das OSPy-System einfach über GIThub anstelle von Systembefehlen zu aktualisieren)
* Wasserzähler (Durchflussmessung mittels Wasserzähler mit Impulsausgang über den I2C-Bus)
* Webcam-Monitor (nimmt Fotos von der USB-Webcam auf)
* Wetterbasierter Wasserstand Netatmo (Einstellen der Wassermenge für die Bewässerung von der Netatmo-Wetterstation)
* Direkte 16 Relaisausgänge (mit dieser Erweiterung können wir 16 Relais (Stationen) steuern, die direkt an den Raspberry Pi angeschlossen sind, einige andere Erweiterungen sind jedoch nicht verfügbar.)
* MQTT (OSPy-Statusmeldung über das MQTT-Protokoll, Stationssteuerung über MQTT...)
* System-Debug-Informationen (Informationen darüber, was im OSPy-System passiert. Wenn wir in den Einstellungen „Debugging aktivieren“ aktiviert haben, wird hier in der Erweiterung ein gespeicherter Datensatz angezeigt)
* Wetterbasierter Wasserstand (Einstellung der Wassermenge für die Bewässerung basierend auf der Wettervorhersage)
* Echtzeit und NTP-Zeit (Erweiterung, die die Systemzeit festlegt – Linux- und HW-RTC-Zeit vom NTP-Server, HW-RTC verwendet I2C-Bus)
* Wassertank (Wasserstandsmessung mittels Ultraschall – zum Beispiel in einem Brunnen mittels I2C-Bus)
* Monatlicher Wasserstand (Einstellung der Wassermenge für einzelne Monate)
* Druckhalter (Pumpe unter Druck setzen, bevor Programme gestartet werden)
* Ping-Monitor (Messung von Netzwerkausfällen)
* Temperaturschalter (Temperaturregler, der 3 unabhängige Zonen ermöglicht)
* Poolheizung (Regelung der Pooltemperatur entsprechend der Solarheizung)
* E-Mail-Reader (Steuerung von OSPy mithilfe von E-Mail-Nachrichten)
* Wetterstationen (Anzeigewerte aus anderen Erweiterungen im Stil von Uhrzeigern) Version 1.0
* Telegram Bot (kommuniziert mit OSPy über die telegram.org-App)
* Door Opening (Öffnen des Türschlosses oder Schiebetors)
* Voice Station (Tonbenachrichtigungen basierend auf Stationsereignissen – Wiedergabe von WAV- und MP3-Dateien)
* Jalousiensteuerung (diese Erweiterung sendet Beispiele über die REST-API an Wi-Fi-Relais von Shelly oder ähnliche Relais)
* Geschwindigkeitsüberwachung der Internetverbindung (Antwort, Download, Upload)
* E-Mail-Benachrichtigungen SSL (Versenden von E-Mails vom System – einige andere Erweiterungen verwenden diese Erweiterung ebenfalls, zum Beispiel: Windgeschwindigkeitsmonitor, Druckmonitor, Lufttemperatur- und Luftfeuchtigkeitsmonitor...) Diese Erweiterung ist eine modernere Variante der ursprünglichen Erweiterung E-Mail-Benachrichtigungen (Verbindung über SSL-Schicht).
* Sonnenaufgang und Sonnenuntergang (Berechnung astronomischer Daten wie Sonnenauf- und -untergang. Nach diesen Berechnungen können Programme nachträglich ausgeführt werden).
* PV-Kessel (Kesselheizung aus dem Verteilnetz oder PV-Kraftwerk).
* IP-Kameras (ermöglicht die Überwachung von IP-Kameras. Als JPEG-Vorschau, GIF-Bild oder MJPEG-Stream von der Kamera).
* CHMI (ermöglicht Ihnen, das aktuelle Wetter vom CHMI-Wetterradar abzulesen und die Zeitverzögerung entsprechend einzustellen. Gleichzeitig den RGB-Wetterstatus auf der HW-Karte anzeigen).
* Daher (das Standard-Plugin zum Erstellen anderer neuer Plugins. Das Plugin macht nichts Besonderes, erklärt aber, wie es funktioniert).
* Label Maker (Erstellung von EAN- und QR-Codes).
* IP-Scanner (Suche nach IP und MAC im Netzwerk).
* Database Connector (Verbindung zur Datenbank zur Speicherung von Daten von Sensoren).
* OSPy Backup (Datenverzeichnissicherung von allen Erweiterungen in ZIP-Dateien).
* MQTT Home Assistant (Integration in HASS über MQTT).
* Shelly Cloud Integration (Abrufen von Zuständen aus der Cloud des Shelly-Geräteherstellers).
* Current Loop Tanks Mmonitor (Füllstandmessung von 4 Sensoren).
* Network Ping Monitor (Überwachung der Verfügbarkeit von 3 Geräten im Netzwerk).
* Weather Dashboard (Anzeigewerte aus anderen Erweiterungen im Stil von Uhrzeigern) Version 2.0
* Thermostat
----

# Abmelden
Nach dem Klicken auf die Schaltfläche „Abmelden“ meldet sich der Benutzer vom System ab.
