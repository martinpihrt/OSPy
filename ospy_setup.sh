#!/bin/bash
set -Eeuo pipefail

###################################################################################################
# Safe interactive installation of OSPy on Raspberry Pi OS / Debian 12 or newer.
# Download: wget https://raw.githubusercontent.com/martinpihrt/OSPy/master/ospy_setup.sh
# Run:      sudo bash ospy_setup.sh
###################################################################################################

trap 'echo "OSPy installation failed on line ${LINENO}. Review the error above; an existing OSPy checkout was not deleted." >&2' ERR

if [ "$(id -u)" -ne 0 ]; then
  echo "Run this script as root: sudo bash ospy_setup.sh" >&2
  exit 1
fi

for required_command in apt-get getent python3 systemctl; do
  if ! command -v "$required_command" >/dev/null 2>&1; then
    echo "Required command not found: $required_command" >&2
    exit 1
  fi
done

python3 - <<'PY'
import sys
if sys.version_info < (3, 11):
    raise SystemExit("OSPy requires Python 3.11 or newer for this installation procedure.")
if sys.version_info >= (3, 15):
    print("Warning: this Python version is newer than the versions currently tested by OSPy.")
PY

current_user="${SUDO_USER:-}"
if [ -z "$current_user" ] || ! getent passwd "$current_user" >/dev/null 2>&1; then
  current_user="root"
fi
current_user_home="$(getent passwd "$current_user" | cut -d: -f6)"

if ! command -v whiptail >/dev/null 2>&1; then
  echo "===== Installing whiptail for setup menus ====="
  apt-get update
  apt-get install -y whiptail
fi

do_upd_sys=false
do_i2c=false
do_mqtt=false
do_user_grp=false
do_multimedia=false
install_location="/opt"

remote_mode="lan"
remote_url=""
remote_warning=""
remote_note=""
cloudflare_token=""
cloudflare_hostname=""
cloudflare_public_url_file="/etc/ospy/cloudflare_public_url"

normalize_cloudflare_hostname() {
  python3 - "$1" <<'PY_HOSTNAME'
import re
import sys
from urllib.parse import urlsplit

value = sys.argv[1].strip()
if not value:
    raise SystemExit(1)

if "://" in value:
    parsed = urlsplit(value)
    try:
        port = parsed.port
    except ValueError:
        raise SystemExit(1)
    if (parsed.scheme.lower() != "https" or parsed.username or parsed.password or
            port is not None or parsed.query or parsed.fragment or
            parsed.path not in ("", "/")):
        raise SystemExit(1)
    hostname = parsed.hostname or ""
else:
    hostname = value.rstrip(".")
    if any(character in hostname for character in "/?#:@"):
        raise SystemExit(1)

try:
    hostname = hostname.encode("idna").decode("ascii").lower().rstrip(".")
except UnicodeError:
    raise SystemExit(1)

if not 3 <= len(hostname) <= 253 or "." not in hostname:
    raise SystemExit(1)

label_re = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
labels = hostname.split(".")
if any(not label_re.fullmatch(label) for label in labels):
    raise SystemExit(1)

print(hostname)
PY_HOSTNAME
}

if ! CHOICES=$(whiptail --title " OSPy setup " --separate-output --checklist \
  "Choose install options" 13 72 5 \
  "1" "Upgrade installed operating-system packages" ON \
  "2" "Enable I2C and install I2C tools" ON \
  "3" "Install the Mosquitto MQTT broker and client" OFF \
  "4" "Add the invoking user to available hardware groups" ON \
  "5" "Install multimedia packages for voice plug-ins" OFF \
  3>&1 1>&2 2>&3); then
  echo "Installation was cancelled before any OSPy files were changed."
  exit 0
fi

for choice in $CHOICES; do
  case "$choice" in
    "1") do_upd_sys=true ;;
    "2") do_i2c=true ;;
    "3") do_mqtt=true ;;
    "4") do_user_grp=true ;;
    "5") do_multimedia=true ;;
    *) echo "Unsupported setup choice: $choice" >&2; exit 1 ;;
  esac
done

if whiptail --title "Installation location" --yesno \
  "Install OSPy in /opt or in the $current_user home directory?" \
  --no-button "Home directory" --yes-button "/opt" 8 64; then
  install_location="/opt"
else
  if [ -z "$current_user_home" ] || [ ! -d "$current_user_home" ]; then
    echo "Home directory for $current_user was not found." >&2
    exit 1
  fi
  install_location="$current_user_home"
fi

REMOTE_HELP=$(cat <<'EOF'
OSPy always runs locally on port 8080. The remote-access modes below place a secure
reverse proxy/tunnel in front of OSPy. OSPy normally uses local HTTP, but an existing
installation may already be configured for local HTTPS. Cloudflare modes can work with
either local protocol; the installer detects the active OSPy origin after startup.

The tunnel service provides the external HTTPS/TLS connection.

1) LOCAL NETWORK ONLY
   No remote-access software is configured.
   OSPy is reachable only from networks that can directly reach the Raspberry Pi.
   No public HTTPS address is created.

2) CLOUDFLARE TUNNEL
   Recommended when OSPy should have a normal public HTTPS address such as:
       https://ospy.example.com

   Cloudflare provides the public HTTPS endpoint and TLS certificate. cloudflared on
   the Raspberry Pi makes an outbound encrypted tunnel to Cloudflare and forwards
   requests locally to OSPy on 127.0.0.1:8080 using HTTP or HTTPS as detected.

   No public IP address and no router port forwarding are required.
   Requires a Cloudflare account, a domain in Cloudflare DNS, a public hostname and a
   Tunnel token. The installer stores only the public HTTPS URL for the OSPy footer;
   it does not store the Tunnel token in the OSPy project.
   Cloudflare Access can optionally be placed in front of OSPy for another login layer.

3) CLOUDFLARE QUICK TUNNEL
   Test/demo mode. No Cloudflare account and no own domain are required.
   A temporary public HTTPS address under trycloudflare.com is generated automatically.
   The address can change after the service is restarted. Cloudflare documents Quick
   Tunnels as development/testing only, not as a production remote-access method.

4) TAILSCALE SERVE
   Recommended for private administrator access.
   OSPy is exposed over HTTPS only inside your Tailscale network (tailnet).
   Devices/users must be members of the tailnet and permitted by its access rules.
   No public IP address, own domain or router port forwarding is required.
   Requires a Tailscale account and login of this Raspberry Pi into the tailnet.

5) TAILSCALE FUNNEL
   Creates a public HTTPS address under your tailnet's *.ts.net name.
   Visitors do not need Tailscale. OSPy is therefore exposed to the public Internet.
   No own domain or router port forwarding is required.
   Requires Tailscale, MagicDNS/HTTPS and permission to use Funnel in the tailnet.
EOF
)

whiptail --title "OSPy remote access - explanation" --scrolltext \
  --msgbox "$REMOTE_HELP" 22 76

if ! remote_mode=$(whiptail --title "OSPy remote access" --menu \
  "Choose how OSPy should be reachable after installation." \
  18 76 6 \
  "lan"               "Local network only (HTTP :8080)" \
  "cloudflare"        "Cloudflare Tunnel - public, own domain" \
  "cloudflare-quick"  "Cloudflare Quick Tunnel - temporary public URL" \
  "tailscale-serve"   "Tailscale Serve - private tailnet HTTPS" \
  "tailscale-funnel"  "Tailscale Funnel - public *.ts.net HTTPS" \
  3>&1 1>&2 2>&3); then
  echo "Installation was cancelled during remote-access selection."
  exit 0
fi

case "$remote_mode" in
  lan)
    whiptail --title "Local network only" --msgbox \
      "No remote-access service will be installed.

After installation use:
http://<Raspberry-Pi-IP>:8080

This is the safest choice when remote Internet access is not needed." 13 72
    ;;

  cloudflare)
    whiptail --title "Cloudflare Tunnel" --scrolltext --msgbox \
      "Before continuing, create a remotely-managed Cloudflare Tunnel in your Cloudflare account.

Choose the public hostname that will be used for OSPy, for example:
  ospy.example.com

Copy the Tunnel token from the Cloudflare installation command. You can create the Published application route before or after this installer finishes.

After OSPy starts, the installer detects whether the local origin is HTTP or HTTPS and prints the exact origin URL to use in Cloudflare. If HTTPS is detected and OSPy uses a self-signed/local certificate, enable Cloudflare's No TLS Verify setting for that Published application.

The installer stores only the public HTTPS URL for the OSPy footer. The Tunnel token is not written to the OSPy project." 24 76

    while true; do
      if ! cloudflare_hostname_raw=$(whiptail --title "Cloudflare public hostname" --inputbox \
        "Enter the public hostname for OSPy.

Example:
ospy.example.com

You may also paste https://ospy.example.com" \
        14 76 3>&1 1>&2 2>&3); then
        echo "Installation was cancelled while entering the Cloudflare public hostname."
        exit 0
      fi

      if cloudflare_hostname=$(normalize_cloudflare_hostname "$cloudflare_hostname_raw"); then
        break
      fi

      whiptail --title "Cloudflare public hostname" --msgbox \
        "The hostname is not valid. Enter a DNS hostname such as ospy.example.com, without a path, port, query string or wildcard." 11 76
    done

    if systemctl is-active --quiet cloudflared.service; then
      whiptail --title "Cloudflare Tunnel" --msgbox \
        "An active managed cloudflared.service already exists. Its current tunnel credentials will be left unchanged, so a Tunnel token is not required for this run. The public hostname entered above will be stored for the OSPy footer." 12 76
    else
      if ! cloudflare_token=$(whiptail --title "Cloudflare Tunnel token" --passwordbox \
        "Paste the Cloudflare Tunnel token.

Paste only the token, not the complete 'cloudflared service install ...' command." \
        13 76 3>&1 1>&2 2>&3); then
        echo "Installation was cancelled while entering the Cloudflare token."
        exit 0
      fi

      if [ -z "$cloudflare_token" ]; then
        whiptail --title "Cloudflare Tunnel" --msgbox \
          "No tunnel token was entered. The installer will use Local network only instead." 9 74
        remote_mode="lan"
        cloudflare_hostname=""
      fi
    fi
    ;;

  cloudflare-quick)
    whiptail --title "Cloudflare Quick Tunnel" --scrolltext --msgbox \
      "This mode creates a temporary public HTTPS URL such as:
https://random-words.trycloudflare.com

No Cloudflare account or own domain is required.

The installer creates a dedicated systemd service so the tunnel starts automatically. After OSPy starts, it detects whether the local origin on port 8080 uses HTTP or HTTPS. HTTPS origins use --no-tls-verify only for the local cloudflared-to-OSPy connection.

The generated address is not guaranteed to remain the same after a restart. Use this mode only for testing or temporary access." 21 76
    ;;

  tailscale-serve)
    whiptail --title "Tailscale Serve" --scrolltext --msgbox \
      "This mode installs Tailscale and connects the Raspberry Pi to your tailnet.

If the Pi is not already authenticated, 'tailscale up' will print a login URL. Open that URL in a browser and approve the Raspberry Pi.

OSPy will then be reverse-proxied from:
  http://127.0.0.1:8080

to a private HTTPS address under your *.ts.net name.

Only permitted members/devices of your Tailscale network can access it. This is the recommended mode when OSPy remote administration is only for you or your team." 21 76
    ;;

  tailscale-funnel)
    whiptail --title "Tailscale Funnel" --scrolltext --msgbox \
      "This mode installs Tailscale and connects the Raspberry Pi to your tailnet.

If the Pi is not already authenticated, 'tailscale up' will print a login URL. Open it and approve the Raspberry Pi.

Funnel then publishes OSPy to the public Internet using HTTPS under the Raspberry Pi's *.ts.net name. Visitors do not need Tailscale.

Tailscale may require you to enable HTTPS/MagicDNS/Funnel permission in the web consent page. Funnel is public, so use a strong OSPy administrator password." 21 76
    ;;

  *)
    echo "Unsupported remote-access mode: $remote_mode" >&2
    exit 1
    ;;
esac

mkdir -p -- "$install_location"

echo "===== Refreshing the operating-system package index ====="
apt-get update
if [ "$do_upd_sys" = true ]; then
  echo "===== Upgrading installed operating-system packages ====="
  apt-get upgrade -y
fi

echo "===== Installing OSPy core requirements ====="
apt-get install -y \
  ca-certificates \
  git \
  python3 \
  python3-cmarkgfm \
  python3-pil \
  python3-qrcode \
  python3-requests \
  wget

echo "===== Checking Python SQLite support ====="
python3 - <<'PY'
import sqlite3

connection = sqlite3.connect(':memory:')
try:
    result = connection.execute('PRAGMA integrity_check').fetchone()
    if result != ('ok',):
        raise SystemExit('Python SQLite in-memory integrity check failed: {}'.format(result))
    print('Python SQLite support is available: {}'.format(sqlite3.sqlite_version))
finally:
    connection.close()
PY

if [ "$do_i2c" = true ]; then
  echo "===== Installing I2C requirements ====="
  apt-get install -y i2c-tools python3-smbus
  if command -v raspi-config >/dev/null 2>&1; then
    raspi-config nonint do_i2c 0
  else
    echo "raspi-config was not found; enable I2C manually if this is not a Raspberry Pi."
  fi
fi

if [ "$do_mqtt" = true ]; then
  echo "===== Installing MQTT requirements ====="
  apt-get install -y mosquitto python3-paho-mqtt
  systemctl enable mosquitto.service
fi

if [ "$do_multimedia" = true ]; then
  echo "===== Installing optional multimedia packages ====="
  apt-get install -y ffmpeg pulseaudio python3-pygame
fi

if [ "$do_user_grp" = true ]; then
  echo "===== Adding $current_user to available hardware groups ====="
  for group_name in gpio i2c dialout; do
    if getent group "$group_name" >/dev/null 2>&1; then
      usermod -aG "$group_name" "$current_user"
    else
      echo "Group $group_name is not present; skipping it."
    fi
  done
fi

ospy_dir="$install_location/OSPy"
echo "===== Installing OSPy in $ospy_dir ====="
if [ -d "$ospy_dir/.git" ]; then
  if ! git -C "$ospy_dir" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "$ospy_dir is not a valid Git checkout." >&2
    exit 1
  fi
  echo "An existing OSPy checkout was found and left unchanged."
elif [ -e "$ospy_dir" ]; then
  echo "$ospy_dir already exists but is not an OSPy Git checkout." >&2
  exit 1
else
  git clone --branch master --single-branch https://github.com/martinpihrt/OSPy.git "$ospy_dir"
fi

service_template="$ospy_dir/service/ospy.service"
if [ ! -f "$service_template" ]; then
  echo "OSPy service template was not found: $service_template" >&2
  exit 1
fi

echo "===== Installing the OSPy systemd service ====="
python_path="$(command -v python3)"
service_file="$(mktemp)"
cleanup() {
  rm -f -- "$service_file"
}
trap cleanup EXIT

sed \
  -e "s|{{OSPY_DIR}}|$ospy_dir|g" \
  -e "s|{{PYTHON}}|$python_path|g" \
  "$service_template" > "$service_file"

install -m 0644 "$service_file" /etc/systemd/system/ospy.service
systemctl daemon-reload
systemctl enable ospy.service
systemctl restart ospy.service

if ! systemctl is-active --quiet ospy.service; then
  echo "OSPy did not start. Recent service output:" >&2
  journalctl -u ospy.service -n 40 --no-pager >&2 || true
  exit 1
fi

install_cloudflared() {
  echo "===== Installing Cloudflare cloudflared ====="
  apt-get install -y curl
  install -d -m 0755 /usr/share/keyrings
  curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg \
    -o /usr/share/keyrings/cloudflare-main.gpg
  printf '%s\n' \
    'deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared any main' \
    > /etc/apt/sources.list.d/cloudflared.list
  apt-get update
  apt-get install -y cloudflared
}

detect_ospy_origin() {
  if curl -sS --connect-timeout 2 --max-time 4 \
      --output /dev/null http://127.0.0.1:8080/ 2>/dev/null; then
    printf '%s\n' 'http://127.0.0.1:8080'
    return 0
  fi

  if curl -ksS --connect-timeout 2 --max-time 4 \
      --output /dev/null https://127.0.0.1:8080/ 2>/dev/null; then
    printf '%s\n' 'https://127.0.0.1:8080'
    return 0
  fi

  return 1
}

install_tailscale() {
  echo "===== Installing Tailscale ====="
  apt-get install -y curl

  if ! command -v tailscale >/dev/null 2>&1; then
    curl -fsSL https://tailscale.com/install.sh | sh
  else
    echo "Tailscale is already installed."
  fi

  systemctl enable --now tailscaled.service
}

ensure_tailscale_connected() {
  if tailscale status >/dev/null 2>&1; then
    echo "Tailscale is already connected."
    return 0
  fi

  echo
  echo "===== Tailscale authentication required ====="
  echo "Open the login URL printed below in a browser and approve this Raspberry Pi."
  echo
  tailscale up
}

tailscale_https_name() {
  tailscale status --json 2>/dev/null | python3 -c '
import json, sys
try:
    data = json.load(sys.stdin)
    name = data.get("Self", {}).get("DNSName", "").rstrip(".")
    if name:
        print("https://" + name)
except Exception:
    pass
' || true
}

echo "===== Configuring remote access ====="

case "$remote_mode" in
  lan)
    echo "Remote access: Local network only."
    ;;

  cloudflare)
    install_cloudflared
    ospy_origin="$(detect_ospy_origin || true)"
    managed_service_ready=false

    if systemctl is-active --quiet cloudflared.service; then
      echo "An active managed cloudflared.service already exists; leaving its tunnel credentials unchanged."
      managed_service_ready=true
    else
      echo "===== Registering Cloudflare Tunnel as a system service ====="
      if cloudflared service install "$cloudflare_token"; then
        systemctl enable cloudflared.service >/dev/null 2>&1 || true
        systemctl restart cloudflared.service

        if systemctl is-active --quiet cloudflared.service; then
          managed_service_ready=true
        else
          remote_warning="cloudflared was installed but its systemd service is not active. Check: journalctl -u cloudflared -n 50"
        fi
      else
        remote_warning="cloudflared could not register the managed tunnel. An existing inactive cloudflared service may already be installed, or the token may be invalid. Existing Cloudflare configuration was not deleted."
      fi
    fi

    if [ "$managed_service_ready" = true ]; then
      echo "Cloudflare Tunnel service is running."
      remote_url="https://$cloudflare_hostname"
      install -d -m 0755 "$(dirname "$cloudflare_public_url_file")"
      printf '%s\n' "$remote_url" > "$cloudflare_public_url_file"
      chmod 0644 "$cloudflare_public_url_file"

      if [ -n "$ospy_origin" ]; then
        remote_note="Cloudflare Published application origin: $ospy_origin"
        echo "$remote_note"
        if [[ "$ospy_origin" == https://* ]]; then
          remote_note="$remote_note
For a self-signed/local OSPy certificate, enable No TLS Verify in the Cloudflare Published application TLS settings."
          echo "For a self-signed/local OSPy certificate, enable No TLS Verify in the Cloudflare Published application TLS settings."
        fi
      else
        remote_warning="Cloudflare Tunnel is running, but OSPy did not respond on local HTTP or HTTPS port 8080. Check the OSPy service before creating the Published application route."
      fi
    fi
    ;;

  cloudflare-quick)
    install_cloudflared

    if systemctl is-active --quiet cloudflared.service; then
      remote_warning="A managed cloudflared.service is already active. The installer did not start a second Quick Tunnel. Existing Cloudflare configuration was left unchanged."
    else
      cloudflared_path="$(command -v cloudflared)"
      ospy_origin="$(detect_ospy_origin || true)"

      if [ -z "$ospy_origin" ]; then
        remote_warning="Cloudflare Quick Tunnel was not started because OSPy did not respond on http://127.0.0.1:8080 or https://127.0.0.1:8080. Check the OSPy service and port 8080."
      else
        cloudflared_origin_options="--url $ospy_origin"

        if [[ "$ospy_origin" == https://* ]]; then
          cloudflared_origin_options="$cloudflared_origin_options --no-tls-verify"
          echo "Detected OSPy HTTPS origin: $ospy_origin"
          echo "Certificate verification is disabled only for the local cloudflared-to-OSPy connection."
        else
          echo "Detected OSPy HTTP origin: $ospy_origin"
        fi

        cat > /etc/systemd/system/ospy-cloudflared-quick.service <<EOF
[Unit]
Description=OSPy Cloudflare Quick Tunnel
Documentation=https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/
After=network-online.target ospy.service
Wants=network-online.target
Requires=ospy.service

[Service]
Type=simple
ExecStart=$cloudflared_path tunnel --no-autoupdate $cloudflared_origin_options
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOF

        systemctl daemon-reload
        systemctl enable --now ospy-cloudflared-quick.service

        if systemctl is-active --quiet ospy-cloudflared-quick.service; then
          echo "Cloudflare Quick Tunnel is running."
          sleep 3
          remote_url="$(
            journalctl -u ospy-cloudflared-quick.service -n 80 --no-pager 2>/dev/null \
              | grep -Eo 'https://[A-Za-z0-9-]+\.trycloudflare\.com' \
              | tail -n 1 || true
          )"

          if [ -z "$remote_url" ]; then
            remote_url="Run: journalctl -u ospy-cloudflared-quick.service -n 50 --no-pager"
          fi
        else
          remote_warning="Cloudflare Quick Tunnel service did not start. Check: journalctl -u ospy-cloudflared-quick.service -n 50"
        fi
      fi
    fi
    ;;

  tailscale-serve)
    install_tailscale
    ensure_tailscale_connected

    echo "===== Enabling private Tailscale Serve access ====="
    if tailscale serve --bg http://127.0.0.1:8080; then
      remote_url="$(tailscale_https_name)"
      [ -n "$remote_url" ] || remote_url="Run: tailscale serve status"
    else
      remote_warning="Tailscale Serve could not be enabled automatically. Tailscale may have printed a web consent URL. Complete the requested tailnet setup, then run: sudo tailscale serve --bg http://127.0.0.1:8080"
    fi
    ;;

  tailscale-funnel)
    install_tailscale
    ensure_tailscale_connected

    echo "===== Enabling public Tailscale Funnel access ====="
    if tailscale funnel --bg http://127.0.0.1:8080; then
      remote_url="$(tailscale_https_name)"
      [ -n "$remote_url" ] || remote_url="Run: tailscale funnel status"
    else
      remote_warning="Tailscale Funnel could not be enabled automatically. Complete any HTTPS, MagicDNS or Funnel permission requested by Tailscale, then run: sudo tailscale funnel --bg http://127.0.0.1:8080"
    fi
    ;;
esac

echo
echo "===== OSPy is installed and the service is running ====="
echo "Installation directory: $ospy_dir"
echo "Local web interface: http://<Raspberry-Pi-IP>:8080"
echo

case "$remote_mode" in
  lan)
    echo "Remote-access mode: Local network only"
    ;;
  cloudflare)
    echo "Remote-access mode: Cloudflare Tunnel"
    ;;
  cloudflare-quick)
    echo "Remote-access mode: Cloudflare Quick Tunnel"
    ;;
  tailscale-serve)
    echo "Remote-access mode: Tailscale Serve (private)"
    ;;
  tailscale-funnel)
    echo "Remote-access mode: Tailscale Funnel (public)"
    ;;
esac

if [ -n "$remote_url" ]; then
  echo "Remote HTTPS address/status: $remote_url"
fi

if [ -n "$remote_note" ]; then
  echo
  printf '%s\n' "$remote_note"
fi

if [ -n "$remote_warning" ]; then
  echo
  echo "WARNING: $remote_warning"
fi

echo
echo "Open the OSPy web interface and change the generated administrator password immediately."

FINAL_MESSAGE="OSPy is installed and running.

Local access:
http://<Raspberry-Pi-IP>:8080

Remote mode: $remote_mode"

if [ -n "$remote_url" ]; then
  FINAL_MESSAGE="$FINAL_MESSAGE

Remote HTTPS:
$remote_url"
fi

if [ -n "$remote_note" ]; then
  FINAL_MESSAGE="$FINAL_MESSAGE

$remote_note"
fi

if [ -n "$remote_warning" ]; then
  FINAL_MESSAGE="$FINAL_MESSAGE

Warning:
$remote_warning"
fi

FINAL_MESSAGE="$FINAL_MESSAGE

Change the generated OSPy administrator password immediately after the first login."

whiptail --title "OSPy setup finished" --scrolltext --msgbox "$FINAL_MESSAGE" 20 76 || true

if [ "$do_i2c" = true ] || [ "$do_user_grp" = true ]; then
  if whiptail --title "Reboot recommended" --yesno \
    "OSPy is running. A reboot is recommended to apply I2C or hardware-group changes. Reboot now?" \
    --no-button "Later" --yes-button "Reboot" 10 74; then
    reboot
  fi
fi

exit 0
