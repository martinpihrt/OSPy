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

if ! CHOICES=$(whiptail --title " OSPy setup " --separate-output --checklist \
  "Choose install options" 13 64 5 \
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

if whiptail --title "Location" --yesno \
  "Install OSPy in /opt or in the $current_user home directory?" \
  --no-button "Home directory" --yes-button "/opt" 8 60; then
  install_location="/opt"
else
  if [ -z "$current_user_home" ] || [ ! -d "$current_user_home" ]; then
    echo "Home directory for $current_user was not found." >&2
    exit 1
  fi
  install_location="$current_user_home"
fi

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

echo "===== Installing the systemd service ====="
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

echo "===== OSPy is installed and the service is running ====="
echo "Installation directory: $ospy_dir"
echo "Open the OSPy web interface on port 8080 and change the generated administrator password."

if [ "$do_i2c" = true ] || [ "$do_user_grp" = true ]; then
  if whiptail --title "Setup finished" --yesno \
    "OSPy is running. A reboot is recommended to apply I2C or group changes. Reboot now?" \
    --no-button "Later" --yes-button "Reboot" 10 70; then
    reboot
  fi
fi

exit 0
