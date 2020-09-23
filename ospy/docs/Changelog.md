OSPy Changelog
====

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

