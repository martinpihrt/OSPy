OSPy (Open Sprinkler Python) Readme 
====

OSPy is a free Raspberry Pi based Python program for controlling irrigation systems ( sprinkler, drip, etc ).

This is my fork from Rimco/OSPy (https://github.com/Rimco/OSPy) and Dan-in-CA/SIP (https://github.com/Dan-in-CA/SIP) with My modifications.  

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
For using "https" in OSPy options you must follow these procedures. SSL certificate via Let’s Encrypt certification authority.
The Certbot (https://certbot.eff.org/) and Let’s Encrypt (https://letsencrypt.org/) for enabling SSL security.

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

Notice: 
Before starting the certification service, make sure that you have correctly configured your NAT network router (redirecting external port 443 to Raspberry Pi's internal IP address 80 for certification service.) 
After the certificate is generated, it is necessary to route your port to the OSPy port in the router (the default OSPy port is 8080).

The certification service is trying to use a connection using IP version 6. If we do not use IPV6 (we do not have a router set for IPV6, or do not want to use IPV6 for any other reason), we must disable the use of IPV6 addreses in Raspberry Pi!

```bash
sudo nano /etc/modprobe.d/ipv6.conf
```
Add to file
alias net-pf-10 off
options ipv6 disable_ipv6=1
blacklist ipv6

```bash
sudo reboot
```

If "Use Own HTTPS access" is selected in OSPy options, file: fullchain.pem and privkey.pem must You insert to folder ssl in OSPy location. 
For manual generating certificate example:

```bash
cd ssl  
```

```bash
sudo openssl req -new -newkey rsa:4096 -x509 -sha256 -days 3650 -nodes -out fullchain.pem -keyout privkey.pem  
```

Warning: OSPy must be next restarted. 

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


## Communication with other systems
OSPy can be controlled and monitored using HTTP GET commands. With the addition of available plugins OSPy can communicate with other systems via MQTT. 
OSPy can also issue Linux shell commands when a station is turned on or off. This is useful for controlling wireless remote devices and for I2C relay hats and boards.
The Blinker package that is shipped with OSPy sends messages to other Python modules such as plugins to report changes in status. See the signaling examples file in OSPy's plugins folder for examples.

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

