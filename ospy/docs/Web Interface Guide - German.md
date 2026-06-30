OSPy Weboberflaechen-Handbuch auf Deutsch
====

    OSPy-Installation
    Anmeldung
    Startseite
    Programme
    Einmal ausfuehren
    Erweiterungen
    Protokoll
    Einstellungen
    Stationen
    Sensoren
    Hilfe
    Abmelden

----

# OSPy-Installation
Es wird empfohlen, OSPy sauber mit einer aktuellen Python-3-Version zu installieren. Beim ersten Start werden Anmeldedaten erzeugt. Nach der ersten Anmeldung sollten Benutzername und Passwort in den Einstellungen geaendert werden.

## Installationsskript
Melden Sie sich per SSH am Raspberry Pi an und fuehren Sie aus:

```bash
wget https://raw.githubusercontent.com/martinpihrt/OSPy/master/ospy_setup.sh
sudo bash ospy_setup.sh
```

Folgen Sie dem Installationsmenue. Nach Abschluss der Installation wird der Raspberry Pi neu gestartet und OSPy ist ueber die Weboberflaeche erreichbar.

----

# Anmeldung
Die Anmeldeseite enthaelt Felder fuer Benutzername und Passwort. Der Standardbenutzer ist `admin`. Bei einer Neuinstallation wird ein zufaelliges Passwort erzeugt. Aendern Sie dieses Passwort nach der ersten Anmeldung in den Einstellungen.

----

# Startseite
Die Startseite ist die Hauptuebersicht des Systems. Sie zeigt Uhrzeit, Navigationsleiste, globale Steuerungen, Zeitachse, Diagramme, Systeminformationen und von Erweiterungen bereitgestellte Zusatzanzeigen.

## Normal - Wasserstand
Legt den globalen Wasserstand in Prozent fest. Dieser Wert beeinflusst die Laufzeit der Bewaesserungsprogramme.

## Aktiv - Regenverzoegerung
Setzt eine Regenverzoegerung. Stationen, die Regen nicht ignorieren, werden fuer die eingestellte Zeit blockiert.

## Zeitplan - Manuell
Schaltet zwischen automatischem Zeitplanbetrieb und manueller Stationssteuerung um.

## Aktiviert - Deaktiviert
Aktiviert oder deaktiviert den allgemeinen Betrieb von OSPy.

## Alle Stationen stoppen
Stoppt sofort laufende Programme oder Stationen.

## Wasserbilanz-Diagramm
Wenn Programme vorhanden sind, zeigt die Startseite ein Diagramm der gelieferten Wassermenge pro Station oder Programm.

## Regenverzoegerung / Regen erkannt
Wenn Regenverzoegerung oder Regensensor aktiv sind, werden betroffene Stationen blockiert.

## CPU, Version, externe IP und Laufzeit
Die Fusszeile zeigt CPU-Temperatur, CPU-Auslastung, Softwareversion, externe IP-Adresse und Systemlaufzeit.

----

# Programme
Auf der Programmseite werden Bewaesserungsprogramme erstellt, organisiert und gesteuert.

## Neues Programm hinzufuegen
Erstellt ein neues Programm im Zeitplan.

## Programmgruppen
Programme koennen in einklappbare Gruppen sortiert werden. Das ist hilfreich fuer saisonale Programme, zum Beispiel Sommer- und Winterbetrieb.

## Gruppe hinzufuegen
Erstellt eine neue Programmgruppe.

## Gruppe umbenennen
Aendert nur den Namen der Gruppe. Die enthaltenen Programme bleiben erhalten.

## Gruppe aktivieren oder deaktivieren
Schaltet alle Programme einer Gruppe auf einmal ein oder aus.

## Gruppe kopieren
Erstellt eine Kopie der Gruppe mit kopierten Programmen. Kopierte Programme sind zuerst deaktiviert.

## Gruppe loeschen
Beim Loeschen wird eine Bestaetigung verlangt. Programme aus der geloeschten Gruppe werden in die Standardgruppe verschoben.

## Jetzt ausfuehren
Startet das Programm sofort, unabhaengig vom geplanten Zeitpunkt.

## Bearbeiten
Oeffnet die Einstellungen eines bestehenden Programms.

## Kopieren
Erstellt eine deaktivierte Kopie des Programms, damit sie vor dem Einsatz geprueft werden kann.

## In Gruppe verschieben
Ordnet ein Programm einer anderen Gruppe zu.

## Alle loeschen
Loescht nach Bestaetigung alle Programme.

## Programm aktivieren oder deaktivieren
Der ON/OFF-Schalter aktiviert oder deaktiviert ein einzelnes Programm.

## Konfliktwarnungen
Beim Speichern prueft OSPy aktivierte Programme auf zeitliche Ueberschneidungen derselben Station oder desselben Ausgangs. Die Warnung blockiert nichts automatisch, zeigt aber die Ueberschneidung an.

## Zeitplantyp
Verfuegbare Typen sind ausgewaehlte Tage, Wiederholung, woechentlich, benutzerdefiniert und wetterbasierte Programme. Je nach Typ werden Startzeit, Dauer, Wiederholungen, Pausen, Intervall, Wochentage oder Prioritaeten eingestellt.

## Keine Anpassungen
Fuer dieses Programm werden keine automatischen Laufzeitanpassungen angewendet.

## Abschneiden
Wenn die angepasste Laufzeit unter dem eingestellten Grenzwert liegt, wird das Programm uebersprungen.

## Master aktivieren
Stationen mit der Einstellung "Master 1/2 durch Programm aktivieren" verwenden die im Programm ausgewaehlte Masterstation.

----

# Einmal ausfuehren
Diese Seite dient zum Testen oder fuer eine einmalige Bewaesserung. Fuer jede aktivierte Station koennen Minuten und Sekunden gesetzt werden.

## Jetzt ausfuehren
Startet die ausgewaehlten Stationen.

## Zeit zuruecksetzen
Loescht die voreingestellten Zeiten.

----

# Erweiterungen
Die Erweiterungsseite verwaltet installierte und verfuegbare Plugins.

## Verwalten
Oeffnet den Erweiterungsmanager. Plugins koennen aktiviert, deaktiviert, installiert oder aktualisiert werden.

## Neue Erweiterung installieren
Oeffnet die Liste verfuegbarer Erweiterungen aus dem Repository.

## Eigene Erweiterung (ZIP)
Installiert ein Plugin aus einer ZIP-Datei. Die ZIP-Datei muss die vollstaendige Plugin-Struktur enthalten.

## Alle deaktivieren / Alle aktivieren
Schaltet alle installierten Erweiterungen aus oder ein.

## Update-Pruefung aktivieren
Prueft automatisch, ob neue Plugin-Versionen verfuegbar sind.

## Aenderungen laden / Aenderungen
Laedt und zeigt die neuesten Aenderungen aus dem Plugin-Repository.

## Automatische Updates
Aktualisiert Plugins automatisch, wenn eine neue Version verfuegbar ist. OSPy sollte zuerst aktualisiert werden, danach die Plugins.

----

# Protokoll
Die Protokollseite zeigt Bewaesserungs-, E-Mail- und Ereignisprotokolle. Protokolle koennen als CSV heruntergeladen oder geloescht werden. Loeschaktionen sind endgueltig.

----

# Einstellungen
Die Einstellungsseite enthaelt aufklappbare Bereiche fuer System, Wetter, Benutzer, Sicherheit, Sensoren, Stationen, Masterstationen, Regensensor, Protokollierung, Neustart, Backup und SSL.

## System
Hier werden Systemname, Design, Uhrformat, HTTP/S-Adresse und Port, Sprache, Stationsbilder sowie Anzeigen auf der Startseite eingestellt.

## Wetter
Aktiviert Wetterfunktionen, API-Schluessel und Standortdaten.

## Benutzer
Verwaltet Anmeldung, Passwort und zusaetzliche Benutzer. Aus Sicherheitsgruenden sollte das Standardpasswort geaendert werden.

## Sicherheit
Enthaelt Formularschutz, HTTPS-Zugriff, Domainname, eigene HTTPS-Zertifikate und API-Zugriffsoptionen.

### API CORS allowed origin
Diese Option steuert den Header `Access-Control-Allow-Origin`, den die API fuer browserbasierte Clients verwendet. `*` erlaubt jeden Origin, ein einzelner Wert wie `https://example.com` erlaubt nur diesen Origin, mehrere Origins koennen durch Kommas getrennt werden, und ein leerer Wert deaktiviert CORS-Header. Dies ersetzt nicht die API-Anmeldung; es steuert nur, welche Browser-Origins API-Antworten lesen duerfen.

### Enable API JSONP
Diese Option aktiviert den alten Parameter `callback` fuer JSONP-Antworten der API. Lassen Sie sie deaktiviert, sofern keine alte Integration JSONP benoetigt. Normale API-Clients sollten JSON mit CORS verwenden.

### Remembered browser logins
Die Login-Seite kann einen Browser mit einem langfristigen zufaelligen Token in einem sicheren Cookie merken. OSPy speichert nur einen Hash dieses Tokens, nicht das Benutzerpasswort. Mit der Schaltflaeche Revoke werden alle gemerkten Browser-Logins geloescht; betroffene Browser muessen sich wieder mit Passwort anmelden.

## Sensoren
Legt das Passwort fuer Firmware-Uploads zu Sensoren fest.

## Stationsbehandlung
Legt maximale Nutzung, Anzahl der Ausgaenge, die Pause zwischen Stationen und die minimale Laufzeit fest. Die maximale Nutzung bestimmt, ob Stationen gleichzeitig laufen duerfen. `0` bedeutet keine Begrenzung, `1` bedeutet eine Station zur gleichen Zeit, wenn jede Station Nutzung `1` hat.

Die Pause zwischen Stationen wird zwischen nacheinander laufenden Stationen eingefuegt, wenn der Planer sie nicht gleichzeitig starten kann. Sie verschiebt eine Station nicht gegenueber der Masterstation. Beispiel: Bei maximaler Nutzung `1` und Stationsnutzung `1` startet Wert `30` die naechste Station 30 Sekunden nach Ende der vorherigen Station.

Die minimale Laufzeit kann diese Pause ueberspringen, wenn der vorherige Lauf kuerzer war. Beispiel: Bei Pause `30` und Mindestlaufzeit `10` erzwingt eine Station, die nur 5 Sekunden lief, keine Pause von 30 Sekunden.

## Masterstationen
Konfiguriert Masterstation 1, Masterstation 2 und die Zeitversatzwerte fuer Ein- und Ausschalten. Eine Masterstation ist normalerweise eine Pumpe oder ein Hauptwasserventil und wird nur fuer Stationen verwendet, denen ein Master zugeordnet ist.

Der Startversatz ist relativ zum Start der Station. Negative Werte starten den Master frueher, positive Werte spaeter. Beispiel: `-10` startet den Master 10 Sekunden vor der Station, `+10` startet ihn 10 Sekunden nach der Station.

Der Stoppversatz ist relativ zum Ende der Station. Negative Werte stoppen den Master frueher, positive Werte lassen ihn laenger laufen. Beispiel: `-5` stoppt den Master 5 Sekunden vor Ende der Station, `+20` stoppt ihn 20 Sekunden nach Ende der Station.

Die gleiche Logik gilt fuer Masterstation 2, die eigene Start- und Stoppversatzwerte hat.

## Regensensor
Aktiviert den Regensensor, legt den Schaltertyp und die Regenverzoegerung fest.

## Protokollierung
Aktiviert Lauf-, E-Mail-, Ereignis- und Debugprotokolle und legt maximale Eintraege fest.

## Systemneustart
Erlaubt Software-Neustart, Raspberry-Pi-Neustart, Herunterfahren und Zuruecksetzen auf Standardwerte.

## Systembackup
Ermoeglicht Download und Upload einer Sicherung der OSPy-Konfiguration.

## SSL-Zertifikat
Eigene Zertifikate koennen hochgeladen oder im System erzeugt werden.

----

# Stationen
Auf der Stationsseite werden Name, Nutzung, Niederschlag, Kapazitaet, ETo-Faktor, Wasserbilanz, Verbindung, Regen ignorieren, Masterverhalten, Notizen und Bilder verwaltet.

----

# Sensoren
Auf der Sensorseite koennen Sensoren hinzugefuegt oder geloescht werden. Unterstuetzt werden Funk- und Netzwerkkommunikation sowie Sensortypen wie Trockenkontakt, Leck, Feuchte, Bewegung, Temperatur, Ultraschall und Bodenfeuchte.

## Shelly-Sensoren
Shelly-Geraete koennen ueber die Shelly-Cloud-Integration eingebunden und danach in OSPy verwendet werden.

----

# Hilfe
Die Hilfeseite enthaelt Dokumentation zu OSPy, API, Hardware und Plugins. Markdown-Dateien aus den Dokumentationsordnern werden automatisch angezeigt.

----

# Abmelden
Die Schaltflaeche zum Abmelden beendet die aktuelle Websitzung.

----
