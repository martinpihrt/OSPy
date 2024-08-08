OSPy Clean installation
====
We recommend performing a clean installation with the latest version of Python 3+. The first time you start the OSPy (login page), login data (password) will be generated for logging in to the OSPy system. after logging in, it is necessary to change the login details in the settings (options page). These generated credentials are also stored in the OSPy system as your credentials. The next time you log in, the window with the generated login data will no longer be displayed.

USING THE INSTALLATION SCRIPT:
===========
Log into the Pi using SSH or Wifi. Enter or copy-paste the following command:
* Remember: Commands on the Raspberry Pi are case sensitive.

```sh
curl -sSL https://raw.githubusercontent.com/martinpihrt/OSPy/master/ospy_setup.sh
```
And next
```sh
sudo bash ospy_setup.sh
```

The OSPy setup menu will appear
Optional: Use the arrow keys to move between options. Tap the space bar to select or de-select an option.
In most cases the default options are recommended..
Tap the Tab key to move to <ok>.
Tap the Enter key then use the arrow keys to choose the location where OSPy will be installed.
Tap the Enter key again to install OSPy.
Depending on the options selected, the install process may take a few minutes to complete.
A dialog box will appear when OSPy is installed.
Tap the Enter key to reboot the Pi.
After the Pi has rebooted OSPy will be up and running, ready to be connected to your OSPy sprinkler system and programmed with your irrigation schedules. See Opening the OSPy web interface to get started.


OLDER MANUAL INSTALLATION:
===========

### Operating system Raspbian for Raspberry Pi
1. Install latest operating system: "Raspbian Bullseye or next new version -  with desktop and recommended software" https://www.raspberrypi.org/downloads/raspbian/
2. Change password for acces from "raspberry" to own
3. Enabling in raspi-config SSH, I²C
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
sudo python3 setup.py install 
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


IF I CANOT LOG IN:
===========
If you can't log in:
- stop the service "sudo service ospy stop"
- move to the "OSPy/ospy/data" folder, for example via midnight commander, and delete the contents of the "data" folder.
- start the service "sudo service ospy start"
- try to log in on the login page (you will see the generated new login details)

[![](https://github.com/martinpihrt/OSPy/blob/master/ospy/images/generatedlogin.png?raw=true)](https://github.com/martinpihrt/OSPy/blob/master/ospy/images/generatedlogin.png)</br>



MANUAL OSPY UPDATE
===========
Using Git, without system update plugin if plugin not work. Go to the folder where the run.py file is located (cd OSPy)

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

1. Download a copy of the program from [Github](https://github.com/martinpihrt/OSPy/archive/master.zip)
2. Extract the contents to a location of your choice


HTTPS
===========

## For enable SSL access in options (for HTTPS connections)
For using "https" in OSPy options you must follow these procedures. SSL certificate via Let’s Encrypt certification authority.
The [Certbot](https://certbot.eff.org/) and [Let’s Encrypt](https://letsencrypt.org/) for enabling SSL security.

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
Before starting the certification service, make sure that you have correctly configured your NAT network router (redirecting external port 443 to Raspberry Pi's internal IP address 80 for certification service.) After the certificate is generated, it is necessary to route your port to the OSPy port in the router (the default OSPy port is 8080). The certification service is trying to use a connection using IP version 6. If we do not use IPV6 (we do not have a router set for IPV6, or do not want to use IPV6 for any other reason), we must disable the use of IPV6 addreses in Raspberry Pi!

```bash
sudo nano /etc/modprobe.d/ipv6.conf
```
Add to file.
```bash
alias net-pf-10 off
options ipv6 disable_ipv6=1
blacklist ipv6
```
And next restart.
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

## For enable I²C device (I²C LCD plugin and more I²C plugins)  

Execute:
```bash
sudo raspi-config
```
and follow enabling I²C bus
```bash
sudo reboot
```
and reboot OS system