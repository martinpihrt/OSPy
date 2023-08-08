OSPy Changelog
====

August 8 2023 (v3.0)
-----------
(martinpihrt)<br/>
Updating the Czech language (new strings) for Proto plugin. Added new plugin "Proto". The proto plugin is designed as a starting point for creating new plugin for OSPy. It does not perform any useful action but contains the basic components necessary for a functioning plugin. More detailed information can be found directly in the plugin on the help page. In the weather.py, the loading of the location has been fixed even without the need to enter the api for stormglass, or the need to enable the stormglass service (the location is used by the CHMI plugin). Added display of data from plugins for display on stations timeline: which allow this (now for future use) alongside the countdown of station running time on the home page timeline. For example, flow in liters per minute, or engine speed (only if station status is ON). Example is here: https://github.com/martinpihrt/OSPy/tree/master/ospy/images/show_sdata.png.

August 4 2023 (v3.0)
-----------
(martinpihrt)<br/>
Updating the Czech language (new strings) for CHMI plugin (added logging).

August 1 2023 (v3.0)
-----------
(martinpihrt)<br/>
Added get function to /api/balances and /api/pluginfooter (for future use in the mobile application). More doc in OSPy help API Details.md.

July 31 2023 (v3.0)
-----------
(martinpihrt)<br/>
Updating the Czech language (new strings) for CHMI plugin. Fix user login (public, user, admin). Added get function to /api/user to find out what permissions the logged in user has (for future use in the mobile application).

July 30 2023 (v3.0)
-----------
(martinpihrt)<br/>
Updating the Czech language (new strings) for new CHMI plugin. Example is here: https://github.com/martinpihrt/OSPy-plugins/blob/master/plugins/chmi/static/images/meteomap.png. The plugin can detect whether it is raining in the set location from the weather radar and possibly set a rain delay.

July 26 2023 (v3.0)
-----------
(martinpihrt)<br/>
Updating the Czech language (new strings). Bug fixed: if the program is running and a time rain delay occurs, the station did not turn off.

July 25 2023 (v3.0)
-----------
(martinpihrt)<br/>
Reworked automatic login (now you can set auto-login from different devices individually. Added a check box on the login page. Canceled in OSPy settings). All dependency on Python 2 has been dropped in OSPy. The name and password for automatic login are stored encrypted in the browsers local storage. Updating the Czech language (new strings).

July 11 2023 (v3.0)
-----------
(martinpihrt)<br/>
Updating the Czech language (new strings). Tested new plugin CHMI. Added new function to wind speed plugin (not tested yet). Removed python 2 dependency from all plugins.

July 01 2023 (v3.0)
-----------
(martinpihrt)<br/>
Fixed a bug with the window about available updates popping up on the home page. When the update check is turned off in the plugins settings, the notification window will not pop up on the home page. Phasing out support for Python 2 in plugins. Added a new CHMI plugin that is under development.

May 25 2023 (v3.0)
-----------
(martinpihrt)<br/>
Attention Python 2 will not be supported from this update. If you want to continue using Python 2, do not update to newer versions of OSPy!
Update jquery.min.js from 3.6.0 to 3.7.0. (https://blog.jquery.com/2023/05/11/jquery-3-7-0-released-staying-in-order/). Remains the same (it is the current latest version) gauge.min.js 2.1.7 (https://canvas-gauges.com/download/). Update web.py to latest stable release 0.62 (only supports Python >= 3.5 https://github.com/webpy/webpy). Python 2 will be phased out and removed from OSPy.

May 24 2023 (v3.0)
-----------
(martinpihrt)<br/>
Added Wi-Fi signal level and power supply voltage logging to multisensors in OSPy (logging to graph).

May 02 2023 (v3.0)
-----------
(martinpihrt, Rimco)<br/>
Fixed service startup in Python 3. Dark Sky API - support for the Dark Sky API will has ended on March 31st, 2023. Dark Sky API is newly replaced by stormglass.io API (The service is free for 10 calls per day). Fixed Czech languages for new String. Added Wi-Fi signal level and power supply voltage logging to multisensors in OSPy (logging to record). Updated Plug-in weather based rain delay to work with Storm Glass API data.

November 11 2022 (v3.0)
-----------
(martinpihrt)<br/>
Changes:<br/>
Fix on the "settings" page (help was displayed when the page was opened and should have been hidden until the user clicked the "help" button).

September 13 2022 (v3.0)
-----------
(martinpihrt)<br/>
Changes:<br/>
Updating the Czech and Slovak language. Fixed error in stations in python 3 (when the number of stations is changed and the master station is not used). The modbus station extension is tested and ready to use.

September 10 2022 (v3.0)
-----------
(martinpihrt)<br/>
Changes:<br/>
Updating the Slovak language (thank you Tomáš Szepesi).

September 9 2022 (v3.0)
-----------
(Rimco)<br/>
Changes:<br/>
Slight improvement to clean up the logging a bit more.<br/>
(martinpihrt)<br/>
Changes:<br/>
Added tooltip to addon manager for future use (packages translation). Updating the Czech language. Tested new feature and fixed bugs in Multi Contact sensors. Added Blue style template to OSPy options.

July 25 2022 (v3.0)
-----------
(martinpihrt)<br/>
Changes:<br/>
Fixed problems on the home page (admin, user, public) with the display of values from sensors (if there were more sensors, not all of them were displayed). Added new plugin "Modbus Stations" (under construction...) This plugin can be used to control devices via modbus protocol (ex. relay boards).

July 23 2022 (v3.0)
-----------
(martinpihrt)<br/>
Changes:<br/>
Updating the Slovak language (thank you Tomáš Szepesi) and the Czech language. Added new option in sensors (Multi Contact) for 7 switch inputs. I2C Bus for OLED display is not changed (not 8 switchs). Not tested (neither FW nor OSPy) but should work. Any detected errors will be subsequently removed. ESP32 firmware update version 1.19:
Added support for multi contact input (the multi sensor will act as a 7 button controller). 

July 18 2022 (v3.0)
-----------
(martinpihrt)<br/>
Changes:<br/>
Updating the Czech language. Added new plugin "IP CAM". Fix in "pressurizer" plugin.

July 1 2022 (v3.0)
-----------
(martinpihrt)<br/>
Changes:<br/>
Updating the Slovak language (thank you Tomáš Szepesi) and the Czech language. Added secondary time to "Photovoltaic Boiler" plugin and fixed known bugs. The plugin "astro sunrise and sunset" is ready to use (but still needs to be properly tested).

June 26 2022 (v3.0)
-----------
(martinpihrt)<br/>
Changes:<br/>
Czech language strings update. Add new plugin "Photovoltaic Boiler". PV boiler (heating boiler from the distribution network or FVE power plant).

July 19 2022 (v3.0)
-----------
(MartinPihrtJR)<br/>
Changes:<br/>
Added automatical login (in OSPy options under user). Browser remembers your login information and logs you in. Added enter support on login page (username or password field must be focused).

July 11 2022 (v3.0)
-----------
(martinpihrt)<br/>
Changes:<br/>
Corrections in OSPy settings: OSPy backup to zip, restore from zip, delete to default. Update of the translation in the Czech language. After this update, it is necessary to create a new backup (in the OSPy settings menu - backup and restore). Backups made before this update will not work!

June 28 2022 (v3.0)
-----------
(martinpihrt)<br/>
Changes:<br/>
Plugin "tank monitor" added new FW 1.4 for CPU atmega with CRC8 calculation. Plugin "astro sunrise and sunset" added menu for selecting programs to run. Czech language update.

June 24 2022 (v3.0)
-----------
(martinpihrt)<br/>
Changes:<br/>
Czech language strings update. Add new plugin "Astro sunrise and sunset". This extension allows you to run a specific program depending on sunrise or sunset. This extension calculate the following astronomical data. !!!I am working on the plugin, not ready to use. At this point, he can read astronomical data, but he has nothing to control yet!!!
Plugin "Tank monitor" At this point, the debug on I2C bus (to detect errors) has been added. For FW version: 1.3 Ping 255cm is thrown away. The value will be correctly from 0 to 254cm and from 256cm to 400cm. In the future version of FW: 1.4, CRC check will be added to transfer data and thus exclude errors (interference on bus I2C).

June 20 2022 (v3.0)
-----------
(martinpihrt)<br/>
Changes:<br/>
Fix in "system information" plugin (show all available I2C addresses. Custom functions instead of Linux command sudo i2cdetect -y 1). Added e-mail client selection for all multisensors (E-mail notifications V1 or E-mail notifications V2 SSL). Finding solutions to random read errors in the "tank monitor" extension. Czech language strings update.

June 15 2022 (v3.0)
-----------
(martinpihrt)<br/>
Changes:<br/>
Add new plugin "Email Notifications SSL". This extension is a more modern variant of the original E-mail Notifications (secured with SSL Connection) extension. This extension is for Python 3 only. All plugins that use sending e-mail will be supplemented with an option from with extension the e-mail will be sent. In the future, we recommend going to this plugin and using a secure SSL connection via port 465.<br />
If you use Gmail for send emails: After may 30, 2022 that using the "less secure apps" option will no longer be available. If Two-Factor Authentication Is Enabled, Generate An App Password. Generate the app passwords to fix the Gmail SMTP not working issue. This will enable you to send emails to a third party. Here's how to do it: In Gmail, go to My Account and select Security. After that, scroll down and select Signing in to Google from the drop-down menu. Now select App Password from the drop-down menu. To enable two-factor authentication, follow these steps: Select Two-step Verification from the Signing into Google menu, and then input your password. Then activate two-step verification by entering the OTP number that was sent to your phone. You'll see a list of applications here; select the one you need. Next, select the Select Device option and select the device that is currently being used to access Gmail. Now press the Generate button. Then, in the Yellow bar, type the password displayed. Finally, click Done.

June 8 2022 (v3.0)
-----------
(martinpihrt)<br/>
Changes:<br/>
Fix in plugin "air temperature" (regulation time mm:ss) and added new function in plugin "pool heating" (safety shutdown. Simply put, if the temperature is higher and it takes xx minutes then it means that the pump is not running or that it is idling (no water). A fault e-mail is sent and the station is switched off permanently and automation is disabled.) Czech language strings update. Slovak language new strings update (via automatic Microsoft translator).

June 1 2022 (v3.0)
-----------
(martinpihrt)<br/>
Changes:<br/>
Fixed an error with the set time delay of switching on and off the main station. Fixed a bug in weather based on weather forecasts. Thanks to Petr Procházka for the report bug errors. Logging error detected (fixed in weather-based program). Fixed hiding "run now" button on programs page for "WEEKLY_ADVANCED, CUSTOM, WEEKLY_WEATHER" programs. Added To-Do "Future enlargements" to help page.

May 24 2022 (v3.0)
-----------
(martinpihrt)<br/>
Changes:<br/>
Fixed: there are two directories in the /data directory: default and backup. if the backup directory is older than one hour, a copy of the default directory is made to the backup directory. If the data in the default directory fails, the data from the backup folder is restored. Czech language strings update.

May 17 2022 (v3.0)
-----------
(martinpihrt)<br/>
Changes:<br/>
Added new extension: Internet connection speed monitor (response, download, upload). Czech language strings update.

May 12 2022 (v3.0)
-----------
(martinpihrt)<br/>
Changes:<br/>
Fixed bug in python 3 (iteritems vs items). When using soil moisture sensor which adjusts program run times. 

May 11 2022 (v3.0)
-----------
(martinpihrt)<br/>
Changes:<br/>
Fixed editing weather based program. Add buttons: Find USB devices, Show TTY devices, AUX output, Show partitons, CPU info to system info plugin. Czech language strings update.

May 05 2022 (v3.0)
-----------
(martinpihrt)<br/>
Changes:<br/>
Soil moisture OSPy: the option to display humidity in the footer has been added to the sensor settings (if not all 4 inputs of the AD converter were occupied, the measured unconnected value was displayed. Now can be switched off or on for each probe the display in the footer on the main page). Fixed: graph logging and conversion (from to) measured value in calibrated range (from to).

April 29 2022 (v3.0)
-----------
(martinpihrt)<br/>
Changes:<br/>
Fixed access to OSPy APIs in Python 3 (api crashed if login and password were required. In newer versions of python, the feature has been removed). This update fixes API access (for example, from an OLED M5Stick-C controller or another device). Fixed rounding numbers in Python 3 (to 2 decimal places). Concerned the display of water level settings (for example from the monthly water level plugin). Correction in the monthly water level plugin (if the user accidentally entered a decimal number instead of the whole one at the input, an error occurred during saving).

April 27 2022 (v3.0)
-----------
(martinpihrt)<br/>
Changes:<br/>
A prepared img image was inserted into the "version" location for easy insertion on the SD card.
Download here: https://github.com/martinpihrt/OSPy/releases/tag/image

April 24 2022 (v3.0)
-----------
(martinpihrt)<br/>
Changes:<br/>
plugin tank monitor: Correction of saving to settings and change of min and max level (no longer saved in settings, but only in status).
plugin air temp humidity: Added automatic submit of the form if the user changes the number of DS sensors in the settings (to expand the DS field at the same time). plugin wind monitor: Added interval selection to clear maximum speed. After this set interval, the maximum speed is cleared. Fixed save to settings. Czech language strings update. Slovak language new strings update (via automatic Microsoft translator).
(Rimco)<br/>
Changes:<br/>
Fixed backup storage and improved program loading. Avoid calling update_station_schedule with outdated information. Use shutil.move instead of os.rename.

April 23 2022 (v3.0)
-----------
(martinpihrt)<br/>
Changes:<br/>
Added new extension "venetian blinds" for controll window venetian blinds. Czech language translation for this extension.

April 22 2022 (v3.0)
-----------
(martinpihrt)<br/>
Changes:<br/>
Added help for the first OSPy installation: https://github.com/martinpihrt/OSPy/tree/master/ospy/docs/Clean_installation.md
Fixed display of the name and role of the logged in user.

April 17 2022 (v3.0)
-----------
(martinpihrt)<br/>
Changes:<br/>
Fix in plugins: LCD, air temp, tank monitor, wind monitor. Fix explicitly decode HTTP response for JSON in weather. Fix in base html popup update notifications. Fix in sensors (find sensors, logging to graph).

April 11 2022 (v3.0)
-----------
(martinpihrt)<br/>
Changes:<br/>
Czech language strings update, Slovak language new strings update (via automatic Microsoft translator). Voice notification plugin is now ready to use.

April 10 2022 (v3.0)
-----------
(martinpihrt)<br/>
Changes:<br/>
From this update, OSPy versions will be counted again from 0 (the version will be 3.0.0), other commits are suppressed. Czech language update. All extensions for Python 2 and Python 3 have been tested (except the voice notification plugin -> it will be overwritten in the same way as the voice station plugin). Python 3 will be the default programming language for OSPy. Starting OSPy for Python 3 during installation is not yet resolved (service).

April 06 2022 (v3.0)
-----------
(martinpihrt)<br/>
Changes:<br/>
Transition from python 2 to python 3
1. Make an OSPy backup on the settings page (a zip file will be generated). The file contains a backup of the database and data from the sensors. We can use this backup to restore the system if necessary.
2. We will stop the ospy service "sudo service ospy stop"
3. Open the OSPy folder "cd OSPy"
4. We will uninstall the existing service "sudo python setup.py uninstall"
5. We will install the new service in Python 3 "sudo python3 setup.py install"
6. If there was a data folder and OSPy was ever run earlier in python 2, the database will be converted to python version 3 Attention: after running OSPy in python 3, it is no longer possible to run OSPy in python 2 again! If necessary, we will delete everything in the "data" folder. Then it is possible to run a clean version of OSPy in python 2 or 3 again.
Work on python 2 vs python 3 is not done yet!

April 05 2022 (v3.0)
-----------
(martinpihrt)<br/>
Changes:<br/>
The clean installation runs in both Python 2 and Python 3 (it seems no problem). Not all plugins have been tested in Python 3 (compatibility not yet done). Further work on OSPy and plugins continues. We do not recommend updating existing installations yet. Advanced users can try a clean installation and report any bugs.

March 24 2022 (v3.0)
-----------
(Rimco & martinpihrt)<br/>
Changes:<br/>
This OSPy update and all plugin updates are not in a stable phase (it is in testing and errors may occur). We do not recommend existing users to update their OSPy and plugins yet!!!
Many thanks to Rimco for converting the parts to Python 3.
1. Switched to Python 3. Python 2 should still be working, but no guarantees.<br/>
2. Moved options storage to separate folders to improve the handling regardless of storage backend. This update will take care of moving the existing options file.<br/>
3. Options stored in Python 2 are made forward compatible for Python 3. Make sure to run at least once more using Python 2 if you want to retain existing Python 2 settings.
(The old options.db in /data/ will not be touched after this update, so you can use it to manually recover if needed.)<br/>
Updating Czech language strings. Fix more bug (bruteforce lock time and login logic for users).

October 21 2021
-----------
(martinpihrt)<br/>
Added new plugin "Voice station" You can upload any song with any name in mp3 and wav format to the song directory. Unlike the "voice notification" package, this extension has no connection to the station scheduler (ie how the programs and the stations assigned in them are set up). In this extension, the song will be played whenever the station status changes, regardless of what event the status triggered (for example, manual mode, scheduler, or some other plugin...). The extension of "voice notification" will also be adjusted in the future.Updating Czech language.

October 14 2021
-----------
(martinpihrt)<br/>
ESP32 firmware update version 1.18:<br/>
Added support for new hardware board HW:1.1 (multisensor by pihrt.com). New feture: two buttons for manual control for two relay. 2x LED for relays ON state. 1x LED for 3,3V power supply status. Contolling two relay via web server (from OSPy) instead one relay. Fixed: random clickering in relay (resistor in gate for FET 2N7002). Inductor package size on PCB. If GPIO4 and GPIO15 have pull-up resistors (state on GPIOs is on VCC 3,3V) then automatic detect and switch HW version to "1" HW1.1.<br/>
Added I2C (0x3c) OLED display 0,96" 128x64 (SSD1306) to display measured values from all inputs except humidity (DHTxx) and ultrasound (because these are on the I2C connector and cannot be used at the same time as the display) More: https://github.com/martinpihrt/OSPy/blob/master/ospy/images/esp32_sensor_oled.png. OSPy: a description field for custom event naming has been added to the dry contact and motion sensor. Fixed: writing to the home page and logging to files in the sensors when the sensor is out of operation. Updating Slovak and Czech language.<br/>
New parameters for web:  
Example for on relay 1 to 400 second:  
http://192.168.88.207/0123456789abcdef?re=1&run=400  
For on relay 2 to 10 second:  
http://192.168.88.207/0123456789abcdef?re_2=1&run_r2=10

September 10 2021
-----------
(martinpihrt)<br/>
Changes:<br/>
Updating Slovak and Czech language. Moisture multigraph (completing the display of values from soil moisture probes in a multi graph). Sensor ESP32 - soil moisture (16 probes). Added label to each probe (you can assign your own name to probe 1-16). ESP32 firmware update version 1.17: Fixed bug in sensor "soil moisture". Tested with one ADS1115 converter (4 probes).

September 1 2021
-----------
(martinpihrt)<br/>
Changes:<br/>
Updating Slovak language (Thank you Tomáš Szepesi) and Czech language. In OSPy the option to rotate the sensing logic from the probe has been added to the ESP32 multi-sensor (soil moisture measurement) settings. Example: normal state 0V=0%, 3V=100%. Rotated state 0V=100%, 3V=0% humidity. TODO: moisture multigraph (it remains to complete the display of values from soil moisture sensors in a multi graph (currently only the first probe is displayed in the graph).

August 20 2021
-----------
(martinpihrt)<br/>
Changes:<br/>
Czech language update. 
Sensor ESP32 - soil moisture (16x probes): Added to all types of sensors - sending e-mails in case the sensor does not respond (or now again responds). On the OSPy side, soil moisture processing is complete (data reception, logging, adjustment of the running time of the selected program according to the humidity from the probe). The ESP32 sensor already sends data to the OSPy. It remains to test the connection of the A/D converter to the sensor ESP32 and verify the values of the transmitted voltage (I have not yet tested physically for the test -> hw is ordered). An image with the connection of probes to the ESP32 sensor has been added to the "create a new sensor" section (documentation on how to connect a specific sensor). Whoever already owns the ESP32 multi-sensor and has the ADS1115 converter together with a humidity probe (which has a voltage at the output in the range from 0 to max 5V), can test this functionality. Good luck with OSPy!

August 18 2021
-----------
(martinpihrt)<br/>
Changes:<br/>
Czech language update. 
Sensor ESP32 - soil moisture (16x probes): A window with program names and the time of their modification at runtime % has been added to the home page. If the sensor adjusts the time for the program below 100% of its set time, the window is visible. 100% from the soil moisture probe means that the program will not start. 50% of the soil moisture probe means that the program will only run for 50% of its set time. 10% of the soil moisture probe means that the program will only run for 90% of its set time. 0% of the soil moisture probe means that the program will run at 100% of its set time. Not ready for use!

August 16 2021
-----------
(martinpihrt)<br/>
Changes:<br/>
ESP32 firmware update version 1.16:
Fixed bug in sensor "motion" and "dry-contact" (send state after power on if input has not changed).
OSPy:
Added logging for soil moisture sensor (not completed).

August 13 2021
-----------
(martinpihrt)<br/>
Changes:<br/>
Preparing for soil moisture probes from sensors ESP32 (ESP32 firmware update version 1.15: Added support for 16 pcs soil moisture (4x ADS1115) on I2C bus address: 0x48,0x49,0x4A,0x4B. To connect 16 pcs of humidity probes, it is necessary to connect 4 pcs of the ADS1115 circuit to the IIC bus to the multisensor board (1 pc always for 4 A/D inputs). Each ADS1115 circuit has its own IIC address set). Added support serial line (processing a request from a serial line) for example: AP| for starting AP manager. RBT| for rebooting. Not ready for use! Czech language update.

August 11 2021
-----------
(martinpihrt)<br/>
Changes:<br/>
Preparing for soil moisture probes from sensors ESP32 (recieving data from sensor, create new sensor, show sensor). Each ESP32 multisensor will allow up to 16 soil moisture probes to be connected, which will affect the times of the selected programs according to the soil moisture. Not ready for use! Czech language update.

August 9 2021
-----------
(martinpihrt)<br/>
Changes:<br/>
Updating Slovak language (Thank you Tomáš Szepesi). Added checker to helpers.py "valid_ipv4_address" and "valid_ipv6_address" for future use (IPv6). ESP32 firmware update version 1.14: AP manager - time for invocation: the time for calling up the AP manager with the button was increased to 4 seconds (at a time of 2 seconds, when manually controlling the relay with the button, the AP manager was called up by mistake, even if the user did not want it). Plugin "pool heating": Correction - When the station is running and a probe fault occurs, the station switches off, if the probe is now ok and the switch-on condition is met, the station does not want to switch on. Plugin "air temp humidity": fixing data log downloading (mimetype...)

August 4 2021
-----------
(martinpihrt)<br/>
Changes:<br/>
Czech language update. Rain sensor: Added rain delay (in hours) in to rain sensor options. When the rain sensor is activated, the rain delay is set (this is suitable, for example, for blocking programs for a longer time than provided by the rain sensor).

August 3 2021
-----------
(martinpihrt)<br/>
Changes:<br/>
Czech language update. Sensors: Added option to stop certain stations in case of an event to a contact type sensor (not tested - try it Tomáš Szepesi).

August 2 2021
-----------
(martinpihrt)<br/>
Changes:<br/>
Czech language update. Added new plugin "Door Opening". Fix external IP (if service is not ready).

August 1 2021
-----------
(martinpihrt)<br/>
Changes:<br/>
Czech language update. Added filter to event overview (in OSPy records). Weather station plugin repair. Air temp humi plugin fix (temperature > 127). Correction of time delay of main stations 1 and 2 in case of using activation of main stations by the program (see previous updates).
Update 2:
Fix in event filter (post saving).

July 14 2021
-----------
(martinpihrt)<br/>
Changes:<br/>
Czech language update. Added selector "Activate Master" to program page for select "Master 1" or "Master 2" station. This setting is only available if you are using both main stations. All stations that have "Activate Master 1/2 by program" set will activate master station 1/2 according to this assignment in the program. The program already controls the main station according to the settings (master 1,2 or 1/2 according to the program). Notice! for stations that have "Activate Master 1/2 by program" set, the "run-once" and "manual" option cannot be used. Only the station starts, not the main station (1 or 2)!

July 11 2021
-----------
(martinpihrt)<br/>
Changes:<br/>
Czech language update. Sending values from OSPy sensors has been added to the "E-mail Notifications" extension (if you use sensors, you will see their values after the program is closed in the received e-mail). Two new signals have been added "internet_available and internet_not_available" for use within the system. At the same time, the failure and connection to the Internet (availability of an external IP address) is newly recorded in the event log. New signals have been added to the "signaling examples" extension. In the station section, the structure of the main stations has changed from check boxes to the selection window. A new item "Activate Master 1/2 by program" has been added for future new OSPy options - this function has not been completed yet. Selector: Activate Master? None - No master station will be used (when this station is activated, the master station will not be activated). Activate Master - If you want the master station (eg pump or main water valve) to be activated when a station is activated, select the "Activate Master". Activate Master Two - If you want the second master station (eg second pump or other water source) to be activated when a certain station is activated, select the "Activate Master Two". Activate Master 1/2 by program - If you want to select master station or master station two with a program, select the "Activate Master 1/2 by program". For a program, it is then possible to select which master station is to use for this station (example: program 1 controls stations 1-4 and master station 5. Program 2 controls stations 1-4 and second master station 6).<br/>
Important warning! After this update, you need to reassign the master stations to the stations (station page). If you are using master stations. Updated help in "help" section "Web Interface Guide - Czech.md and Web Interface Guide - English.md".

July 08 2021
-----------
(martinpihrt)<br/>
Changes:<br/>
M5stick-C FW:1.01 (Add checker for enable or disable read NTP time. Add baterry status (percentage and rectangle). Added battery saving (after 10 seconds the brightness of the LCD display decreases). If the any button is pressed, the brightness is restored to maximal brightness).<br/>
OSPy: Updating Slovak language (Thank you Tomáš Szepesi). Correction of data reception from sensors in API. If the data from the probe is not valid, the value -127 is always set. Corrections in data processing from sensors.

Jun 30 2021
-----------
(martinpihrt)<br/>
Changes:<br/>
A list of sensors has been added to the lcd display extension for showing. Several bugs in the lcd have been fixed. Czech language update. Fix in sensors web page (if change sensor types).

Jun 28 2021
-----------
(martinpihrt)<br/>
Changes:<br/>
A logging page has been added to some extensions. Czech language update. A window with comments has been added to the sensors page - if it is filled in for the sensor, it will be displayed (otherwise it is not visible).

Jun 23 2021
-----------
(martinpihrt)<br/>
Changes:<br/>
ESP32 firmware update version 1.13: fixed: value refresh for calibration of temperature sensors. Removal of the hw timer for LED flashing and replacement by flashing in the loop. OSPy: added to logging event: system OSPy "Stopping" and "Starting".

Jun 22 2021
-----------
(martinpihrt)<br/>
Changes:<br/>
Updating Slovak language (Thank you Tomáš Szepesi). Fix in plugin "pool heating" (the station switches off if the sensor has a fault). Add logging events from OSPy core (so far only rain sensor). ESP32 firmware update version 1.12: possibility of tuning (calibration of temperature sensors +- C) DS1-DS4 in menu AP manager.

Jun 14 2021
-----------
(martinpihrt)<br/>
Changes:<br/>
Update jquery.min.js from 3.5.1 to 3.6.0. (https://blog.jquery.com/2021/03/02/jquery-3-6-0-released/). Update gauge.min.js from 2.1.4 to 2.1.7 (https://canvas-gauges.com/download/).

Jun 13 2021
-----------
(martinpihrt)<br/>
Changes:<br/>
Added checkbox "Show also errors" (Show also errors in graph. Example: -127) to sensors graph. Added ultrasonic sensor to plugin "weather stations". Updating Czech language (new strings).

Jun 10 2021
-----------
(martinpihrt)<br/>
Changes:<br/>
Sensor ESP32 firmware update version to 1.11: Fix in ultrasonic probe. 

Jun 07 2021
-----------
(martinpihrt)<br/>
Changes:<br/>
Fix in plugin "tank monitor". Added new remote controller based on M5stick-C. This controller allows you to select a program stored in the OSPy on the LCD display and start it with the button. The controller is connected to the home Wi-Fi network. We do not even need a mobile phone or a computer to quickly select programs. We will use this miniature controller. Visit my youtube channel "OSPy - Open Sprinkler Controller Python" for more informations: https://youtube.com/playlist?list=PLZt973B9se__UN_CVyOoy1_lr-ZSlSv0L.

May 28 2021
-----------
(martinpihrt)<br/>
Changes:<br/>
Updating Czech language (new strings and repair strings). Fixed in plugins: "tank monitor" and "pool heating".

May 23 2021
-----------
(martinpihrt)<br/>
Changes:<br/>
Updating Czech language (new strings and repair strings). Added: in to plugin "tank monitor" - log page. Changes: in plugin "CLI control" and "signal examples" new signals.

May 21 2021
-----------
(martinpihrt)<br/>
Changes:<br/>
Updating Czech language (new strings). Logging and support for a more accurate DHT22 sensor have been added to the "air temp" extension (i must fix the error: in the graph and log display if the log data already exists. If you delete the log, everything will work). Logging, test buttons and basic help for wget commands have been added to the "CLI" extension.

May 18 2021
-----------
(martinpihrt)<br/>
Changes:<br/>
Updating Czech language and translating to Slovak (Thank you Tomáš Szepesi). Fixed markdown in help files (now is used markdown2 from: https://github.com/trentm/python-markdown2). Suport form markdown in Python 2 is ended. If you not view correctly help file and readme file you must using SSH and type: "cd OSPy" and "sudo python setup.py install" for installing markdown2.<br/>
Added new function in to the "tank monitor" extension  "rain delay" in case there is not enough water in the tank. Stations are blocked for a set time. <br/>
Added new button to sensor firmware for starting AP manager (if you are not physically present at the sensor - without disassembling and pressing the AP button on the sensor). Available from ESP32 firmware version 1.10. Added upload form to "sensor fimware page" for uploading own custom update file. Working on sensors in core OSPy (still not done flow meter). Ultrasonic in multisensor is ready for using. Fixed in show firmware version in sensor (if the fw version was, for example, 1.10, then 1.1 was shown).<br/> ESP32 firmware update version 1.10: Added function to webserver for starting AP manager from OSPy.

May 10 2021
-----------
(martinpihrt)<br/>
Changes:<br/>
ESP32 firmware update version 1.09: Added fake test for DS1-DS4 DS18B20 sensors (China clone sensors). Repair known bugs.<br/>
OSPy: Updating button control plugin. Fix bug in webpages (sensor log table - if not record yet). Cosmetics fix hmtl css in sensor search page and readme.md file. Working on ultrasonic sensors.

May 04 2021
-----------
(martinpihrt)<br/>
Changes:<br/>
ESP32 firmware update version 1.08: Added flash state to LED when the sensor is connecting to a Wi-Fi network. Added if the sensor is disconnected from Wi-Fi, the sensor will restart immediately. Added new parameter running time for relay outputs (ex: http://192.168.88.207/0123456789abcdef?re=1&run=120 re=1 is relay on and run=xxx is time in seconds 0123456789abcdff is secure code from sensor. If the run parameter is not specified, it will be ignored). This is a good solution for possible shutdown of the relay in case of connection failure (example: OSPy switches the relay on the sensor board to ON for 4 minutes and then after time turns it OFF. If OSPy not send command for OFF, the sensor switches itself to OFF after 5 minutes) Fixed DS18B20 probe to 12 bit resolution (+- 0.0625C). Warning: after this update it will probably be necessary to settings your sensor via the AP manager.<br/>
OSPy: Added forms for future use of the ultrasonic sensors. Fixed bug in sensors. Fixed html css styles in sensors. Leak detector and ultrasonic sensor is not ready for use (i working on it). Updating Czech language (new strings for sensors).

Apr 23 2021
-----------
(martinpihrt)<br/>
Changes:<br/>
ESP32 firmware update version 1.07: Fix time for AP manager to 10 minutes. Fix message in serial print. Add calibration for voltage divider in to AP settings. Divider correction (+-) = if we need to fine-tune the exact value of the voltage measurement 0-30V, then we can use the + - value for this adjustment. Example: the displayed voltage value is 10.7V and the actual value should be 12.7V (measured by a voltmeter on the main power input). Enter the value 20 in the field. The entered value is multiplied by the number 0.1 during the calculation. Add LED ON if relay is ON. Add ultrasonic support for distance level (not tested yet). Tested probe DHT22 and DHT11 for moisture measuring. Add documentation for sensors to "help" file folder. <br/>
OSPy: Add case 3D models for ESP32 multisensor. Work started on ultrasound support in OSPy for multisensor - not ready for use.

Apr 03 2021
-----------
(martinpihrt)<br/>
Changes:<br/>
Updating Czech language (new strings and repair strings). Adding help button to the remaining  plugins. Add Sensors to Weather Stations plug-in.

Apr 01 2021
-----------
(martinpihrt)<br/>
Changes:<br/>
Updating Czech language (new strings and repair strings). Adding help button to more plugins.

Mar 28 2021
-----------
(martinpihrt)<br/>
Changes:<br/>
Updating Czech language (new strings for telegram bot extension).

Mar 26 2021
-----------
(martinpihrt)<br/>
Changes:<br/>
Updating Czech language (new strings). Updating LCD display plugin (help page and new msg for print to LCD), Signaling Examples plugin (help page), System Update plugin (help page).

Mar 24 2021
-----------
(martinpihrt)<br/>
Changes:<br/>
Error Repair images in stations images. If not installed Python Pillow for image proccessing. Now is available button for installing it. New: GIF image can be uploaded to the stations images. Fix Czech language. 

Mar 23 2021
-----------
(martinpihrt)<br/>
Changes:<br/>
Updating and fix in "pool heating" plugin. Updating Czech language (new strings). Add new plugin "telegram bot" - !!!Not ready for use!!! Working on it.

Mar 20 2021
-----------
(martinpihrt)<br/>
Changes:<br/>
Updating images connection diagram in docs and help page. ESP32 firmware update version 1.06 (Add time limit for sending data (if it was not sent to the OSPy within 2 minutes, then restart the sensor). Sensor freeze prevention.)

Mar 15 2021
-----------
(martinpihrt)<br/>
Changes:<br/>
Updating Slovak language (Thank you Tomáš Szepesi). Add to plugin "pool heating" possibility to read temperatures from OSPy sensors.

Mar 12 2021
-----------
(martinpihrt)<br/>
Changes:<br/>
ESP32 firmware update version 1.05 (Add selector for moisture probe type - user changeable (in AP mode). Add password for access to upload new firmware via http in STA (normal) mode - user changeable. For uploading in STA mode use html post "/FW_YOURUPLOADPASSWORD". Add password for Wi-Fi access - user changeable (in AP mode). Add moisture sensors DHT22 (AM2302, AM2321), DHT 21 (AM2301), DHT11 - used SDA pin GPIO33 (not used I2C bus). Add moisture sensor SHT21 (HTU21D) used I2C bus.<br/>
Add 3D print file case for OSPy ESP32 multisensor (not tested yet). It is now possible to upload a new firmware version directly from the OSPy to the ESP32 sensor (possible from version FW1.05). A new item "password for uploading" for uploading firmware via http" has been added to the "sensors" section of the OSPy settings. Translation of new strings into Czech. Warning! After This OSPy update you must update OSPy sensor ESP32 to last fw:1.05!

Mar 08 2021
-----------
(martinpihrt)<br/>
Changes:<br/>
ESP32 firmware update version 1.04 (Add leak detector to input via interrupt routine. If leak pulses > 0 sending data in cycle 3 seconds. Add I2C scanner routine for find I2C addreses - for moisture and more). Updated Web Interface Guide.md - Czech/English. Add to sensors "datetime" for last input info. Translation of new strings into Czech.

Mar 07 2021
-----------
(martinpihrt)<br/>
Changes:<br/>
The item "display data from sensors on the home page) has been added to the OSPy settings and to the sensors themselves. Fixed several errors. Translation of new strings into Czech. Added HW1.00 ESP32 sensor to: https://github.com/martinpihrt/OSPy/tree/master/hardware_pcb/sensors_pcb_fw/ESP32.

Mar 03 2021
-----------
(martinpihrt)<br/>
Changes:<br/>
Error correction in sensors. if the user has already added a sensor (for example a multi sensor) and then added another input from the same sensor, then a problem has occurred if the sensor type has been selected incorrectly. Updating Slovak language (Thank you Tomáš Szepesi). More information about sensors here: https://pihrt.com/elektronika/439-ospy-jak-pridat-a-pripojit-snimace.

Jan 18 2021
-----------
(martinpihrt)<br/>
Changes:<br/>
Add directory for sensors with ESP8266 chip, add download button fw to sensor search page. Updating Czech and Slovak languages.

Jan 17 2021
-----------
(martinpihrt)<br/>
Changes:<br/>
Fix bugs in sensors pages (if programs is none). Add sensor last available ESP32 FW version info to sensors search page.

Jan 15 2021
-----------
(martinpihrt)<br/>
Changes:<br/>
Added new version of FW 1.03 for Wi-Fi/LAN sensors. Added help on how to set up sensors in to OSPy "help" tab. More on the sensor new firmware on web: https://pihrt.com/elektronika/439-ospy-jak-pridat-a-pripojit-snimace.

Jan 11 2021
-----------
(martinpihrt)<br/>
Changes:<br/>
Fix in setup.py (TypeError: coercing to Unicode: need string or buffer...) Thank you user Zoek Mach for reporting.

Jan 8 2021
-----------
(martinpihrt)<br/>
Changes:<br/>
Updating Czech language and translating to Slovak (Thank you Tomáš Szepesi). If a sensor is added in the sensor section, a graph and a table with records can be displayed for it (if logging was enabled in the sensor settings). Dry contact sensor and motion sensor (or multi dry contact/motion) is fully completed and tested (with sending E-mails and start running program). The temperature sensor (or multi temperature sensor - 4x DS18B20) also writes to the graph and to the log (sends an e-mail and runs the program not completely tested). Missing to finish flow and humidity measurement to sensors and implement to OSPy sensors. I'm still working on it. 

Jan 3 2021
-----------
(martinpihrt)<br/>
Changes:<br/>
Czech language update. ESP32 firmware update version 1.02 (bug fixes, sensors DS18B20 connection detection). Emailing, event logging and sample logging have been added (for the "Dry Contact, Motion, Multi Dry Contact, Multi Motion") to sensor website. Added sensor data logging page (possibility to download as csv format). Fixed sensor selection (when a multi sensor was not selected, fields that they did not have were displayed). Missing finish: logging events and samples and sending email for temperature, humidity and flow meter. for all program start sensors. There is still a lot of work on this part of the "sensors".

Dec 29 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Updating language translating to Czech. Updating language translating to Slovak (Thank you Tomáš Szepesi). Adding blue and green color, Wind monitor, text or canvas mode to new canvas plugin "Weather Stations". Prepare in sensors.py for running programs.

Dec 27 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Updating language translating to Czech. Adding new canvas plugin "Weather Stations". Displays data probes DS18B20 (DS1-6) from Air Temperature and Humidity Monitor plugin and volume, percent from Water Tank Monitor plugin.

Dec 26 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Updating language translating to Czech. More changes for sensors input to OSPy. For this testing use FW:1.02 and ESP32 board in folder: hardware_pcb/sensors_pcb_fw/. More infos with images is here: https://pihrt.com/elektronika/439-ospy-jak-pridat-a-pripojit-snimace. Sensor ESP32 FW: 1.02: Add AP manager for settings sensor from phone, tablet (4 minutes timeout). For run AP manager: push button least > 2 seconds. Password for AP Wi-Fi is "ospy-sensor-esp32", next open browser and type IP "192.168.1.1". Add saving to eeprom memory. Fast blinking LED if AP manager. Slow blinking LED if normal run. Add control relay from stations (plugin CLI Control in plugin manager): ex command: http://IP/securecode?re=1 (or re=0). In AP manager is active button  for control relay ON or OFF. Available only on the same network as OSPy. Now exists parameter "multi sensor" in sensors (for measure temperature 4xDS18B20 and Dry Contact, Leak Detector, Moisture, Motion) just one ESP32 board and all parameters can be sent and responded to in OSPy. 

Dec 23 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Updating language translating to Czech. More changes for sensors input to OSPy. For first testing use FW:1.01 and ESP32 board in folder: hardware_pcb/sensors_pcb_fw/. It is now possible to add sensors and display their values (the web manager in the sensor has not been resolved yet, the values must be entered in the code). Tested: Dry Contact (between pin and ground), Motion (between pin and ground), Temperature (DS18B20 with pull-up resistor 4k7 for data pin on 3,3 VDD source). Todo not tested: Leak Detector, Moisture. Not yet done logging and running programs on events in OSPy core for sensors. More infos with images is here: https://pihrt.com/elektronika/439-ospy-jak-pridat-a-pripojit-snimace

Dec 14 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Adding and changes in /api for incomming data from sensors (Wi-Fi or LAN). Updating language translating to Czech. Added category for user "sensor" for data input from sensors. Added a new page to search for sensors that are not assigned. Only for testing - not ready to use.

Dec 9 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Adding and changes in /api for incomming data from sensors (Wi-Fi or LAN). Only for testing - not ready to use. Updating language translating to Slovak (Thank you Tomáš Szepesi).

Dec 6 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
When adding a new sensor, the error in checking the MAC and IP address in the case of a radio sensor was fixed. The method of backing up the system OSPy has changed. Not only is the database file (options.db) saved, but the stations folder is also saved, where the station images are stored. At the same time, the events.log log file (if it exists) is saved. Everything is saved in a zip file (Example: ospy_backup_systemname_4.12.2020_18-40-20.zip). We can easily identify from which OSPy system the backup comes. The SSL folder where is the certificate is not stored for security reasons in to backup zip file! Restoring OSPy from zip file: The uploaded file must be zip file! The following paths and files must be in the:  
```bash
*.zip folder:
* ospy/data/events.log  
* ospy/data/options.db  
* ospy/data/options.db.bak  
* ospy/images/stations/station1.png  
* ospy/images/stations/station1_thumbnail.png 
``` 
Or other pictures of stations in the same format. Updating Czech language translate for changes. Newly, if we click on delete OSPy in the settings tab to the default settings, the files will be deleted: .pem in the /ssl folder. Next, events.log, options.db, and options.db.bak in the data folder. And all images in the folder images/stations. Added Documetation from sensors (pages: Web Interface Guide - Czech.md and Web Interface Guide - English.md).

Nov 30 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Updating language translating to Slovak (Thank you Tomáš Szepesi). Add to helpers.py for future use: valid ip, encrypt name, decrypt name.

Nov 28 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
New sensors selector: Dry Contact, Leak Detector, Moisture, Motion, Temperature. And communications selector: Wi-Fi/LAN or Radio. Sensors can already be added to the sensors tab. Sensors are displayed after addition and can be edited. Nothing else is done yet (communication with sensors and their response in the system). Added translation of new strings into Czech language. Fixed run time on the home page.

Nov 23 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Fixed in login (if "access without password" was checked in the settings, then access to panels was not displayed in OSPy.)

Nov 21 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Fixed in users (user name and password lenght check, if the user name already exists, that the new user does not have the same name as the administrator). Added and updating Czech language translate for new strings.<br/>
Fixed loading header (cpu temperature, load ...) -> redirection to update_footer.<br/>
Added new tab "sensors". Added support for sensors. In the future it will be possible to add sensors (pressure, temperature, humidity, contact ...) and their assignment to various operations (for example, the temperature sensor closes a certain program).

Nov 19 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Fixed setup.py (user name and password check, print function). Updating Czech language translate for new strings (from setup.py).

Nov 18 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Fixed uptime (if uptime is bigger of 30 days). Update in Web Interface Guide - Czech/English. Automatic refresh for temperature cpu, usage cpu, IP and uptime after 5 seconds.

Nov 16 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Updating Czech and Slovak language translate for new strings. Added support for displaying images at stations and on the home page. If in the "options tab" is checked display of an image for stations, then the option to work with images will appear in the station tab and on the home page.<br/>
Demo is here in folder:<br/>
https://github.com/martinpihrt/OSPy/blob/master/ospy/images/

Nov 14 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Updating Czech and Slovak language translate for new strings. Fixed login page (the username and password are checked at the same time - if there were more users with the same name, unauthorized access could occur). Added support for images (in the images folder) for future use.<br/>
HOME page<br/>
public access: https://github.com/martinpihrt/OSPy/blob/master/ospy/images/home_public.png
<br/>user access: https://github.com/martinpihrt/OSPy/blob/master/ospy/images/home_user.png
<br/>admin access: https://github.com/martinpihrt/OSPy/blob/master/ospy/images/home_admin.png
<br/>PROGRAMS page<br/>
<br/>user access: https://github.com/martinpihrt/OSPy/blob/master/ospy/images/programs_user.png
<br/>admin access: https://github.com/martinpihrt/OSPy/blob/master/ospy/images/programs_admin.png
<br/>LOG page<br/>
<br/>user access: https://github.com/martinpihrt/OSPy/blob/master/ospy/images/log_user.png
<br/>admin access: https://github.com/martinpihrt/OSPy/blob/master/ospy/images/log_admin.png

Nov 13 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Updating language translating to Slovak (Thank you Tomáš Szepesi). Updating web.py to version 0.51 (Thank you Dan-in-CA). Czech language translate for new strings. Added multiple users control (public, user, administrator) for logging to OSPy. Fixed run-now in programs (enable run now for programType.WEEKLY_ADVANCED, CUSTOM, WEEKLY_WEATHER).

Nov 10 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Added new command to plugin "E-mail reader" for get data from plugins (wind monitor, temp monitor, tank monitor). Czech language translate for new strings.

Nov 6 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Correction in options.html (autocomplete = "new-password"). Fixed Users in users.py (now it is possible to add new and delete old users who have access to the OSPy system). Assignment of rights to users is still unresolved (all users are administrators). Added new strings to Czech translation. Updating language translating to Slovak (Thank you Tomáš Szepesi).

Nov 5 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Added selectors to plugin "E-mail reader" for control more programs and reboot (shuttdown). Czech language translate for new strings. Fixing unicode in scheduler.py, runonce.py, webpages.py

Nov 4 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Updating language translating to Slovak (Thank you Tomáš Szepesi).

Nov 3 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Added subject to plugin "E-mail reader" for control more OSPy systems. Czech language translate for new strings.

Oct 31 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Added new plugin "E-mail reader" for controling OSPy via E-mails. Warning: Control via dict {} not completed! Others is posible (command, list).

Oct 29 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
WARNING! Default name is now "admin"!<br/>
Added prepare support for multiple users (public, user, administrator) for logging to OSPy. NOT READY TO USE! Fixed a bug in the "plugins update" if not enabled not check updates (fix for pop-up notification on home page if plugin has update). New field for logging to ospy "user name". Default name is "admin". Name change is posible in OSPy options/user. Fixed device up time on home page.

Oct 24 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Added support for multiple languages in the helpers.py file. Better display of uptime in home page. Added warning to page "help.html" Error: Failed loading Python extension partial gfm in markdown! README.md information in help not be displayed correctly. Added support for multiple languages and fixed "when no I2C circuit is found" bug in lcd_display extension. Fixed a bug in the "system info" extension when the I2C bus was not found.

Oct 23 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Added language translating to Slovak (Thank you Tomáš Szepesi).

Oct 21 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
The option to turn off the selected stations in the scheduler has been added to the extension of pressure monitor, tank monitor. Added language strings and translating to czech.<br/>
Fixed ImportError: Failed loading extension "partial_gfm" in web page plugins install.

Oct 19 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
The option to turn off the selected stations in the scheduler has been added to the extension of wind speed measurement. Added language strings and translating to czech. in web page "stations" is removed new button "ignore plugins". Added speed dial buttons in a pop-up window.

Oct 17 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Added new language strings, in web page "stations" is added new button "ignore plugins" for later use (as the ignore rain button now has). The option to turn on and off the display on the home page in the footer section has been added to the "system update" plugin. Preparation for notifications was performed (pop-up window with information about the availability of updates for plugins and OSPy of the system). Fix css style for checker.

Oct 15 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Updating and add new language strings, fix loading and changind data from plugins on the home page.

Oct 11 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Update to jQuery 3.5.1 min, added file "notice.html" for viewing messaging in OSPy (restarting, updating, deleteting, uploading...)

Oct 1 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Added option for regulation "Minimum maintained water level" and selection of interval for reading data into the graph (plugin tank monitor). Added language string (CZ and SK).

Sept 27 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Added "Regulate the maximum water level" into tank monitor plugin. Added czech strings into language.

Sept 23 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Added "generate" buton in "options SSL certificate" for own SSL certificate generating. OSPy Language fix in cz string. Fix 24 hour reseting max speed in wind speed monitor.

Sept 9 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Changes in wind monitor plugin. OSPy Language fix in cz string.

Sept 7 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Added option to stop the scheduler in the water tank plugin if the correct value is not returned from the sensor (must > 0). OSPy Language fix in cz string.

Sept 4 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
A new pool heating extension has been added to the plugins.

Sept 2 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
A new temperature switch extension has been added to the plugins.

Aug 27 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Fixed webpages stations.html (translating strings and css style for checkbox).

Aug 19 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Fixed buttons "water level" and "rain delay" on the home page after update from 18.8.2020 (Thank you for the report by V. Hrabe). Added new plugin MQTT run-once (run-now schedulling via MQTT protocol). Plugin is not ready for using!

Aug 18 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Fixed redirection when displaying data from plugins on the home page. Automatic loading of data from plugins (on the home page). Fix translation (in czech language). Add print function in to helpers.py

Aug 15 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Added strings for translation, translation into Czech and into other language translations (machine translations).
Add plugin data to display (any plugin now allows you to display data on the home screen and time line). Not 100% ready to use. Working on it. Fixing in restart and power down in menu (new notifications windows). 

Aug 12 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Added strings for translation into all graphs, translation into Czech and into other language translations (machine translations).
Add plugin data display (any plugin now allows you to display data on the home screen). Better loading of data from plugins. Completion of translations. Netatmo delay fix.

Aug 4 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Added "delete all" button to the plugin manager (you can delete all installed plugins at once). Added missing untranslated strings.
Added strings for translating the name of plugins in the list of plugins. Languages other than Czech are not checked!
WARNING: BEFORE THIS UPDATE, FIRST UPDATE ALL PLUGINS, FOLLOW OSPY AND THEN RESTART THE SYSTEM!

Aug 3 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Machine translation without checking strings into languages: Slovak, German, French, Greek, Italian, Portuguese, Slovenian, Spanish, Tamil, Arabic, Afrikaans.<br />
If you find an error in the translation, report it to: admin@pihrt.com

Aug 3 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
All plugins use the local i18n translation file in all plugins. All language mutations are now merged into one file within the i18n OSPy system. Update all plugins first, then the system OSPs, and then restart the operating system (linux). Slovak will have to be translated (does anyone want to help for other languages?)

July 30 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Fonts are no longer loaded from fonts.googleapis.com/css?family=Open+Sans:400,300,600,700, but directly from the /static/fonts folder of the local web server. If the Internet connection fails, the fonts from google would not be loaded.

July 28 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Fixing: common warnings (SameSite=None requires SecureThe SameSite attribute of the Set-Cookie HTTP response header allows you to declare if your cookie should be restricted to a first-party or same-site context. None requires the Secure attribute in latest browser versions. See below for more information. https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie/SameSite).<br />
https://web.dev/samesite-cookies-explained/ Change to: SameSite=Lax.

July 27 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Fixing: common warnings (SameSite=None requires SecureThe SameSite attribute of the Set-Cookie HTTP response header allows you to declare if your cookie should be restricted to a first-party or same-site context. None requires the Secure attribute in latest browser versions. See below for more information. https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie/SameSite).<br />
Fixing: Markdown only accepts unicode input in plug-in manager (for README.md files).

July 10 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Add to plugin "water tank" switch for displaing liters or m3. Fix displaing liters or m3 in LCD, e-mail and home page. New plugin: MQTT secondary remote control for more OSPy systems via MQTT protocol.

May 18 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Fix: display data from plugins on home page. Add Python 3 compatible in i18n and helpers (for future Python 3).

May 4 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Fix: do not display data from plugins if manual mode.

Apr 30 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Added to home page: PRESSURE MONITOR plugin, UPS plugin, added buttons for opening plugins. Added in PRESSURE MONITOR plugin and UPS plugin data json status.</br> 
Fix: if the plugin is not enabled in the plugin settings, the data will not be displayed on the home page.

Apr 12 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Added to ospy folder: 3d box for ospy, circuit master board and slave board (hardware 3.3 version). Fixed plugin "measurement of water in tank". Added hardware and software to plugins (scheme, circuit boards and possibly 3D add-ons).

Feb 21 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Caution: sha1 has been changed to sha256 for safety reasons. If you are updating the OSPy version, you must delete the options.db file in the folder "OSPy/data/". You will then need to set up the entire system again. It is up to the user to make this security update. Sha1 is out of date and is not secure. The current password is in sha1 and after updating to sha256 you will not be able to log in to OSPy.</br>
Added option to upload own certificate into settings (certificate files will be saved to "ssl/" folder).

Feb 5 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Preparation for Python 3.
Stage 1 does not add any imports from the future package. The output of stage 1 will probably not (yet) run on Python 3.</br>
The goal for this stage is to create most of the diff for the entire porting process, but without introducing any bugs.</br>
It should be uncontroversial and safe to apply to every Python 2 package.</br>
The subsequent patches introducing Python 3 compatibility should then be shorter and easier to review.

Jan 22 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Upgrade the OSPy to version to 4.0.0. Preparation for python 3. Add select in air temp plugin (in graph). Add graph for water tank plugin.</br>
Add select in graph on home page.

Jan 10 2020
-----------
(martinpihrt)<br/>
Changes:<br/>
Fix in ospy service (Thank's Dan Kimberling).</br>

Dec 31 2019
-----------
(martinpihrt)<br/>
Changes:<br/>
Fix in water tank plugin and wind plugin. Update language. Fix weather status msg on home page. Prepare for python 3.</br>

Nov 6 2019
-----------
(martinpihrt)<br/>
Changes:<br/>
Add to options domain name for SSL (certificate via Lets Encrypt certification authority) and for own certificate. Fix in options. Update language. Add weather status msg to home page.</br>

Sep 9 2019
-----------
(martinpihrt)<br/>
Changes:<br/>
Add data from plugins "Air Temperature and Humidity Monitor, Water Tank Monitor, Wind Speed Monitor" to home page under graph. For use you must update plugins and enable this function in options "Show plugins on home". For demo see: https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Web%20Interface%20Guide%20-%20Czech/plugins%20home.png. Add get data_json to "Air Temperature and Humidity Monitor, Water Tank Monitor, Wind Speed Monitor" for others use.</br>

Sep 3 2019
-----------
(martinpihrt)<br/>
Changes:<br/>
New plugin: "Pressurizer" is ready to use. The pressurizer plugin used to switch on the main relay (pump) before starting the set program (switching on the station). Some valves require pressure in pipe to reliably open/close. Update: "signaling examples plugin" - for pressurizer plugin. Update the OSPy and affected extensions to the latest version.<br/>

Sep 2 2019
-----------
(martinpihrt)<br/>
Changes:<br/>
Add new plugins: "MQTT slave" and "Pressurizer". Not finish version (working on it).<br/>

Aug 16 2019
-----------
(martinpihrt)<br/>
Changes:<br/>
Fix in plugins: "LCD" Add button for re-find I2C bus, "System info" Fix UTF8 code. Add english and czech Web Interface Guide to help page.<br/>
Fix readme.md, Add images for czech Web Interface Guide, Fix help string in options page, Fix string czech translation in options page.<br/>

Aug 4 2019
-----------
(martinpihrt)<br/>
Changes:<br/>
Fix in plugins "water tank, email, LCD". Add anonymous usage statistics collector for statistics (python version, general information about the operating system - architecture, distribution, system). Fix program name in scheduler.<br/>

July 28 2019
-----------
(martinpihrt)<br/>
Changes:<br/>
Fixing in server.py for last web.py (0.40) version. The SSL certificate is now created automatically after checking the "https" option in OSPy settings. If you already have your server.crt and server.key files nothing changes.<br/>

July 19 2019
-----------
(martinpihrt)<br/>
Changes:<br/>
Fixing in helpers.py markdown (conversion UTF-8 string) for help page. Preparing files for Web Interface Guide.<br/>

June 27 2019
-----------
(martinpihrt)<br/>
Changes:<br/>
Add new signal for system signalling (master station one and master station two in stations, rain detect in scheduller).<br/>
Fixed CPU usage in plugin water consumption counter. Add new signals in plugin signaling examples.

June 21 2019
-----------
(martinpihrt)<br/>
Changes:<br/>
Add new plugin water consumption counter. Fix in scheduller if rain (or rain delay) and stations has not ignore rain -> not logging.<br/>

May 21 2019
-----------
(martinpihrt)<br/>
Changes:<br/>
Fixed CPU usage in plugins, Fixed MQTT PIP isue, Ignore in mp3 user file modification. Add CPU usage to home page.<br/>

May 4 2019
-----------
(martinpihrt)<br/>
Changes:<br/>
Fixed I2C range in LCD plugin. Fixed range in programs.py. Thank's user ITDPG4<br/>

Apr 15 2019
-----------
(martinpihrt)<br/>
Changes:<br/>
Weather Underground has been replaced with Dark Sky API. Thank's user Rimco<br/>

Sep 6 2018
-----------
(martinpihrt)<br/>
Changes:<br/>
Fix for download in options if file is not ready for download.(options.db).<br>
Add msg for upload options.db if file name is not options.db.<br>
Add new plugin: CLI Control. Add status in pressure monitor plugin.<br>
Add signaling examples plugin.<br>
LCD plugin change: insert stations running info in to loop.<br>
Fix home page in manual mode for msg graph.

Aug 18 2018
----------
(martinpihrt)<br/>
Changes:<br/>
Add new dark theme in templates. Add info on homepage if wunderground graph data is not correct.

Aug 9 2018
----------
(martinpihrt)<br/>
Changes:<br/>
Prepare i2c function in helper.py - add pigpio (for future and better use in plugins), change getip() function, add cz and sk string. Plugins: Voice (add more voices), Email (add temperature)

July 22 2018
----------
(martinpihrt)<br/>
Changes:<br/>
Add email logging to all plugins (where is email used). Add subject into email to all plugins (where is email used). Add email to system update plugin. Fix blinker signal (restart) in webpages.

July 20 2018
----------
(martinpihrt)<br/>
Changes:<br/>
Add notes in station.html, Add email logging in log.html and options.html, Add function for email logging, Add blinker, Fix unicode error in options.html.

July 11 2018
----------
(martinpihrt)<br/>
Changes:<br/>
Add in webpages.py and plugins_manage.html Adding new button for enabling all plugins in manage.

July 5 2018
----------
(martinpihrt)<br/>
Changes:<br/>
Fix in weather.py Reduce startup delay to be faster than plugins. Make the weather module more robust in determining the location. Thank's Rimco.

June 29 2018
----------
(martinpihrt)<br/>
Changes:<br/>
Fix in options.py Some even more temporary file might block saving. Thank's Rimco.

June 27 2018
----------
(martinpihrt)<br/>
Changes:<br/>
Fix in options.py Ensure clean options file is created such that we don't get stuck in case it was corrupted. Thank's Rimco.                                                                                                      

June 25 2018
----------
(martinpihrt)<br/>
Changes:<br/>
Add slovak translate for all plugins and OSPy.
Fix in __init.py__ (plugins) loading modules after 1 sec.
Add traceback in scheduler.py Thank's Rimco. 

June 4 2018
----------
(martinpihrt)<br/>
Changes:<br/>
programs.py, stations.py, webpages.py, stations.html, i18n: Better controls for weather based programs. Thank's Rimco. 

May 31 2018
----------
(martinpihrt)<br/>
Changes:<br/>
programs.py, weather.py: Be more robust against temporary Wunderground hiccups, recalculate yesterday instead of using cached value. Thank's Rimco. Fix logging, check on directory wunderground. 

May 28 2018
----------
(martinpihrt)<br/>
Changes:<br/>
programs.py: Fix in PEM: https://github.com/martinpihrt/OSPy/issues/2. Thank's Ithill.
api.py: Extend and fix system API. Thank's Rimco.
OSPy-plugins/plugins/lcd_display/: Adding more type for hardware LCD I2C boards.

May 16 2018
----------
(martinpihrt)<br/>
Changes:<br/>
programs.py: The PEM might be removed before it has been executed. This change allows up to 3 hours of delay (instead of 1) before a PEM is considered old and will not be reported by the program to the scheduler anymore.
options.py: Add option Use Wunderground. Add option to set IP addres to bind to for HTTP server.
server.py: Add IP addres to bind to for HTTP server.
version.py: date version 16.5.2018.

Apr 11 2018
----------
(martinpihrt)<br/>
Changes:<br/>
OSPy-plugins/plugins/air_temp_humi/ and /plugins/lcd_display/ 
Add print from 6 sensors to LCD plugin. Fixed errors. Translations to Czech.

Apr 6 2018
----------
(martinpihrt)<br/>
Changes:<br/>
OSPy-plugins/plugins/air_temp_humi/ new HW2 board plugin DS18B20 
Add labels for DS1-6 sensors. Fixed errors. Change structure for log file.

Mar 25 2018
----------
(martinpihrt)<br/>
Changes:<br/>
OSPy/ospy/programs.py
Fixed the missing space in the text "Weather Schedule" and the following string of days.
Thanks https://github.com/lthill

Dec 28 2017
----------
(martinpihrt)<br/>
Changes:<br/>
Air Temperature and Humidity Monitor - plugin. Repair negative temperature measurement with DS18B20 probe.
Beware of this update, it is necessary to change the version of the program in ATMEGA 328 from 1.0 version to 1.1 (if we use temperature measurement using DS18B20)!

Aug 22 2017
----------
(martinpihrt)<br/>
Changes:<br/>
Added reverse proxied.py for nginx.<br>
Fixed language in helpers.py.<br>
Fixed saving and loading files in options.py.<br>
Added new repository for plugins (OSPy-plugins). Removing core and temporary plugins.<br>
Change address for plugins repository in server.py.<br>
Updated date in version.py.<br>
Added MQTT zone brodcaster and fixed error in MQTT plugin.<br>

Aug 1 2017
----------
(martinpihrt)<br/>
Changes:<br/>
Fixed options database corruption protection.<br>
Fixed webpages upload backup options.db back to server.<br>

July 31 2017
----------
(martinpihrt)<br/>
Changes:<br/>
81e8636 options database corruption protection not function 100% not used.<br>
Fixed LCD plug-in and email plug-in.<br>
Add Czech string for weather.<br>

July 24 2017
----------
(martinpihrt)<br/>
Changes:<br/>
Add all Rimco modifications:<br>
420dfc7 Fixed dynamics around current time. Fixed cache clean-up.<br>
7ee0572 Added support to skip station delay after short runs.<br>
28490a6 Fixed temperature unit switching.<br>
230f0fe Consider small gaps to be part of consecutive runs.<br>
3e1bc71 Scheduler fix where runs would be forgotten in case another blocked run would be at the same time.<br>
eeb4ffa Added new style favicons.<br>
976478c Better support for manual touch control.<br>
d25dec8 1. Added native weather module using Weather Underground data.<br>
d25dec8 2. Added ETo calculations based on Weather Underground data.<br>
d25dec8 3. Added precipitation in mm/h per station.<br>
d25dec8 4. Added new schedule type which sprinkles based on ETo calculations.<br>
93ba751 Small fixes.<br>
4e48b14 Small CSS fix.<br>
5f7214f Added station capacity.<br>
ff0f41c Critical fix for weather based program.<br>
8e3f468 Updated weather based schedule to partially take manual runs into account.<br> 
0d79b7e Fixed problems with saving run information for weather based schedules.<br>
bf4e3e4 Improved weather based scheduling looking at all constraints. Small robustness improvement in plug-in loader.<br>
81e8636 More correct scheduling and options database corruption protection.<br>
f36d2c0  Still improving db handling.<br>
399f36b Better fallback mechanism and caching for weather information.<br>
3fc5377 Improved weather caching.<br>
5ed5ebb Added plot for weather based water balance overview.<br>
68c224c Improved caption.<br>
09c68a6 Fix in predicted balance.<br>
627efff Added some rounding.<br>
425801f Increased recalculation frequency.<br>
e4dfec4 Hide graph in manual mode.<br>
22021fa Added weather based schedule logic to sprinkle less while it is raining.<br>
adf653a Added balance fix in schedule.<br>
d646d7f Fixed scheduling and graph updating.<br>
7a4fe64 Even more refreshing.<br>
66696d7 Prevent double planning.<br>
84dc4a8 Not sure yet what to pick as constant.<br>
420dfc7 Fixed dynamics around current time. Fixed cache clean-up.<br>
28ecda7 Schedule shortest runs first.<br>

July 19 2017
----------
(martinpihrt)<br/>
Changes:<br/>
1. Fix name in manifest app -> Sprinkler.<br>
2. Fix bug in real time plugin (+Add secondary NTP server).<br>

June 30 2017
----------
(martinpihrt)<br/>
Changes:<br/>
1. Add MQTT plugin. MQTT client to the OSPy daemon for other plugins to use to publish information and / or receive commands over MQTT.  Having a shared MQTT client simplifies configuration and lowers overhead on the OSPy process, network and broker.<br>
2. Fix bug in button control plugin. If a connection to the i2c bus is lost, 1 button has been triggered spontaneously.<br>

May 30 2017
----------
(martinpihrt)<br/>
Changes:<br/>
1. Add support to skip station delay after short runs. Create favicon.ico. Scheduler fix where runs would be forgotten in case another blocked (…un would be at the same time). Update theme.css.<br> 
2. Fix - limited event log output in "System Debug Information" plugin.<br>

May 10 2017
----------
(martinpihrt)<br/>
Changes:<br/>
1. Add text selector in "LCD plugin". Fix speed for text.<br>

Oct 18 2016
----------
(martinpihrt)<br/>
Changes:<br/>
1. Add function first version plugin "button control".<br>

Sep 14 2016
----------
(martinpihrt)<br/>
Changes:<br/>
1. Fix scheduler.py Run-Now program (if is set water level, program run time calculated with water level in "Run-Now" program.)<br>
2. Fix scheduler.py string Run-Now in program name.<br>

Aug 22 2016
----------
(martinpihrt)<br/>
Changes:<br/>
1. Add info on running stations xx in LCD plugin. Ex: If stations 1+2+3 is ON -> LCD print 1, 2, 3.<br>

Aug 19 2016
----------
(Vaclav Hrabe)<br/>
Changes:<br/>
1. Add NetAtmo support - read data from NetAtmo API of Rain module in weather_based_rain_delay plugin.<br>
2. Add czech translate for plugin.<br>
(martinpihrt)<br/>
Changes:<br/>
1. Fix error in stations.html checked master 2, fix in scheduler.py master_relay on/off, fix debug print only if relay has changed.<br>

Aug 18 2016
----------
(Vaclav Hrabe)<br/>
Changes:<br/>
1. Add NetAtmo support - read data from NetAtmo API of Rain module in weather_based_water_level plugin (martinpihrt: Checked, Tested and improved).<br>
2. Add czech translate for plugin (martinpihrt).<br>

Aug 16 2016
----------
(martinpihrt)<br/>
Changes:<br/>
1. Add support for master 2 station.<br>
2. Fix error in czech translate (home page, stations).<br>
3. Add support for master 2 stations to pressure_monitor plugin.<br>
4. Fix in helpers and lcd plugin Add cz string uptime.<br>

Aug 15 2016
----------
(martinpihrt)<br/>
Changes:<br/>
1. fix logging (czech string to debug file).<br>


Aug 11 2016
----------
(martinpihrt)<br/>
Changes:<br/>
1. Added [new FTP control plugin](https://github.com/martinpihrt/OSPy-plugins-temp/tree/master/plugins/remote_ftp_control) for remote control your OSPy without public IP addresses and [PHP script for control](https://github.com/martinpihrt/OSPy-PHPfileFTP).<br>

July 21 2016
----------
(martinpihrt)<br/>
Changes:<br/>
1. Added SSL support for HTTPS connections in options. For howto setup SSL read file https://github.com/martinpihrt/OSPy/blob/refactor/README.md.<br>

July 10 2016
----------
(martinpihrt)<br/>
Changes:<br/>
1. Fixed relay on the board (rele output 9) without stations 1-8 relay. Now is in test relay plugin function ready.<br>

July 5 2016
----------
(martinpihrt)<br/>
Changes:<br/>
1. Added languages support for all OSPy-temp-plugins (now Czech, English) without plugins: sms_adj, water_meter.<br>
2. Added new button in options for delete options.db file (delete all user settings and restore default value.<br> 

June 15 2016
----------
(martinpihrt)<br/>
Changes:<br/>
1. Added languages support for all OSPy-temp-plugins (now Czech, English) without plugins: air_temp_humi, button_control, sms_adj, volt_temp_da, water_meter, webcam.<br>

June 9 2016
----------
(martinpihrt)<br/>
Changes:<br/>
1. Added languages support for all OSPy-core-plugins (now Czech, English) and for LCD plugin from OSPy-temp-plugins.<br>
2. Changes OSPy font style in css and add buttons gap in plugins manager (Thanks janboreczech.)<br>

June 7 2016
----------
(martinpihrt)<br/>
Changes:<br/>
1. Added languages in the Options and all pages i18n (Czech, English).<br/>
2. Changes helpers.py, options.py, program.py, runonce.py, server.py, scheduler.py, version.py, webpages.py.<br/>
3. Changes base.html, help.html, home.html, log.html, login.html, options.html, plugins_install.html, plugins_manage.html, programs.html, program.html, restarting.html, runonce.html, stations.html.<br/>
4. Move to html code: static/scripts/basic.js, help.js, program.js, base.js.<br/>
5. Change jquery on to 2.2.4.min.js.<br/>
6. Added languages (Czech, English) in plugins/lcd_display.<br/>
7. Added in the Options backup configuration (file.db) - upload and download configuration file.<br/>
8. Fixed togle button on the home page for change temperature C/K.<br/>  


September 10 2014
----------
(martinpihrt)<br/>
Changes:<br/>
1. Added new functions in helpers.py: reboot, poweroff, restart, uptime and getIP.<br/>
2. Added new plugins:<br/>
   - System update (Rimco: Checked, tested and improved.)<br/>
   - Email (Rimco: Checked, tested and improved.)<br/>
   - SMS (Rimco: Globally checked and reformatted, not tested.)<br/>
   - LCD (Rimco: Globally checked and reformatted, not tested.)<br/>
   - Pressure Monitor (Rimco: Globally checked and reformatted, not tested.)<br/>
   - PCF8591 A/D converter read-out (Rimco: Globally checked and reformatted, not tested.)<br/>
3. Added pylcd2 library in /plugins for LCD plug-in.<br/>

September 9 2014
----------
(Rimco, Dan, Samer Albahra and Andrew Radke)<br/>
Changes:<br/>
1. Fixed plugin executable bits<br/>
2. Removed all old txt reading functions<br/>
3. Improved mobile app interface<br/>
4. Fixed timeline display errors.<br/>
5. Improved version numbering (partially automatic)<br/>
6. Added @media CSS extension<br/>

August 2014
----------
(Rimco and Dan)<br/>
Changes:<br/>
1. Improved weather level adjustment robustness, error logging and data removal.<br/>
2. Added on-off buttons to program page<br/>
3. Moved station names to JSON file<br/>
4. Moved options section to gv.py<br/>

July 22 2014
-----------
(Rimco)<br/>
Changes:<br/>
1. Split contents of the original ospi.py file into blocks that are more logical. (Should be improved even more.)<br/>
2. Removed numerous bugs regarding undeclared variables, unreachable code and misinterpretation of python classes. Tried to use python standards as much as possible.<br/>
3. Improved the way that plug-ins can adjust the water level. Each plug-in can now provide a water level adjustment which are combined by the main program.<br/>
4. Introduced template inheritance to solve many web-page inconsistencies and code duplication.<br/>
5. Fixed security issues where login-credentials were not checked. Introduced a ProtectedPage class as base class to be used for each page that should only be reachable if logged in.<br/>
6. Removed unused code, reduced code duplication.<br/>
7. Removed gv class (was not used at all) and put all global variables in the gv module itself.<br/>
8. Improved exception handling.<br/>
9. Because of the introduced template inheritance, plug-ins are now also using the same base template and are integrated better.<br/>
10. Improved page load speeds.<br/>
11. Added new weather-based water level adjustment plug-in that can change the water level depending on the history+forecast. This plug-in caches the queries made to WUnderground to reduce the number of queries, but a clean-up action needs to be added.<br/>
12. Removed files that should not committed to GitHub.<br/>
13. Removed APScheduler dependency.<br/>

July 11 2014
-----------
(Dan)<br/>
Changes:<br/>
1. Fixed reported bugs in the Home page irrigation timeline.<br/>
2. Fixed a bug that caused a momentary power pulse to stations during a cold boot.<br/>
3. Added error checking to Programs page to try and fix "server error".<br/>

June 23 2014
-----------
(Dan)<br/>
Changes:<br/>
1. A fix for the irrigation timeline on the Home page<br/>
2. The addidion of a "Plugins" button to the Home page<br/>

June 9 2014
-----------
(Dan)<br/>
Changes:<br/>
Software version 2.0
Jonathan Marsh's UI is now default under the master branch.
A version based on the original UI derived from OpenSprinkler firmware 1.8.3 is still available under the branch named "firmware_based.
This revision also includes several bug fixes.

May 4 2014
-----------
(Dan)<br/>
Changes, bug fixes:<br/>
1. Program now explicitly sets all valves to off at startup. Fixes a bug that sometimes valves were on at program load.<br/>
2. Fixed a bug that could freeze the program under certain conditions if a station name was blank.<br/>
3. Changing station names would not be updated properly - Fixed.<br/>
4. Changed how ospi.py handles time and date. Changes such as to or from daylight time are now automatic. Time zone setting it options no longer has an effect.<br/>
5. Plugins must now have group permission set to executable in order to load. Allows plugins to be selectively enabled/disabled.<br/>
6. Removed deprecated "ospi_addon.py" file from program directory.

April 4 2014
-------------
(Dan)<br/>
New plugin architecture including a plugin to support Samer's new JavaScript app

February 7 2014
--------------
(Dan)<br/>
Added support for Rain sensor and partial support for relay on OSPi Rev. 1.3.<br/>

November 12 2013
--------------
(Dan)<br/>
Modified program to run on either OSPi or OSBo<br/>

October 16 2013
--------------
(Dan)<br/>
Additions, bug fixes:<br/>
1. Fixed a bug that would cause an error in program preview when a master was enabled.<br/>
2. Changing to manual mode would clear rain delay setting, Setting rain delay in manual mode would switch to program mode - fixed.<br/>

October 11 2013
--------------
(Dan)<br/>
Additions, bug fixes:<br/>
1. Fixed a bug that would cause an error when a master was enabled and making changes to station settings.<br/>
2. added approve_pwd function and removed redundant code.<br/>
3. removed write_options function and added options.txt file to distribution.<br/>

October 4 2013
--------------
(jonathanmarsh)<br/>
Additions, bug fixes:<br/>
1. Improved options handling and passing logic<br/>
2. Added a "System Name" option to help users distinguish between multiple systems<br/>
3. Configurable station name length (increased default to 32)<br/>
4. Added logging options to options page<br/>

(Dan)<br/>
Additions, bug fixes:<br/>
1. Moved RasPi specific code into try-except blocks allowing program to run on multiple platforms<br/>
2. Added "write_options" function to create/update new style options.txt file in data directory.<br/>
3. Fixed a bug in new options code that prevented master station from being selected.<br/>
4. Fixed a bug that caused an exception when the number of expansion boards was reduced.<br/>

October 1 2013
--------------
Changes:<br/>
1. Changed the pin numbering option in the RPi.GPIO module from BCM to BOARD.<br/>

September 23 2013
--------------
Additions, bug fixes:<br/>
1. Added a new revisions page to the native web interface.<br/>
2. Modified the home.js file to show time zone info in the last run log near the bottom of the page.<br/>
3. Fixed a bug in concurrent mode that kept a station running after it's duration had expired.<br/>
4. Fixed a bug that would cause an exception (freeze the program) after the number of expansion boards was changed in Options.<br/>
5. Fixed a bug that would stop a running station and clear scheduled stations when the number of expansion boards was changed in Options.<br/>

September 10 2013
--------------
Additions, bug fixes:<br/>
1. Added a per-station "Ignore rain" option that allows a station to operate during rain delay or if a rain sensor detects rain.<br/>
2. Modified the program to use the HTTP port setting from the Options page.<br/>
3. Improved the way the program tracks current time. This simplified the code and should eliminate some timing bugs.<br/>
4. Edited Denny's init.d startup script to remove IP address and port settings no longer needed.<br/>

August 30 2013
--------------
Additions, bug fixes:<br/>
1. Modified the program to use only the time zone setting from the Options page and not the tz setting from the py.<br/>
2. Made the CPU temperature readout on the home page clickable to toggle between C and F.<br/>
3. Added a copy of Denny Fox's init.d auto startup script<br/>

August 25 2013
--------------
Additions, bug fixes:<br/>
1. Implemented improved installation and update methods using GitHub.<br/>
2. Modified the program to automatically create default config files on new installations. This also prevents existing settings from being overwritten.<br/>
3. Added a "Run now" button to the programs page. Allows a schedule program to be started at any time. This overrides (stops) any running program.<br/>
4. Added a readout of the Raspberry Pi's CPU temperature to the home page.<br/>
5. Fixed a bug that would allow a station to be stopped / started without a password ueing the HTML API.<br/>
6. Fixed a bug that would display an incorrect start day for a schedule program.<br/>

August 1 2013 Reved to firmware V 1.8.3
---------------------------------------
Now supports concurrent operation.<br/>
Additions, bug fixes:<br/>
1. Added Sequential/Concurrent option.<br/>
2. Added a function to detect Pi board rev and auto-configure GPIO pins for rev 1 boards.<br/>
3. Fixed a bug in manual mode that would cause any zone with a master association to stop the master when turned off, even if another station with a master association was still running.<br/>
4. Changed how ospi.py handles master zone associations. The program should now work with more than 3 expansion boards (untested in hardware but at least 5 expansion boards, 64 stations work in software).<br/>

July 21 2013
------------
Bug fixes:<br/>
1. Fixed a bug that kept an in progress program running after it was disabled.<br/>
2. Added error checking to prevent an 'lg' KeyError<br/>
3. When a new program was added, it became program 1 instead of being added at the end of the list. - fixed.<br/>
4. When Rain Delay was set, running stations did not stop. - Fixed.<br/>
5. Added a 1.5s delay in the screen refresh of manual Mode to allow active stations and last run log time to update.<br/>

July 19 2013
------------
Code re-factored:<br/>
1. Eliminated over 100 lines of redundant code. The code is now much closer to the micro-controller version. Manual Mode and Run-once now rely on the main loop algorithm. This eliminates potential conflicts and makes the code easier to maintain. The program should now be more stable and have fewer bugs although the UI is a little slower.<br/>
2. Changed bit-wise operations to make them more reliable.<br/>
3. Station names now accept Unicode characters allowing names to be entered in any language.<br/>
4. Faveicon now appears on all pages.<br/>
5. A small bug in the display of Master valve off time in the program preview has been fixed. The off time was 1 minute short.<br/>
6. A file named 'sd_reference.txt' has been added to the OSPi directory. It contains a list with descriptions of the values contained in the global settings dictionary variable (gv.sd) which holds most settings for the program. These values are kept in memory and also stored in the file OSPi/data/sd.json to persist across system restarts. This is for the benefit of anyone who wishes to tinker with the code.<br/>

It is recommended to re-install the entire OSPi directory from GitHub. You can keep your current settings by saving the contents of the OSPi/data directory to another location before installation, then replace the contents of the newly installed directory with your saved files.

july 10 2013
------------
Bug fixes and additions:<br/>
1. Fixed a bug that prevented zones 9+ from running.<br/>
2. The Run once program was not observing the station delay setting - Fixed<br/>
3. Made the sd variable an attribute of the gv module. All references to sd... are now gv.sd... This should potentially fix several bugs, Specifically the Rain delay seems to be working properly now.<br/>
4. The Graph Programs time marker was not recognizing the time zone setting from the Options page - fixed.<br/>
5. Time displayed on the last run line of the main page was not correct - fixed.<br/>
6. Added a faveicon which will help distinguish the OpenSprinkler tabs on the browser.<br/>
7. Added an import statement and file which provide a stub for adding user written custom functions to the interval program without modifying the program itself.<br/>

Jun 26 2013
-----------
1. Last run logging is now working for manual mode when an optional time value is selected, even if more that one station is started.<br/>
2. Fixed a bug that prevented the home page display from updating when running irrigation programs.<br/>
3. Includes a fix from Samer that allows the program preview time marker to update properly.<br/>

Jun 20, 2013
------------
This update includes:<br/>
1. Changed the way ospi.py handles time. It now uses the time zone setting from the OS options page. It also eliminates the auto daylight savings time adjustment that was causing problems for some users.<br/>
2. Fixes a bug mentioned on the forum that caused Samer's app to not update in program mode.<br/>
3. Fixes a bug that caused a program to re-start after the "Stop all stations" button was clicked.<br/>
4. A partial fix for the "last run" problems. Still need to get manual mode with an optional time setting working.<br/>
5. Added a docstring at the top of the ospi.py file with the date for version tracking.

Jun 19, 2013
------------
  Applied Samer Albahra's patch so that the program will work with Samer's mobile web app.
  Per forum discussion: http://rayshobby.net/phpBB3/viewtopic.php?f=2&t=154&start=40#p781<br/>

