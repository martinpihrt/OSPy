OSPy Web Interface Guide in English
====

    Logging in
    Home page
        Normal - Water Level
        Active - Rain Delay
        Schedule - Manual
        Enabled - Disabled
        Stop All Stations
        Water balance Graph
        Suppressed by Rain Delay
        Rain sensed
        CPU Temp
        CPU Usage
        Software version
        External IP
        Working
    Programs page
        Add a New Program
        Run Now
        Edit 
        Delete All 
        Enable or Disable a Program
        Schedule type
            Selected days (Simple)
                Start time
                Duration
                Repeat
                Repetitions
                Pause
            Selected days (Advanced)
                Schedule
            Repeating (Simple)
                Water interval
                Starting in
                Start time
                Duration
                Repeat
                Repetitions
                Pause
            Repeating (Advanced)
                Water interval
                Starting in
                Schedule
            Weekly (Advanced)
                Monday-Sunday
            Custom
                Water interval
                Starting in
                Day 1 - Day 7
            Weekly (Weather based)
                Irrigation min
                Irrigation max
                Run max
                Pause ratio
                Preferred Execution Moments
                    Day
                    Start time
                    Priority
                    Add - Delete
        No adjustments
        Cut-off
    Run Once page
        Run Now
        Reset Time
    Plugins page
        Manage
        Install New Plugin
            Custom plug-in (ZIP)
            Github (https://github.com/martinpihrt/OSPy-plugins/archive/master.zip)  
        Disable All
        Enable All 
        Enable check updates
        Automatic updates
    Log page
        Download log as
        Clear Log
        Clear Log Email
    Options page
        System Section
            Show Tooltips
            Set System name
            Select System theme
            Clock format
            HTTP IP addr
                About the port number 
            HTTP/S port
            Show plugins on home
            Show sensors on home
            Select Language
            Show pictures at stations          
        Weather Section
            Use Weather
            Dark Sky API key
            Location
            Elevation
        Users Section
            Disable security
            Admin login name
            Current password
            New password
            Confirm password
            Aditional users
        Security Section             
            Use HTTPS access
            Domain name 
            Use Own HTTPS access
        Sensors
            Password for uploading
            AES key for sensors
            Generate new key              
        Station Handling Section
            Maximum usage
                About Sequential and Concurrent modes
            Number of outputs
            Station delay
            Minimum runtime
        Configure Master Section
            Master station
            Master two station
            Activate relay
            Master on delay
            Master off delay
            Master two on delay
            Master two off delay 
        Rain Sensor Section
            Use rain sensor
            Normally open
        Logging Section
            Enable run log
            Max run entries
            Enable email log
            Max email entries
            Enable debug log
        System Restart Section
            Restart
            Reboot
            Shutdown
            Default 
        System Backup Section
            Download
            Upload 
        SSL certificate
            Upload    
            Generate        
    Stations page
        Station 
        Name
        Usage
        Precipitation
        Capacity
        ETo factor
        Balance adjustment
        Connected
        Ignore Rain
        Activate Master?
            None
            Activate Master
            Activate Master Two
            Activate Master 1/2 by program
        Notes 
    Sensors page
        Add a New Sensor
            Sensor Parameters
        Delete All sensors         
    Help page
        OSPy
            Readme
            Changelog
            Programs
            Web Interface Guide - Czech
            Web Interface Guide - English
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
    Logging out

----

# Logging in
The login page presents a text box for entering a password. The default password is **opendoor**. 
It is recommended that you change to a new password on the Options page.
Enter the password and click the **LOGIN** button.

----

# Home page
The Home page is the main control center of the web interface. It includes:

* A clock showing the current time at the location of the controller. This also appears on all pages.
* A navigation bar at the top for moving between pages of the interface. This is also present on the other pages except the login page.
* A set of buttons for making global changes to the behavior of the system including.
* A time line that provides information about completed and scheduled irrigation events.
* A graph that provides information about irrigation events.
* A footer that is present on all pages (if user is logged). The footer includes: CPU Temp, CPU Usage, Software version, External IP, Working.

## Normal - Water Level
A button that allows setting the "Water Level" which is a global percentage the run time for all irrigation programs.

## Active - Rain Delay
A "Rain Delay" button which allows suspending irrigation for all stations except ones that have been set to ignore rain on the Stations page.

## Schedule - Manual
An Schedule - Manual button which switches the system between Schedule, automatic mode, and manual mode which allows direct control of stations.

## Enabled - Disabled
For controlling the overall operation of the OSPy software.

## Stop All Stations
A "Stop all Stations" button for immediate cancellation of a running irrigation program or station.

## Water balance Graph
If at least one program is set in the scheduler, a graph with the amount of water delivered for each station (programs) will be drawn at the bottom of the screen.

## Suppressed by Rain Delay
When the rain delay is activated, "Rain Delay" is displayed and all stations without exception will be blocked for a certain time.
  
## Rain sensed
If the rain sensor is activated, "Rain sensed" is displayed and all stations with no exception will be blocked.

## CPU Temp
The Temperature of the Raspberry pi's CPU temperature. The displayed temperature can be toggled between C and F.

## CPU Usage
The Usage of the Raspberry pi's CPU usage. The displayed usage as %.

## Software version
A link to the project's software repository and the revision number of the installed software.

## External IP
The External IP address for OSPy system. Connected your network to provider. Tested via pihrt.com.

## Working
The Running time of the system Raspberry pi's.

----

# Programs page

## Add a New Program

## Run Now

## Edit 

## Delete All 

## Enable or Disable a Program

## Schedule type
  
### Selected days (Simple)

#### Start time

#### Duration
 
#### Repeat
    
#### Repetitions
    
#### Pause

### Selected days (Advanced)

#### Schedule

### Repeating (Simple)
    
#### Water interval
    
#### Starting in
    
#### Start time
    
#### Duration
    
#### Repeat
    
#### Repetitions
    
#### Pause

### Repeating (Advanced)
   
#### Water interval
    
#### Starting in
    
#### Schedule

### Weekly (Advanced)

#### Monday-Sunday

### Custom

#### Water interval
    
#### Starting in
    
#### Day 1 - Day 7

### Weekly (Weather based)

#### Irrigation min
    
#### Irrigation max
    
#### Run max     

#### Pause ratio
    
#### Preferred Execution Moments
    
#### Day
    
#### Start time
   
#### Priority
    
#### Add - Delete

## No adjustments

## Cut-off

----

# Run Once page
The Run Once page presents a list of enabled stations with minute and seconds fields for each. This page can be used for testing and to provide additional irrigation on a one-time basis.

## Run Now
This button activates all selected preset stations.
   
## Reset Time
This button delete all presets time for all stations.

----

# Plugins page
Use the Plugins page to configure or controll all plugins in OSPy system.
  
## Manage
After clicking the "Manage" button, the OSPy Extension Manager window will open. All available extensions can be turned on, off, installed from a repository, etc...
  
## Install New Plugin
After clicking on the button "Install New Plugin" a window with a remote repository will open, where we can choose available plugins for OSPy installation and read general information about all plugins.
  
### Custom plug-in (ZIP)
The Extension Manager allows you to install custom plugin that are not published to the remote repository (such as your personal plugin) on OSPy. Use the "browse" button to select the desired file in our computer for installation in the OSPy system. The plugin file (zip) must contain the complete plugin structure (init, templates, i18n, readme, etc.)

### Github (https://github.com/martinpihrt/OSPy-plugins/archive/master.zip)  
The above location has a repository with available OSPy plugins.

## Disable All
The button disables all installed extensions.
   
## Enable All 
The button enables all installed extensions.
  
## Enable check updates
When the button is active, a new version of the plugin is automatically checked in remote storage after an hour. "Update" message appears when new version is available.
  
## Automatic updates
When the button is active, when a new version of an plugin is available, the plugin is automatically updated. Note: The OSPy system is constantly evolving and if the OSPy system changes significantly and the user does not update the OSPy system, the upgrade may not work after the upgrade. Always update the OSPy system first and then all plugins!

----

# Log page
Use the Log page to view logs in OSPy system. The number of records is set on the "Options page".
    
## Download log as
The "Download log as Excel log.csv" link allows you to save the irrigation log as a csv file (Excel program) to your computer.
* The table structure is: Date, Start Time, Zone, Duration, Program. Data is separated by a comma.
* Example: 2019-08-12 	05:00:00 	Filtrace 	60:00 	Filtrace

The "Download log as Excel log email.csv" link allows you to save a record of sent emails as a csv file (Excel program) on your computer.
* The table structure is: Date, Time, Subject, Body, Status. Data is separated by a comma.
* Example: 2019-08-12 	06:00:04 	Odesláno 	CHATA SYSTÉM 	Ukončené zalévání-> Program: Filtrace , Stanice: Filtrace , Začátek: 2019-08-12 05:00:00 , Trvání: 60:00 , Water-> Množství vody v zásobníku: Level: 170 cm (90 %), Ping: 95 cm, Volume: 1.28 m3 , Temperature DS1-DS6-> SKLEP: 21.1 ℃ ČERPADLO: 33.5 ℃ BOJLER: 26.6 ℃ UVNITŘ: 22.1 ℃ STUDNA: 12.2 ℃ 
   
## Clear Log
After pressing the "Clear Log" button all records of the irrigation run are deleted. The action is irreversible.

## Clear Log Email
After pressing the "Clear Log Email" button all records of sent emails will be deleted from the system. The action is irreversible.

----

# Options page
Use the Options page to configure system wide settings. 
The Options page includes several collapsible sections.
It opens with the System section expanded. Click a blue bar to open or close a section.

## System Section
The System section contains settings that identify the system and its local.

### Show Tooltips

* Click the SHOW TOOLTIPS button to display descriptive information about each option.
* Click the button to hide Tool tips.

### Set System name
Naming the system is useful when working with several controllers.

* Enter a unique descriptive name for the system.
* Click the Submit Changes button at the bottom of the page to save the change.

When the system name has been changed from OpenSprinkler Pi, the default, it will be displayed in the header of each page for easy system identification.

### Select System theme
There are several topics to choose from in the list (green mode, black and white mode...)

### Clock format
The 24-Hour clock option selects between the international 24 hour clock format, sometimes referred to as military time, and the 12 hour-AM/PM format.

* Uncheck the box to select the 12 hour, AM/PM format.
* Click the Submit Changes button at the bottom of the page to save the change.

You will be taken to the home page and the clock will be in the selected format.

### HTTP IP addr
IP Address used for HTTP/S server socket. IPv4 or IPv6 address (effective after reboot.) Default is 0.0.0.0.

#### About the port number 
The HTTP port number is part of the system's URL.
Port 80 is the default number for web sites and as such does not need to be included when the URL is entered into a browser's address bar. Many web servers use port 80 by default.
If you are running another server on the same Raspberry Pi as OSPy and using the same port number there will be a conflict and OSPy may not start.
You can avoid the conflict by changing OSPy's port number on the Options page to something like 8080. If you change the port number OSPy uses you will need to include that number, preceded by a colon, in the URL for OSPy's web interface. For example:
[URL of the Raspberry pi]:8080

### HTTP/S port
The HTTP/S port number is part of the system's URL. Port 80 is the default number for web pages.

* Click in the text field next to the HTTP/S port option.
* Type the port number you wish to use, e.g. 8080.
* Click the Commit Changes button at the bottom of the page.

You will be returned to the home page. The system will reboot but there is no visible indication of the reboot in the web interface. Wait at least 60 seconds, then add the new port number to the URL of the Pi, preceded by a colon (:), and try re-connecting to OSPy.

### Show plugins on home
If you want to display measured data from the extension (wind, temperature, level ...) on the home page, check the box. If we don't want to show data from the extension, we uncheck it.
* Please note that it is necessary to have the extension enabled and properly set in order for the data to be displayed correctly.

### Show sensors on home
If you want to display measured data from the sensors on the home page, check the box. If we don't want to show data from the sensors, we uncheck it.
* Please note that it is necessary to have the sensors enabled and properly set in order for the data to be displayed correctly.

### Select Language  
The language option can change the language used in the web interface.

* Click the downward arrow at the right of the language field to display a list of available languages.
* Click the language you wish to use in the interface.
* Click the Submit Changes button at the bottom of the page.

The software will restart and after a few seconds the interface will appear in the language selected.

### Show pictures at stations  
Select the check box to display images for the stations on the home page and the stations page.  

## Weather Section
The weather section allows you to access the weather forecast service for your location. You must register for this feature on the web (https://darksky.net/dev).
According to the weather forecast, the irrigation cycle can then be automatically adjusted (if we choose a plugin that uses the weather forecast).

### Use Weather
Enabling or disabling connection to service Dark Sky.

### Dark Sky API key
To make use of local weather conditions, a Dark Sky API key is needed.

### Location
City name or zip code. Used to determine location via OpenStreetMap for weather information.

### Elevation
Elevation of this location in meters. (need not be filled)

## Users Section
Here is the credentials of a system administrator (main user) who can manage the entire system.
For improved security it is recommended that you change the system password from the default opendoor and user name default admin. You can also disable the password requirement if desired.

* Click the triangle at the left of the bar labled Change password to expand the section.
* Check the "No password" box if you have a very good reason to disable password and name protection. The system will no longer require the user to log in. Access to all sections will be allowed.
* Enter your login name the the boxes labeled Administrator name.
* Enter the current password in the first text box This will be opendoor on a new installation.
* Enter your new password into the the boxes labeled New password and Confirm password.
* Click the Submit Changes button at the bottom of the page.
You will return to the home page. Your new password and name will be required the next time you log in.

### Disable security
Leave the Disable security box unchecked unless you have a very good reason to disable password protection.

### Login name
Enter the Login name. This will be admin on a new installation.

### Current password
Enter the current password in the first text box. This will be opendoor on a new installation.

### New password
Enter your new password into the the boxes labeled New password.

### Confirm password           
Enter your Confirm into the the boxes labeled Confirm password.

### Aditional users
After clicking on the button, a page will open where we can create and possibly edit new users to access the system.

## Security Section
In this section you can customize a secure connection using SSL and a certificate.

### Use HTTPS access 
If we have configured the OSPy server for enhanced security of SSL data transmission, select the "Use HTTPS" checkbox. If the "Use HTTPS" option is checked and the server is not set up correctly, OSPy will run as an http server without security.

### Domain Name
The certificate is located on the system in the '/etc/letsencrypt/live/' domain name '/fullchain.pem' and '/etc/letsencrypt/live/' domain name '/privkey.pem' directories. It is necessary to install the certificate manually into the system (Linux) using the "Certbot" tool (the use of https will not be reflected in OSPy until the OSPy is restarted).
* The procedure for installing Certificate Services can be found in the "Readme" help file or on Github.

### Use Certbot
For using "https" in OSPy options you must follow these procedures. SSL certificate via Let�s Encrypt certification authority.
The Certbot (https://certbot.eff.org/) and Let�s Encrypt (https://letsencrypt.org/) for enabling SSL security.

Execute:
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

### Use Own HTTPS access
If "Use Own HTTPS access" is selected in OSPy settings, file: fullchain.pem and privkey.pem must You insert to folder ssl in OSPy location. Warning: OSPy must be next restarted.
For manual generating certificate example:
```bash
sudo openssl req -new -newkey rsa:4096 -x509 -sha256 -days 3650 -nodes -out fullchain.pem -keyout privkey.pem  
```

The second way is to use the "generate" button in the SSL certificate tab.

## Sensors Section
The Sensors section contains settings for sensors security.  

### Password for uploading
Password for uploading firmware from OSPy to sensor (for all used sensors - the same password must be used in sensor options.) Default is: "fg4s5b.s,trr7sw8sgyvrDfg".

### AES key for sensors
AES key for sensors. The length must be 16 characters (for all sensors used - the same code must be used in the Arduino code in the sensor.)

### Generate new key
After pressing the button, a new random 16-digit key is generated for use in the sensors.

## Station Handling Section
The Station Handling section contains settings for stations.

### Maximum usage
Determines how the stations combine. Concurrency 0 or sequential >= 1 (2, 3 ...) If all stations have sequential use.

#### About Sequential and Concurrent modes
* When setting the sequence (Maximum usage > = 1), only one (or more stations if set> = 1) station (output) - for example: main station 1 and station 3 flower beds is always started. After the program time has elapsed, the main station 1 and the station 3 turn off. The main station 1 and the station 4 lawn will start. The two stations (for example, the flower beds and the lawn shown in our example) will never sleep together. Sequence mode is important if we do not have such a water source (pressure and water quantity) available to cover all stations simultaneously.
* When you set up concurrency (Maximum usage = 0), an unlimited number of stations are set to run at any given time. For example, the main station 1 (pump) and the stations 2, 3, 4 are switched on. Concurrent irrigation reduces the irrigation time but requires a larger water source.

### Number of outputs
The total number of outputs available is (8 outputs + x extension board.) The number of outputs can be set higher than we actually have the number of physical outputs (we create the virtual outputs).

### Station delay
Enter the number of seconds to delay between station operations. Time in seconds between 0 and 3600.

### Minimum runtime
Skip station delay if run time is less than this value (in seconds) between 0 and 86400.

## Configure Master Section
The section "Configure Master Section" contains settings for all master stations. The master station is activated when any station is activated.
* The master station is a pump or the main valve with water as the water supply to the system.

### Master station
Selection of the first main station (for pump or main valve).

### Master two station
Selection of the next main station (for pump 2 or main valve 2).

### Activate relay
If checked, the relay will also be activated as the main output. The relay has activating from first or second master stations.

### Master on delay
Delay ON for master station (in seconds), between -1800 and +1800.

### Master off delay
Delay OFF for master station (in seconds), between -1800 and +1800.

### Master two on delay
Delay ON for master two station (in seconds), between -1800 and +1800.

### Master two off delay 
Delay OFF for master two station (in seconds), between -1800 and +1800.

## Rain Sensor Section
Enable and set the switch type of a rain sensor. If you are using a Raspberry Pi and want to connect a Rain Sensor directly to the GPIO pins use pins 8 and 6 (ground).

### Use rain sensor
Click the Use rain sensor check box to enable rain sensing.

### Normally open
Leave the Normally open box checked if your sensor's switch is the normally open type otherwise un check the box. See the rain sensor's user guide for information about the switch type.

## Logging Section
Turn on logging and set the number of records to keep. Turn on logging for email and set the number of records to keep.
  
### Enable run log
Click the Enable run log checkbox. This will turn logging on and enable irrigation history on the Home page's timeline.

### Max run entries
Enter the number of records to keep in the log Set this to a number that will cover a reasonable length of time such as a week or month. This will depend on the number of programs and stations you have. There will be one record for each time a station is run.

### Enable email log
Click the Enable email log checkbox. This will turn logging on and enable irrigation history via sends email.

### Max email entries
Enter the number of records to keep in the log Set this to a number that will cover a reasonable length of time such as a week or month. This will depend on the number of programs and stations you have. There will be one record for each time a email has send.

### Enable debug log
Click the Enable debug log for saving all internal operation in OSPy to file for better debugging. *Note:* storing data too frequently in a file can damage the SD card or reduce the capacity of the SD card (storage) after a long time.

## System Restart Section
The System Restart section contains buttons for restarting the software, for rebooting the hardware, for shuttdown the hardware and delete all setings to default.

### Restart
The Restart button restarts the software only. It is a quick way to implement siftware changes.

### Reboot
The Reboot button reboots the Raspberry Pi. This takes longer but does a complete restart of the system.

### Shutdown
The Shutdown button shutting power the Raspberry Pi hardware.

### Default 
The Default button clears all custom user settings to the default clean OSPy installation.

## System Backup Section
If we want to back up all the settings of our irrigation system or transfer the settings to another system, we will use the "Download" and "Upload" button. 

### Download
The Download button is used to download the configuration file to your computer for later use or to restore the OSPy system. Not only is the database file (options.db) saved, but the stations folder is also saved, where the station images are stored. At the same time, the events.log log file (if it exists) is saved. Everything is saved in a zip file (Example: ospy_backup_systemname_4.12.2020_18-40-20.zip). We can easily identify from which OSPy system the backup comes. The SSL folder where is the certificate is not stored for security reasons in to backup zip file!

### Upload 
The Upload button allows you to insert and restore OSPy system (for example, when you reinstall a Linux system). The uploaded file must be zip file! The following paths and files must be in the

```bash
*.zip folder:
ospy/data/events.log  
ospy/data/options.db  
ospy/data/options.db.bak  
ospy/images/stations/station1.png  
ospy/images/stations/station1_thumbnail.png 
``` 
Or other pictures of stations in the same format.

## SSL Certificate
If we have our own SSL (https) security certificate (fullchain.pem and privkey.pem) we can upload it here using the form.

## Generate
If we want to generate an SSL certificate, press the "generate" button. A certificate is generated in the ssl directory. Then in the settings/security we check the "own HTTPS" option and then restart the OSPy.

### Upload
The "Upload" button sends the attached files (fullchain.pem and privkey.pem) to the ssl folder in the OSPy directory.

----

# Stations page
On the "Stations" page, we set the names of stations, properties around the use of water, control of the master stations.

## Station 
Automatic numbering to mark stations. For example 1 = station 1, 2 = station 2...

## Name
User name of stations for better identification in the system, for example "lawn".

## Usage
Set concurrency (0) or sequence (> = 1) for certain stations. More about concurrency or sequence in the text above in the section "Settings / About sequential and concurrent modes".

## Precipitation
The amount of water per hour in mm that atomises the sprinklers at the station. Used for weather-based programs. To measure this value, it is advisable to obtain, for example, a plastic rain gauge.

## Capacity
The amount of water that the soil can store above level 0. Used for weather-based programs.

## ETo factor
Factor used to multiply the ETo factor for weather-based programs. Use a value higher than 1 for sunny / dry soil, use a value lower than 1 for shade / wet soil.
* Type of soil

Soils have different properties that make them unique. Knowing the type of soil you have will help you identify its strengths and weaknesses. While soil consists of many elements, the place to start is with your soil type. You only need to monitor the composition of the soil particles. OSPy allows users to determine the soil type for each zone (station), allowing for more accurate and efficient watering calculations. Different soil types react differently to water; clay soils tend to drain, while clay soils can retain water for a long time, etc. The amount of water contained in the soil after the excess water is drained and the soil retention capacity is referred to as field capacity (measured in inches or millimeters).

### Bottle test
How to find approximate proportions of sand, mud and clay? This is a simple test that will give you a general idea of ​​the proportions of sand, mud and clay present in the soil. Place 5 cm of soil in the bottle and fill with water.
Mix the water and soil well, remove the bottle and do not touch it for an hour. After an hour the water becomes clear and you will see that larger particles have settled:

- Pieces of organic matter may float on the water surface
- There's a layer of clay on top.
If the water is still not clear, it is because some of the finest clays are still mixed with water
- In the middle is a layer of mud
- There is a layer of sand at the bottom

* Measure the depth of sand, mud and clay and estimate their approximate ratio.

The following three types of particles can form your soil: clay, sand and mud. Most soils are a combination of these three particles, but the type of particle that dominates dictates many of the properties of your soil. The ratio of these sizes determines the type of soil: clay, clay, clay, mud, etc.

* Ideal soil is 40% sand, 40% mud and 20% clay. This mixture is referred to as aluminum. It takes the best of any type of soil particles. It has good drainage of water and allows air to penetrate the soil like sand, but also maintains moisture well and is fertile as mud and clay.

## Balance adjustment
Increase or decrease the water balance for weather-based programs (unless set to 0).

## Connected
If we have a station connected (it is physically connected) and we want to use it (it is visible in the selection in the programs, on the homepage ...), check "Connected". If you do not use the station and do not want to publish in the OSPy system leave the "Connected" unchecked. If a station is used as "master station" or "2 master stations" in the system, it cannot be checked or unchecked (deactivated) in the table.
The main station is assigned in the system settings "Options / master station".

## Ignore Rain
If you check "Ignore Rain" for a station, the station will be activated according to the program regardless of whether the rain delay is set or whether the rain sensor detects rain. We can use this option, for example: in a greenhouse where it does not rain and we need to water it regularly or, for example: to trigger pool filtration, which we also clean regardless of whether it rains.

## Activate Master?
### None
No master station will be used (when this station is activated, the master station will not be activated).
### Activate Master
If you want the master station (eg pump or main water valve) to be activated when a station is activated, select the "Activate Master".
### Activate Master Two
If you want the second master station (eg second pump or other water source) to be activated when a certain station is activated, select the "Activate Master Two".
### Activate Master 1/2 by program
If you want to select master station or master station two with a program, select the "Activate Master 1/2 by program". For a program, it is then possible to select which master station is to use for this station (example: program 1 controls stations 1-4 and master station 5. Program 2 controls stations 1-4 and second master station 6).

## Notes  
Notes are for operating the OSPy system. It can be noted for example: what types of el. valve, sprinkler etc. we have used in the system.

## Image
After clicking on the window, a page will open on which you can upload your own image to the station.   

----

# Sensors page
On the "Sensors" page, we can add or delete sensors that perform various functions in the OSPy system.

## Add a New Sensor
The button "Add a New Sensor" add new sensor in the system. The sensors settings are listed below in "Sensor Parameters".

## Sensor Parameters
Two types of communication are used for sensors:  
* Wireless (radio) - ID radio sensor  
* Network (Wi-Fi/LAN) - MAC address, IP address 
You can choose from 6 different types of sensors:  
* Dry Contact  
* Leak Detector  
* Moisture  
* Motion  
* Temperature  
* Multisensor

### Enable sensor
Enabling or disabling this sensor.

### Sensor name
Type Sensor Name. Sensor names must be non-null and unique.

### Sensor type
Select the sensor type.
#### Dry Contact
* Open Program(s) Mark the required programs to run.
* Closed Program(s) Mark the required programs to run.

#### Leak Detector
* Sensitivity (0-100%) When this level is exceeded, the high program(s) is activated.
* Stabilization Time (mm:ss) The detector will not respond to the change for this set time.
* Low Program(s) Mark the required programs to run.
* High Program(s) Mark the required programs to run.

#### Moisture
* Low Threshold (0-100%) When this level is exceeded, the low program(s) is activated.
* Low Program(s) Mark the required programs to run.
* High Threshold (0-100%) When this level is exceeded, the high program(s) is activated.
* High Program(s) Mark the required programs to run.

#### Motion
* Program(s) Mark the required programs to run.

#### Temperature
* Low Threshold (0-100 �C/�F) When this level is exceeded, the low program(s) is activated.
* Low Program(s) Mark the required programs to run.
* High Threshold (0-100 �C/�F) When this level is exceeded, the high program(s) is activated.
* High Program(s) Mark the required programs to run.  
The temperature is displayed in degrees Celsius or degrees Fahrenheit, depending on how the temperature is set on the home page (by clicking on the temperature, you can change the units).

#### Ultrasonic
* TODO

### Type of communication
Select communication type for sensor.
#### Radio
Enter sensor ID for your radio sensor. Radio ID must be non-null and unique.

#### Wi-Fi/LAN
* Enter Sensor MAC Address. Example: aa:bb:cc:dd:ee:ff
* Enter Sensor IP Address. Example: 192.168.88.10 

### Sample Rate
Enter the sampling time in minutes and seconds (mm:ss).

### Log Samples
Enable sample logging.

### Log Events
Enable event logging.

### Text/Email Events
Allow sending an E-mail when there is an event. For this function is requred plugin E-mail notification!

### Notes
Here we can make our notes.

## Delete All sensors 
The button "Delete All sensors" deletes all added sensors in the system.

----

# Help page
On the "Help" page we can find documentation for all Plugins, system OSPs, system changes, API access, web interface.

## OSPy
### Readme
Main documentation for OSPy, system installation, board interconnection, license.

### Changelog
Changes to OSPs or Plug-ins.

### Programs

### Web Interface Guide - Czech
Web interface help in Czech language.

### Web Interface Guide - English
Web Interface Help in English.

## API
### Readme
The proposal is to have a proper, modern web-API built on the CRUD principle using JSON as data-container format.

### Details
HTTP/s Method Mapping.

## Plug-ins
Readme
The basic structure is as follows:
plugins
+ plugin_name
  + data
  + docs
  + static
  + templates
  + __init__.py
  \ README.md

The static files will be made accessible automatically at the following location: /plugins/plugin_name/static/...
All * .md files in the docs directory will be visible in the help page. *

Available plug-ins:

* Usage Statistics
* LCD Display
* Pressure Monitor
* Voice Notification
* Pulse Output Test
* Button Control
* CLI Control
* System Watchdog
* Voltage and Temperature Monitor
* Remote Notifications
* System Information
* MQTT
* Air Temperature and Humidity Monitor
* Wind Speed Monitor
* Weather-based Rain Delay
* Relay Test
* UPS Monitor
* Water Consumption Counter
* SMS Modem
* Signaling Examples
* E-mail Notifications
* Remote FTP Control
* System Update
* Water Meter
* Webcam Monitor
* Weather-based Water Level Netatmo
* Direct 16 Relay Outputs
* MQTT Zone Broadcaster
* MQTT Slave
* System Debug Information
* Weather-based Water Level
* Real Time and NTP time
* Water Tank
* Humidity Monitor
* Monthly Water Level
* Pressurizer
* Ping monitor
* Temperature Switch
* Pool Heating
* E-mail Reader
* Weather Stations
* Telegram Bot

----

# Logging out
After clicking the "Logging out" button, the user logs out of the system.








