OSPy
###### **O**pen **S**prinkler **Py**thon
OSPy is a free Raspberry Pi based Python 3 program for controlling irrigation systems (sprinkler, drip, IoT, etc). This is my fork from [Rimco/OSPy](https://github.com/Rimco/OSPy) and [Dan-in-CA/SIP](https://github.com/Dan-in-CA/SIP) with My modifications.  

## For first installation and other visit 
[Clean installation](https://github.com/martinpihrt/OSPy/tree/master/ospy/docs/Clean_installation.md)

## Emergency administrator login recovery
If the administrator password is unknown or access to the configured two-factor method has been lost, run the local recovery script from the OSPy directory on the Raspberry Pi or another trusted local shell:

```bash
sudo service ospy stop
sudo python3 back_door.py
sudo service ospy start
```

Stop the service first so its settings database is not being written while recovery runs. The script requires typing `RESET` for confirmation and then generates a new one-time recovery password for the `admin` account. It disables passwordless access and two-factor authentication, removes the TOTP secret and backup codes, revokes remembered browser logins, and invalidates active web sessions after OSPy starts again. Irrigation programs, settings, plug-ins, and logs are not deleted. Open the login page, use the displayed recovery password, change it immediately, and configure two-factor authentication again if required. Use `sudo python3 back_door.py --yes` only in a trusted automated local recovery procedure. See [Clean installation](https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Clean_installation.md) for more information.

## Hardware relay board test before starting OSPy
The standalone `relay_test.py` script can verify the relay board and GPIO wiring before OSPy is started, or help diagnose a board fault. It switches all eight shift-register relay outputs and the additional main relay output on and off together every 1.5 seconds.

**Warning:** Disconnect pumps, valves, contactors, and any other equipment that must not start unexpectedly. The test energizes every relay. Do not run it while the OSPy service is controlling the same GPIO pins.

From the OSPy directory run:

```bash
sudo service ospy stop
sudo python3 relay_test.py
```

Watch or listen for every relay switching. Stop the test with `Ctrl+C`; the script disables the outputs and cleans up GPIO in its `finally` block. OSPy can then be started normally:

```bash
sudo service ospy start
```

## More information visit
[Pihrt.com](https://pihrt.com/elektronika/248-moje-rapsberry-pi-zavlazovani-zahrady) and [OpenSprinkler](https://opensprinkler.cz  )

YouTube OpenSprinkler channel</br>
[![](https://github.com/martinpihrt/OSPy/blob/master/ospy/images/yt.png?raw=true)](https://youtube.com/playlist?list=PLZt973B9se__UN_CVyOoy1_lr-ZSlSv0L)

## Hardware diagram
[![](https://github.com/martinpihrt/OSPy/blob/master/ospy/images/blockconnection_mini.png?raw=true)](https://github.com/martinpihrt/OSPy/blob/master/ospy/images/blockconnection.png)

## Multisensor ESP32 and Shelly.com
[![](https://github.com/martinpihrt/OSPy/blob/master/ospy/images/esp32multi_mini.png?raw=true)](https://github.com/martinpihrt/OSPy/blob/master/ospy/images/esp32multi.png)</br>
[![](https://github.com/martinpihrt/OSPy/blob/master/ospy/images/esp32multi3D_mini.png?raw=true)](https://github.com/martinpihrt/OSPy/blob/master/ospy/images/esp32multi3D.png)</br>
[Sensors by Pihrt.com](https://pihrt.com/elektronika/444-esp32-multisnimac-pro-opensprinkler-system)</br>
[Sensors by Shelly.com](https://www.shelly.com/collections/smart-monitoring-saving-energy)

## For translate OSPy to other language
The OSPy system is currently available in multiple languages. For available [languages](https://github.com/martinpihrt/OSPy/tree/master/i18n) and step by step, how to use is typed in MD file
Any user who joins the "OSPy" project is welcome! Translation of strings into other languages is not demanding (using the [Poedit](https://poedit.net/))

## Changelog and Issues
* [Changelog](https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Changelog.md)
* [Issues](https://github.com/martinpihrt/OSPy/issues)

## Help with to user web Interfaces
* [Czech help page](https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Web%20Interface%20Guide%20-%20Czech.md)
* [English help page](https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Web%20Interface%20Guide%20-%20English.md)
* [German help page](https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Web%20Interface%20Guide%20-%20German.md)
* [Polish help page](https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Web%20Interface%20Guide%20-%20Polish.md)
* [Russian help page](https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Web%20Interface%20Guide%20-%20Russian.md)
* [Serbian help page](https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Web%20Interface%20Guide%20-%20Serbian.md)
* [Slovak help page](https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Web%20Interface%20Guide%20-%20Slovak.md)

## Communication with other systems
OSPy can be controlled and monitored using HTTP GET commands. With the addition of available plugins OSPy can communicate with other systems via MQTT. OSPy can also issue Linux shell commands when a station is turned on or off. This is useful for controlling wireless remote devices and for I²C relay hats and boards. The Blinker package that is shipped with OSPy sends messages to other Python modules such as plugins to report changes in status. See the signaling examples file in OSPy's plugins folder for examples. Homeassistant integration via MQTT plugin.

## Sensors
OSPy allows to read data from wireless sensors (ESP32, ESP8266...) [Docs](https://github.com/martinpihrt/OSPy/blob/master/hardware_pcb/sensors_pcb_fw/docs/Details.md)
Shelly sensors and periphery [Sensors by Shelly.com](https://www.shelly.com/)

## Remote Controller for OSPy based on M5stick-C 
This controller allows you to select a program stored in the OSPy on the LCD display and start it with the button. The controller is connected to the home Wi-Fi network. We do not even need a mobile phone or a computer to quickly select programs. We will use this miniature controller. [Docs](https://github.com/martinpihrt/OSPy/blob/master/hardware_pcb/remote_controllers_fw/docs/Details.md)

## License
OpenSprinkler Py (OSPy) Interval Program
Creative Commons Attribution-ShareAlike 3.0 license

## Acknowledgements
Full credit goes to Dan for his generous contributions in porting the microcontroller firmware to Python.
* The program makes use of web.py (http://webpy.org) for the web interface.
* The program makes use of cmarkgfm (https://github.com/theacodes/cmarkgfm) to render the help pages written in GitHub flavored markdown (Python 3+).
* The program makes use of OpenStreetMap (https://www.openstreetmap.org) to convert locations into coordinates.
* The program makes use of Stormglass API (https://stormglass.io/) for weather information.
* The program makes use Blinker (https://pythonhosted.org/blinker/) package that is shipped with OSPy sends messages to other Python modules such as plugins to report changes in status.
* The program makes use Arduino (https://arduino.cc) ESP32, Atmega328 and more HW boards pro OSPy aditional sensors, water tank monitor.
