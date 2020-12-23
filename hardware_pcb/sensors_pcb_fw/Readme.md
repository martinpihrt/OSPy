OSPy Sensors Readme 
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


