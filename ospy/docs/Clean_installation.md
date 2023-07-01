OSPy Clean installation
====
We recommend performing a clean installation with the latest version of Python 3+. The first time you start the OSPy (login page), login data (password) will be generated for logging in to the OSPy system. after logging in, it is necessary to change the login details in the settings (options page). These generated credentials are also stored in the OSPy system as your credentials. The next time you log in, the window with the generated login data will no longer be displayed.

INSTALLATION:
===========

### Operating system Raspbian for Raspberry Pi
1. Install latest operating system: "Raspbian Bullseye or next new version -  with desktop and recommended software" https://www.raspberrypi.org/downloads/raspbian/
2. Change password for acces from "raspberry" to own
3. Enabling in raspi-config SSH, I²C

## Setup
Go to the folder where the setup.py file is located (cd OSPy)

Execute: 
```bash
sudo apt update
```
and follow the procedures

```bash
sudo apt upgrade
```
and follow the procedures 

```bash
sudo pip3 install pycrypto
```
for installation pycrypto if not in the system

```bash
sudo apt install mc
```
for installation midnight commander if not in the system

```bash
git clone -b master https://github.com/martinpihrt/OSPy
```
download OSPy from github

```bash
cd OSPy
```
open a OSPy folder

```bash
sudo python3 setup.py install 
```
installation steps (we confirm yes everywhere) as in the example below

EXAMPLE:
===========
sudo apt update
sudo apt upgrade
sudo pip3 install pycrypto
sudo apt install mc
git clone -b master https://github.com/martinpihrt/OSPy
cd OSPy
sudo python3 setup.py install
i18n.py: The language will be set to: en_US
setup.py: Checking web
setup.py: web is available
setup.py: Checking cmarkgfm
cmarkgfm not available, do you want to install it? [y/yes/n/no]
yes
Do you want to install OSPy as a service? [y/yes/n/no]
yes
setup.py: Done installing service.
Do you want to start OSPy now? [y/yes/n/no]
yes
setup.py: Done.
sudo reboot

IF I CANOT LOG IN:
===========
If you can't log in:
- stop the service "sudo service ospy stop"
- move to the "OSPy/ospy/data" folder, for example via midnight commander, and delete the contents of the "data" folder.
- start the service "sudo service ospy start"
- try to log in on the login page (you will see the generated new login details)

[![](https://github.com/martinpihrt/OSPy/blob/master/ospy/images/generatedlogin.png?raw=true)](https://github.com/martinpihrt/OSPy/blob/master/ospy/images/generatedlogin.png)</br>