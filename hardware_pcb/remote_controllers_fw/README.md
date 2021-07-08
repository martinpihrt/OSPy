OSPy Remote Controllers
====

## More information visit
[pihrt.com Martin Pihrt website](https://pihrt.com/) and [Arduino core for the ESP32 website](https://github.com/espressif/arduino-esp32)

INSTALLATION:
===========

### Arduino IDE in operating system (Linux or Windows)
- Install the current upstream Arduino IDE at the 1.8 level or later. The current version is at the [Arduino website](http://www.arduino.cc/en/main/software).
- Start Arduino and open Preferences window.
- Enter one of the release links above into *Additional Board Manager URLs* field. You can add multiple URLs, separating them with commas.
- ESP32 *URLs for Additional Board Manager* https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
- For ESP32 Open Boards Manager from Tools > Board menu and install *esp32* platform (and don't forget to select your ESP32 board from Tools > Board menu after installation).

## Acknowledgements
Arduino IDE software (https://arduino.cc).
Arduino core for the ESP32 website (https://github.com/espressif/arduino-esp32).

Remote Controller - M5STICK-C FW Changelog
====

FW: 1.01
-----------
(martinpihrt)<br/>
Changes:<br/>
Add checker for enable or disable read NTP time. Add baterry status (percentage and rectangle). Added battery saving (after 10 seconds the brightness of the LCD display decreases). If the any button is pressed, the brightness is restored to maximal brightness).

FW: 1.00
-----------
(martinpihrt)<br/>
Changes:<br/>
Initial version.


