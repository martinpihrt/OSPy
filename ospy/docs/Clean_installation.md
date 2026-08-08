OSPy Clean installation
====

The supported clean-installation path is Raspberry Pi OS or Debian 12 and Python 3.11 or newer. The installer always downloads the stable OSPy `master` branch. When OSPy starts for the first time, the login page displays a generated administrator password. Sign in and change it immediately in Options; the generated-password notice is not displayed again.

USING THE INSTALLATION SCRIPT
===========

Log into the Raspberry Pi using SSH. Commands on Linux are case sensitive.

Download the installer:

```sh
wget https://raw.githubusercontent.com/martinpihrt/OSPy/master/ospy_setup.sh
```

Run it as root:

```sh
sudo bash ospy_setup.sh
```

The installer is interactive and uses `whiptail`. It first asks which optional operating-system components should be installed, then asks for the OSPy installation directory, and finally asks how OSPy should be reachable over the network.

INSTALLER OPTIONS
===========

## Main installation options

### 1. Upgrade installed operating-system packages

Default: **ON**

Runs:

```sh
sudo apt-get upgrade -y
```

after refreshing the package index. Disable this option if operating-system package upgrades are managed separately.

### 2. Enable I2C and install I2C tools

Default: **ON**

Installs `i2c-tools` and `python3-smbus`. On Raspberry Pi OS, the installer also uses `raspi-config` to enable I2C.

This option is useful for the I2C LCD plug-in and other OSPy plug-ins that use the Raspberry Pi I2C bus.

A reboot is recommended after installation if I2C was enabled.

### 3. Install the Mosquitto MQTT broker and client

Default: **OFF**

Installs the Mosquitto broker and Python MQTT support and enables `mosquitto.service`.

Enable this only if OSPy or one of its plug-ins will use a local MQTT broker.

### 4. Add the invoking user to available hardware groups

Default: **ON**

Adds the user who invoked `sudo` to available groups:

```text
gpio
i2c
dialout
```

Missing groups are skipped safely.

A reboot or a new login session is recommended before the changed group membership is used.

### 5. Install multimedia packages for voice plug-ins

Default: **OFF**

Installs:

```text
ffmpeg
pulseaudio
python3-pygame
```

Enable this only when plug-ins requiring audio/multimedia support are used.

INSTALLATION LOCATION
===========

The installer offers two locations:

```text
/opt/OSPy
```

or:

```text
<invoking-user-home>/OSPy
```

A new installation is cloned from the stable `master` branch.

If an existing Git checkout is found, the installer never deletes, resets or automatically updates it; it installs the service around that checkout. A non-Git `OSPy` path stops the installation and must be inspected manually.

REMOTE ACCESS OPTIONS
===========

OSPy normally serves its web interface on port `8080`.

Regardless of the selected tunnel mode, local LAN access remains:

```text
http://<Raspberry-Pi-address>:8080
```

Cloudflare Tunnel, Tailscale Serve and Tailscale Funnel act as reverse proxies in front of this local HTTP service. In those modes OSPy normally **does not need its own HTTPS certificate**. The external service provides HTTPS/TLS and forwards requests to:

```text
http://127.0.0.1:8080
```

No router port forwarding is required for any of the tunnel modes below.

## 1. Local network only

Recommended when OSPy does not need remote Internet access.

No Cloudflare or Tailscale software is configured.

Access OSPy directly from the local network:

```text
http://192.168.x.x:8080
```

Advantages:

- simplest configuration;
- no external account;
- no public OSPy endpoint;
- no tunnel dependency.

This mode does not automatically add HTTPS.

## 2. Cloudflare Tunnel

Recommended when OSPy should be reachable through a normal public hostname such as:

```text
https://ospi.example.com
```

Architecture:

```text
Web browser
    |
    | HTTPS - public TLS certificate
    v
Cloudflare
    |
    | encrypted Cloudflare Tunnel
    v
cloudflared on Raspberry Pi
    |
    | local HTTP
    v
http://127.0.0.1:8080
    |
    v
OSPy
```

Cloudflare manages the public HTTPS connection and certificate. OSPy remains on local HTTP.

A public IPv4 address, DDNS and router port forwarding are not required.

### Requirements

Before running the OSPy installer with this option:

1. Have a Cloudflare account.
2. Have a domain using Cloudflare DNS.
3. Create a remotely-managed Cloudflare Tunnel in the Cloudflare dashboard.
4. Add a Public Hostname, for example:

```text
ospi.example.com
```

5. Set the origin/service to:

```text
HTTP
http://localhost:8080
```

6. Copy the Tunnel token from the Cloudflare installation command.

The OSPy installer asks only for the token. Paste the token itself, not the complete command.

The installer then:

- installs `cloudflared` from Cloudflare's official Debian package repository;
- registers the tunnel as `cloudflared.service`;
- enables the service at boot;
- starts the tunnel.

Cloudflare documentation:

- https://developers.cloudflare.com/tunnel/setup/
- https://developers.cloudflare.com/tunnel/downloads/

### Security

Cloudflare Tunnel makes the selected hostname publicly reachable unless access is restricted separately.

For an Internet-facing OSPy installation, consider using Cloudflare Access in front of OSPy. This can provide an additional authentication layer before the OSPy login page is reached.

Always change the generated OSPy administrator password immediately after first login.

## 3. Cloudflare Quick Tunnel

This option is intended for testing and temporary access.

No Cloudflare account and no own domain are required.

The installer starts:

```sh
cloudflared tunnel --url http://127.0.0.1:8080
```

as a dedicated systemd service:

```text
ospy-cloudflared-quick.service
```

Cloudflare generates a temporary address similar to:

```text
https://random-words.trycloudflare.com
```

The address can be shown with:

```sh
sudo journalctl -u ospy-cloudflared-quick.service -n 50 --no-pager
```

While `ospy-cloudflared-quick.service` is installed and active and a valid `https://*.trycloudflare.com` address is present in its journal, OSPy also shows the current Quick Tunnel address as a clickable **Cloudflare Quick Tunnel** link in the footer. If the service is missing, inactive, unreadable or no valid Quick Tunnel address is available, the footer does not show the link.

Cloudflare documents Quick Tunnels as a development/testing feature, not as a production hosting method. The generated hostname can change when the tunnel is recreated or restarted.

Cloudflare documentation:

- https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/

## 4. Tailscale Serve

Recommended for **private OSPy administration**.

Tailscale Serve exposes OSPy over HTTPS only inside the user's Tailscale network, called a tailnet.

Architecture:

```text
Your phone / PC
     |
     | Tailscale encrypted network
     v
https://raspberry-pi.<tailnet>.ts.net
     |
     v
Tailscale Serve
     |
     | local HTTP
     v
http://127.0.0.1:8080
     |
     v
OSPy
```

Users and devices must be allowed into the tailnet. Tailnet access-control rules also apply to Serve.

No own Internet domain, public IP address or router port forwarding is required.

The installer:

1. installs Tailscale using the official Tailscale Linux installer;
2. enables `tailscaled.service`;
3. runs `tailscale up` if the Raspberry Pi is not already authenticated;
4. runs:

```sh
sudo tailscale serve --bg http://127.0.0.1:8080
```

The `--bg` configuration persists across normal reboots.

If authentication is needed, Tailscale prints a login URL. Open the URL in a browser and approve the Raspberry Pi.

Check the Serve configuration with:

```sh
tailscale serve status
```

Tailscale documentation:

- https://tailscale.com/docs/install/linux
- https://tailscale.com/docs/features/tailscale-serve
- https://tailscale.com/docs/reference/tailscale-cli/serve

## 5. Tailscale Funnel

Tailscale Funnel is similar to Serve, but the resulting HTTPS service is reachable from the **public Internet**. Visitors do not need a Tailscale client.

The public address uses the tailnet's `*.ts.net` DNS name.

The installer:

1. installs and authenticates Tailscale;
2. runs:

```sh
sudo tailscale funnel --bg http://127.0.0.1:8080
```

Tailscale may display a web consent URL if HTTPS, MagicDNS or Funnel permissions still need to be enabled for the tailnet.

Check the Funnel configuration with:

```sh
tailscale funnel status
```

Tailscale Funnel currently requires the Tailscale HTTPS/MagicDNS configuration and appropriate Funnel permission. Funnel is public, so the OSPy login page is exposed to the Internet.

Tailscale documentation:

- https://tailscale.com/docs/features/tailscale-funnel
- https://tailscale.com/docs/reference/tailscale-cli/funnel

WHICH REMOTE MODE SHOULD I CHOOSE?
===========

| Requirement | Recommended mode |
|---|---|
| OSPy only on the local LAN | **Local network only** |
| Private remote access only for administrators | **Tailscale Serve** |
| Public OSPy with my own domain | **Cloudflare Tunnel** |
| Temporary public test without a domain | **Cloudflare Quick Tunnel** |
| Public access without my own domain using `*.ts.net` | **Tailscale Funnel** |

For most permanent installations:

- use **Tailscale Serve** when only trusted administrators need remote access;
- use **Cloudflare Tunnel** when OSPy needs a normal public hostname.


COST AND DOMAIN REQUIREMENTS
===========

The tunnel software used by these installer options does not require buying a separate TLS certificate.

At the time this documentation was updated:

- Cloudflare Tunnel is available with Cloudflare's free offering for this type of self-hosted access. A custom public hostname requires a domain placed in Cloudflare DNS; domain registration itself may have an annual cost.
- Cloudflare Quick Tunnel does not require an account or domain, but is only intended for testing/development.
- Tailscale Serve and Tailscale Funnel are available on Tailscale plans that support these features; Serve/Funnel use the tailnet's `*.ts.net` naming rather than requiring your own domain.

Provider plans and limits can change. Check the current Cloudflare or Tailscale documentation before relying on a particular commercial limit.

OSPY HTTPS AND TUNNEL HTTPS
===========

There are two different HTTPS designs.

## Recommended with Cloudflare/Tailscale

Keep OSPy itself on HTTP:

```text
http://127.0.0.1:8080
```

The browser sees HTTPS because Cloudflare or Tailscale terminates TLS:

```text
Browser --HTTPS--> Cloudflare/Tailscale --local HTTP--> OSPy
```

Do **not** enable OSPy's own HTTPS only because a tunnel is being used. The tunnel already provides the external TLS layer.

## Direct OSPy HTTPS without a tunnel

The older configuration is still possible. OSPy can use its own certificate and be exposed directly through the network/router.

For Let's Encrypt, install Certbot:

```bash
sudo apt-get install certbot
```

Check it:

```bash
certbot --version
```

Request a certificate:

```bash
sudo certbot certonly --standalone -d your_domain_name
```

Renew it:

```bash
sudo certbot renew
```

Copy the certificate and private key into the `ssl` directory of the installed OSPy checkout, for example:

```bash
sudo cp /etc/letsencrypt/live/your.domain.com/fullchain.pem /opt/OSPy/ssl/
sudo cp /etc/letsencrypt/live/your.domain.com/privkey.pem /opt/OSPy/ssl/
sudo systemctl restart ospy.service
```

If OSPy is installed in the user's home directory, use that OSPy path instead of `/opt/OSPy`.

The server-side HTTPS selection is explicit: the own certificate has priority, otherwise Let's Encrypt is used. Enabling both options does not cause a silent HTTP fallback.

Direct Internet exposure normally requires correct DNS and router/firewall/NAT configuration. It is not required when Cloudflare Tunnel, Tailscale Serve or Tailscale Funnel is used.

For a manually generated self-signed certificate:

```bash
cd /path/to/OSPy/ssl
sudo openssl req -new -newkey rsa:4096 -x509 -sha256 -days 3650 -nodes \
  -out fullchain.pem -keyout privkey.pem
sudo systemctl restart ospy.service
```

A self-signed certificate is not automatically trusted by browsers.

SYSTEMD SERVICE
===========

The installer creates a native systemd service from the versioned:

```text
service/ospy.service
```

template, reloads systemd, enables and starts OSPy, then verifies that the service is active.

If OSPy startup fails, recent service output is printed and the installation returns an error.

Useful commands:

```bash
sudo systemctl status ospy.service
sudo systemctl restart ospy.service
sudo journalctl -u ospy.service -n 50 --no-pager
```

A reboot is only recommended for I2C or hardware-group changes. Choosing to reboot later is still a successful installation.

SQLITE CHECK AND SETTINGS SHADOW COPY
===========

The installer verifies Python's built-in SQLite support with a temporary in-memory database and an integrity check.

No SQLite server, command-line program, API key or separate Python package is installed.

OSPy settings continue to use the existing shelve/DBM files. The SQLite test only confirms that the platform is ready for the separately controlled settings migration.

After a successful settings save, OSPy also creates a verified `options.sqlite3` shadow copy beside the active shelve/DBM files. The shadow is written through a temporary file and atomically replaced only after its schema, keys, values and SQLite integrity check pass.

OSPy does not read settings from this shadow file during startup. If shadow synchronization fails, the shelve/DBM save remains valid and Diagnostics reports the failure without switching the active backend.

FIRST LOGIN
===========

After installation, local access is:

```text
http://<Raspberry-Pi-address>:8080
```

If a tunnel mode was selected, the installer also prints the remote address or a command that shows its status.

On the first login:

1. review the generated administrator password;
2. sign in;
3. change the administrator password immediately;
4. make an OSPy backup after the initial configuration.

IF I CANNOT LOG IN
===========

Do not delete `ospy/data`; that would remove configuration and history.

Use the local recovery script:

```bash
cd /path/to/OSPy
sudo systemctl stop ospy.service
sudo python3 back_door.py
sudo systemctl start ospy.service
```

Run it only from the Raspberry Pi console or another trusted local shell and confirm by typing `RESET`.

The script resets the administrator name to `admin`, disables passwordless access and two-factor authentication, removes the TOTP secret and backup codes, revokes remembered browser logins and active web sessions, and generates a one-time recovery password.

Irrigation settings, programs, plug-ins and logs remain intact. Change the recovery password immediately after signing in.

MANUAL OSPY UPDATE
===========

Using Git, without the System Update plug-in, go to the OSPy directory containing `run.py`.

Create an OSPy backup first. Stop the service, verify that the checkout has no local changes, and accept only a fast-forward update:

```bash
sudo systemctl stop ospy.service
sudo git status --short
sudo git pull --ff-only
sudo systemctl start ospy.service
```

If `git status --short` prints files, do not discard them automatically. Review or back up the changes before updating.

The System Update plug-in remains the preferred update path because it creates a verified safety backup and uses the external rollback watchdog.

OLDER MANUAL INSTALLATION
===========

### Operating system for Raspberry Pi

1. Install a supported Raspberry Pi OS or Debian 12 image:
   https://www.raspberrypi.com/software/operating-systems/
2. Configure a secure account/password.
3. Enable SSH and I2C in `raspi-config` if required.
4. Install OSPy using Git.


### Manual setup using the historical `setup.py`

A setup file is also available for the older manual installation path.

Go to the directory containing `setup.py`:

```bash
cd /path/to/OSPy
```

Refresh packages:

```bash
sudo apt-get update
```

Optionally upgrade the operating system:

```bash
sudo apt-get upgrade
```

Run the historical setup procedure:

```bash
sudo python3 setup.py install
```

Follow the prompts shown by the script.

### Preferred option using Git

This option supports automatic updating.

Ensure Git is installed and clone the stable branch:

```bash
git clone -b master https://github.com/martinpihrt/OSPy
```

Then follow the manual setup procedure used by the project.

### Without Git

This option does not support automatic updating.

Download:

https://github.com/martinpihrt/OSPy/archive/master.zip

and extract it to the chosen installation directory.

MANUAL I2C ENABLE
===========

If I2C was not enabled by the installer:

```bash
sudo raspi-config
```

Enable the I2C interface and reboot:

```bash
sudo reboot
```
