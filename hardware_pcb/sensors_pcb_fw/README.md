OSPy Sensors ESP32 by www.pihrt.com and ESP8266 (by Sonoff THxx) Readme 
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
- ESP8266 *URLs for Additional Board Manager* https://arduino.esp8266.com/stable/package_esp8266com_index.json
- For ESP32 Open Boards Manager from Tools > Board menu and install *esp32* platform (and don't forget to select your ESP32 board from Tools > Board menu after installation).
- For ESp8266 Open Boards Manager from Tools > Board menu and install *esp8266* platform (and don't forget to select your ESP8266 board from Tools > Board menu after installation).
- Extract the OneWire and Dallas Temperature folders from the esp32/library folder. Then copy the folders to your arduino library location. Example: documents/arduino/libraries
- More infos with images is here: https://pihrt.com/elektronika/444-esp32-multisnimac-pro-opensprinkler-system and https://pihrt.com/elektronika/439-ospy-jak-pridat-a-pripojit-snimace


## Acknowledgements
Arduino IDE software (https://arduino.cc).
Arduino core for the ESP32 website (https://github.com/espressif/arduino-esp32).
Arduino core for the ESP8266 website (https://github.com/esp8266/Arduino).
DS18B20 libraries (https://www.arduinolibraries.info/libraries/dallas-temperature).
OneWire libraries (https://www.arduinolibraries.info/libraries/one-wire).
Adafruit DHT libraries (https://github.com/adafruit/DHT-sensor-library).
SparkFun HTU21 libraries (https://github.com/sparkfun/SparkFun_HTU21D_Breakout_Arduino_Library).

Sensor ESP8266 FW Changelog
====

FW: 1.01
-----------
(martinpihrt)<br/>
Changes:<br/>
Working on it.


Sensor ESP32 FW Changelog
====

FW: 1.10
-----------
(martinpihrt)<br/>
Changes:<br/>
Added function to webserver for starting AP manager from OSPy.

FW: 1.09
-----------
(martinpihrt)<br/>
Changes:<br/>
Added fake test for DS1-DS4 DS18B20 sensors (China clone sensors).

FW: 1.08
-----------
(martinpihrt)<br/>
Changes:<br/>
Added flash state to LED when the sensor is connecting to a Wi-Fi network. Added if the sensor is disconnected from Wi-Fi, the sensor will restart immediately. Added new parameter running time for relay outputs (ex: http://192.168.88.207/0123456789abcdef?re=1&run=120 re=1 is relay on and run=xxx is time in seconds 0123456789abcdff is secure code from sensor. If the run parameter is not specified, it will be ignored).

FW: 1.07
-----------
(martinpihrt)<br/>
Changes:<br/>
Fix time for AP manager to 10 minutes. Fix message in serial print. Add calibration for voltage divider in to AP settings. Divider correction (+-) = if we need to fine-tune the exact value of the voltage measurement 0-30V, then we can use the + - value for this adjustment. Example: the displayed voltage value is 10.7V and the actual value should be 12.7V (measured by a voltmeter on the main power input). Enter the value 20 in the field. The entered value is multiplied by the number 0.1 during the calculation. Add LED ON if relay is ON. Add ultrasonic support for distance level (not tested yet). Tested probe DHT22 and DHT11 for moisture measuring.

FW: 1.06
-----------
(martinpihrt)<br/>
Changes:<br/>
Add time limit for sending data (if it was not sent to the OSPy within 2 minutes, then restart the sensor). Sensor freeze prevention. 

FW: 1.05
-----------
(martinpihrt)<br/>
Changes:<br/>
Add selector for moisture probe type - user changeable (in AP mode). 
Add password for access to upload new firmware via http in STA (normal) mode - user changeable. For uploading in STA mode use html post "/FW_YOURUPLOADPASSWORD".
Add password for Wi-Fi access - user changeable (in AP mode).
Add moisture sensors DHT22 (AM2302, AM2321), DHT 21 (AM2301), DHT11 - used SDA pin GPIO33 (not used I2C bus).
Add moisture sensor SHT21 (HTU21D) used I2C bus.

FW: 1.04
-----------
(martinpihrt)<br/>
Changes:<br/>
Add leak detector to input via interrupt routine. If leak pulses > 0 sending http data in cycle 3 seconds (normal is 30 seconds). Add I2C scanner routine for find I2C addreses (for moisture and more sensors)

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


