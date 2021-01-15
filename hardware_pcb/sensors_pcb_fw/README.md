OSPy Sensors ESP32 Readme 
====

## More information visit
[pihrt.com Martin Pihrt website](https://pihrt.com/) and [Arduino core for the ESP32 website](https://github.com/espressif/arduino-esp32)

INSTALLATION:
===========

### Arduino IDE in operating system (Linux or Windows)
- Install the current upstream Arduino IDE at the 1.8 level or later. The current version is at the [Arduino website](http://www.arduino.cc/en/main/software).
- Start Arduino and open Preferences window.
- Enter one of the release links above into *Additional Board Manager URLs* field. You can add multiple URLs, separating them with commas.
- Open Boards Manager from Tools > Board menu and install *esp32* platform (and don't forget to select your ESP32 board from Tools > Board menu after installation).
- Extract the OneWire and Dallas Temperature folders from the esp32/library folder. Then copy the folders to your arduino library location. Example: documents/arduino/libraries
- More infos with images is here: https://pihrt.com/elektronika/439-ospy-jak-pridat-a-pripojit-snimace


## Acknowledgements
Arduino IDE software (https://arduino.cc).
Arduino core for the ESP32 website (https://github.com/espressif/arduino-esp32).
DS18B20 libraries (https://www.arduinolibraries.info/libraries/dallas-temperature).
OneWire libraries (https://www.arduinolibraries.info/libraries/one-wire).


Sensor ESP32 FW Changelog
====

FW: 1.03
-----------
(martinpihrt)<br/>
Changes:<br/>
Add upload new firmware via web. Dry contact and motion now support pull-up or pull-down connection. Add manual relay on/off with AP button (if press time < 2 sec). Voltage check with R1=100K and R2=10K as divider from source to analog pin ESP32. Add CSS style (OpenSprinkler design). Add print time to reboot on pages. Fix read temperature 85C from 4x DS18B20.
 
FW: 1.02
-----------
(martinpihrt)<br/>
Changes:<br/>
Add AP manager for settings sensor from phone, tablet (4 minutes timeout). For run AP manager: push button least > 2 seconds. Password for AP Wi-Fi is "ospy-sensor-esp32", next open browser and type IP "192.168.1.1".<br/>
Add saving to eeprom memory. Fast blinking LED if AP manager. Slow blinking LED if normal run.<br/>
Add control relay from stations: ex: http://IP/securecode?re=1 (or re=0). In AP manager is active button  for control relay ON or OFF. Available only on the same network as OSPy.

FW: 1.01
-----------
(martinpihrt)<br/>
Changes:<br/>
Initial sensor version without AP manager.


