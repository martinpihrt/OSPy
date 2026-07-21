OSPy Clean installation
====
The supported clean-installation path is Raspberry Pi OS or Debian 12 and Python 3.11 or newer. The installer always downloads the stable OSPy `master` branch. When OSPy starts for the first time, the login page displays a generated administrator password. Sign in and change it immediately in Options; the generated-password notice is not displayed again.

USING THE INSTALLATION SCRIPT:
===========
Log into the Pi using SSH. Enter or copy and paste the following commands:
* Remember: Commands on the Raspberry Pi are case sensitive.

```sh
wget https://raw.githubusercontent.com/martinpihrt/OSPy/master/ospy_setup.sh
```
And next
```sh
sudo bash ospy_setup.sh
```

The menu separates core requirements from optional integrations. Operating-system upgrade, I2C and hardware-group setup are selected by default. Mosquitto and multimedia packages for voice plug-ins are optional and disabled by default. Astral and the MySQL connector are already included in the OSPy repository and are not downloaded from separate archives.

Select `/opt` or the invoking user's home directory. A new installation is cloned from the stable `master` branch. If an existing Git checkout is found, the installer never deletes, resets or updates it; it installs the current service around that checkout. A non-Git `OSPy` path stops installation and must be inspected manually.

The installer creates a native systemd service from the versioned `service/ospy.service` template, reloads systemd, enables and starts OSPy, then verifies that the service is active. If startup fails, recent service output is printed and installation returns an error. A reboot is only recommended for I2C or hardware-group changes. Choosing to reboot later is a successful installation, not an error.

After installation, open `http://<Raspberry-Pi-address>:8080`. Review the generated administrator password, change it immediately and make an OSPy backup after the initial configuration.


OLDER MANUAL INSTALLATION:
===========

### Operating system Raspbian for Raspberry Pi
1. Install a supported Raspberry Pi OS or Debian 12 image: https://www.raspberrypi.com/software/operating-systems/
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
Do not delete `ospy/data`; that would remove configuration and history. Use the local recovery script instead:

```bash
cd /path/to/OSPy
sudo systemctl stop ospy.service
sudo python3 back_door.py
sudo systemctl start ospy.service
```

Run it only from the Raspberry Pi console or another trusted local shell and confirm by typing `RESET`. The script resets the administrator name to `admin`, disables passwordless access and two-factor authentication, removes the TOTP secret and backup codes, revokes remembered browser logins and active web sessions, and generates a one-time recovery password. Irrigation settings, programs, plug-ins and logs remain intact. Change the recovery password immediately after signing in.


MANUAL OSPY UPDATE
===========
Using Git, without system update plugin if plugin not work. Go to the folder where the run.py file is located (cd OSPy)

Create an OSPy backup first. Stop the service, verify that the checkout has no local changes, and accept only a fast-forward update:

```bash
sudo systemctl stop ospy.service
sudo git status --short
sudo git pull --ff-only
sudo systemctl start ospy.service
```

If `git status --short` prints files, do not discard them automatically. Review or back up the changes before updating. The System Update plug-in remains the preferred update path because it creates a verified safety backup and uses the external rollback watchdog.

### Second option (without Git)
(This option does *not* support automatic updating.)

1. Download a copy of the program from [Github](https://github.com/martinpihrt/OSPy/archive/master.zip)
2. Extract the contents to a location of your choice


HTTPS
===========

## For enable SSL access in options (for HTTPS connections)
For using "https" in OSPy options you must follow these procedures. SSL certificate via Let’s Encrypt certification authority.
The [Certbot](https://certbot.eff.org/) and [Let’s Encrypt](https://letsencrypt.org/) for enabling SSL security.

The server-side HTTPS selection is now explicit: the own certificate has priority, otherwise Let’s Encrypt is used; enabling both options no longer causes a silent HTTP fallback.

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
