OSPy (Open Sprinkler Python) Readme 
====

OSPy - Open Sprinkler Python An improved Python port of the Arduino based OpenSprinkler firmware.

This is my fork from Rimco/OSPy (https://github.com/Rimco/OSPy) with My modifications.  

## More information visit
Martin Pihrt - pihrt.com: https://pihrt.com/elektronika/248-moje-rapsberry-pi-zavlazovani-zahrady

## Hardware
<a href="blockconnection.png"><img src="blockconnection.png" width="100%"></a>

INSTALLATION:
===========

### Operating system (Debian >= 9) for Raspberry Pi
1. Install latest operating system: "Raspbian Buster or next new version -  with desktop and recommended software" https://www.raspberrypi.org/downloads/raspbian/
2. Change password for acces from "raspberry" to own
3. Enabling in raspi-config SSH, I2C
4. Install OSPy using Git

## Setup
A setup file has been provided to help you setting up your environment to contain all required packages.
This setup also helps you in case you want to run the program as a service (on Raspbian).

Go to the folder where the setup.py file is located (cd OSPy)

Execute: 
```bash
sudo apt-get update
```
and follow the procedures

```bash
sudo apt-get upgrade
```
and follow the procedures

```bash
sudo python setup.py install 
```
and follow the procedures of the script


### Preferred option (using Git)
(This option does support automatic updating.)

Ensure git is installed (and the git executable is in your path)
Use git to clone:

```bash
git clone -b master https://github.com/martinpihrt/OSPy
```
Next use step "Setup"

### Manual OSPy-system update (using Git, without system update plugin if plugin not work)
Go to the folder where the run.py file is located (cd OSPy)

Execute:
```bash
sudo git config core.filemode false
```
```bash
sudo git reset --hard
```
```bash
sudo git pull
```

### Second option (without Git)
(This option does *not* support automatic updating.)

1. Download a copy of the program from https://github.com/martinpihrt/OSPy/archive/master.zip
2. Extract the contents to a location of your choice

## For enable SSL access in options (for HTTPS connections)
If "https" is selected in OSPy settings, server.crt and sever.key files are created automatically. Warning: OSPy must be next restarted. 

## For enable I2C device (I2C LCD plugin and more I2C plugins)  

Execute:
```bash
sudo raspi-config
```
and follow enabling I2C bus
```bash
sudo reboot
```
and reboot OS system
 
## For translate OSPy to other language
The OSPy system is currently in three languages: English, Czech, Slovak. For other languages: https://github.com/martinpihrt/OSPy/tree/master/i18n and step by step, how to use is typed in MD file
Any user who joins the "OSPy" project is welcome! Translation of strings into other languages is not demanding (using the https://poedit.net/)

## For OSPy and plugins (ospy-plugins) Changelog      
https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Changelog.md

## For OSPy and plugins Issues
https://github.com/martinpihrt/OSPy/issues

## Help with to user web Interfaces
* Czech
https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Web%20Interface%20Guide%20-%20Czech.md
* English
https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Web%20Interface%20Guide%20-%20English.md

## License
OpenSprinkler Py (OSPy) Interval Program

Creative Commons Attribution-ShareAlike 3.0 license

## Acknowledgements
Full credit goes to Dan for his generous contributions in porting the microcontroller firmware to Python.

The program makes use of web.py (http://webpy.org) for the web interface.

The program makes use of gfm (https://github.com/dart-lang/py-gfm) to render the help pages written in GitHub flavored markdown.

The program makes use of pygments (http://pygments.org) to provide syntax highlighting in the help pages.

The program makes use of OpenStreetMap (https://www.openstreetmap.org) to convert locations into coordinates.

The program makes use of Dark Sky API ([Powered by Dark Sky](https://darksky.net/poweredby/)) for weather information.

