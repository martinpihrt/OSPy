OSPy Readme
====

An improved Python port of the Arduino based OpenSprinkler firmware.

Because the web interface is based on the original firmware,
the basics described in the [user manual](http://rayshobby.net/opensprinkler/svc-use/svc-web) are still applicable.  
This is my fork from Rimco/OSPy (https://github.com/Rimco/OSPy) with My modifications.  
## More information visit
HW PCB board: https://pihrt.com/elektronika/248-moje-rapsberry-pi-zavlazovani-zahrady

INSTALLATION:
===========

### Preferred option (using Git)
(This option does support automatic updating.)

1. Ensure git is installed (and the git executable is in your path).
2. Use git to clone https://github.com/martinpihrt/OSPy.git to a location of your choice.

### Second option (without Git)
(This option does *not* support automatic updating.)

1. Download a copy of the program from https://github.com/martinpihrt/OSPy/archive/master.zip.
2. Extract the contents to a location of your choice.

## Setup
A setup file has been provided to help you setting up your environment to contain all required packages.
This setup also helps you in case you want to run the program as a service (on Raspbian).

1. Go to the folder where the setup.py file is located (cd OSPy).
2. Execute: sudo apt-get update and follow the procedures
3. Execute: sudo apt-get upgrade and follow the procedures
2. Execute: sudo apt-get install python-setuptools and follow the procedures
2. Execute: python setup.py install
3. Follow the procedures of the script.

## For enable I2C device (LCD plugin and more I2C plugins)  
1. Execute: sudo nano /etc/modules
2. Add in to the file:  
i2c-bcm2708  
i2c-dev  
3. Execute: sudo nano /etc/modprobe.d/raspi-blacklist.conf  
4. Change to:  
#blacklist spi-bcm2708  
#blacklist i2c-bcm2708  
5. Execute: sudo apt-get install python-SMBus  
6. Execute: sudo apt-get install i2c-tools  
7. Reboot OS system: sudo reboot
8. Try find I2C devices: sudo i2cdetect -y 1 (for RPi-1 HW sudo i2cdetect -y 0)
 
## For translate OSPy to other language  
https://github.com/martinpihrt/OSPy/tree/refactor/i18n and step by step, how to use is typed in MD file

## For OSPy Changelog      
https://github.com/martinpihrt/OSPy/blob/refactor/ospy/docs/Changelog.md

## License
OpenSprinkler Py (OSPy) Interval Program

Creative Commons Attribution-ShareAlike 3.0 license

## Acknowledgements
Full credit goes to Dan for his generous contributions in porting the microcontroller firmware to Python.

The program makes use of web.py (http://webpy.org) for the web interface.

The program makes use of gfm (https://github.com/dart-lang/py-gfm) to render the help pages written in GitHub flavored markdown.

The program makes use of pygments (http://pygments.org) to provide syntax highlighting in the help pages.

