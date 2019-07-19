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
            Use HTTPS access 
            Select Language          
        Weather Section
            Use Weather
            Dark Sky API key
            Location
            Elevation
        Security Section
            Disable security
            Current password
            New password
            Confirm password           
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
        Activate Master
        Activate Master Two
        Notes  
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
            Water Tank and Humidity Monitor
            Monthly Water Level
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
The External IP address for OSPy system. Connected your network to provider. Tested via bot.whatismyipaddress.com.

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
  
## Manage
  
## Install New Plugin
  
### Custom plug-in (ZIP)

### Github (https://github.com/martinpihrt/OSPy-plugins/archive/master.zip)  

## Disable All
   
## Enable All 
  
## Enable check updates
  
## Automatic updates

----

# Log page
    
## Download log as
   
## Clear Log

## Clear Log Email

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

### Use HTTPS access 
In case we have configured OSPy server for higher security of data transmission by SSL certificate, check "Use HTTPS access". If the "Use HTTPS access" option is checked and the server is not set up correctly, OSPy will start as http.

### Select Language  
The language option can change the language used in the web interface.

* Click the downward arrow at the right of the language field to display a list of available languages.
* Click the language you wish to use in the interface.
* Click the Submit Changes button at the bottom of the page.

The software will restart and after a few seconds the interface will appear in the language selected.
        
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

## Security Section
For improved security it is recommended that you change the system password from the default opendoor. You can also disable the password requirement if desired.

* Click the triangle at the left of the bar labled Change password to expand the section.
* Leave the Disable security box unchecked unless you have a very good reason to disable password protection.
* Enter the current password in the first text box This will be opendoor on a new installation.
* Enter your new password into the the boxes labeled New password and Confirm password.
* Click the Submit Changes button at the bottom of the page.

You will return to the home page. Your new password will be required the next time you log in.

### Disable security
Leave the Disable security box unchecked unless you have a very good reason to disable password protection.

### Current password
Enter the current password in the first text box This will be opendoor on a new installation.

### New password
Enter your new password into the the boxes labeled New password.

### Confirm password           
Enter your Confirm into the the boxes labeled Confirm password.

## Station Handling Section

### Maximum usage

#### About Sequential and Concurrent modes

### Number of outputs

### Station delay
Enter the number of seconds to delay between station operations.

### Minimum runtime

## Configure Master Section

### Master station
### Master two station
### Activate relay
### Master on delay
### Master off delay
### Master two on delay
### Master two off delay 

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
The Download button is used to download the configuration file to your computer for later use or to restore the OSPy system. The downloaded filename is "options.db". Not change this name!

### Upload 
The Upload button allows you to insert and restore OSPy system (for example, when you reinstall a Linux system). The uploaded file must be filename "options.db"!

----

# Stations page
## Station 
## Name
## Usage
## Precipitation
## Capacity
## ETo factor
## Balance adjustment
## Connected
## Ignore Rain
## Activate Master
## Activate Master Two
## Notes  

----

# Help page
## OSPy
### Readme
### Changelog
### Programs
### Web Interface Guide - Czech
### Web Interface Guide - English

## API
### Readme
### Details

## Plug-ins
Readme
The basic structure is as follows:
plugins
+ plugin_name
  + data
  + docs
  + static
  + templates
  + i18n
  + __init__.py
  \ README.md

The static files will be made accessible automatically at the following location: /plugins/plugin_name/static/...
All *.md files in the docs directory will be visible in the help page. 

Available plug-ins:

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
* Email Notifications
* Remote FTP Control
* System Update
* Water Meter
* Webcam Monitor
* Weather-based Water Level Netatmo
* Direct 16 Relay Outputs
* MQTT Zone Broadcaster
* System Debug Information
* Weather-based Water Level
* Real Time and NTP time
* Water Tank and Humidity Monitor
* Monthly Water Level

----

# Logging out








