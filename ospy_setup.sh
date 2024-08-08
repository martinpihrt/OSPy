
#! /bin/bash
###
# script: easy install OSPy and requirements on a fresh Debian version: 12 (bookworm) Pi image
# by: Gerard ported to ospy Martin Pihrt
# version: 0.96
# usage:  curl -sSL https://github.com/martinpihrt/OSPy/ospy_setup/-/raw/main/ospy_setup.sh | sudo bash
###


if [[ $(id -u) -gt 0 ]]
then
    echo "Run this command as root or sudo otherwise this script might fail"
    exit
fi

current_user=${SUDO_USER:-$USER}

do_upd_sys=false
do_i2c=false
do_mqtt=false
do_user_grp=false
do_log2ram=false
install_location="/opt"

CHOICES=$(whiptail --title " OSPy setup " --separate-output --checklist  "Choose install options" 12 45 5 \
 "1" "Update system (recommended)" ON \
 "2" "Enable i2c" ON \
 "3" "Install MQTT broker" OFF \
 "4" "Adjust user permissions" ON \
 "5" "Install log2ram" ON 3>&1 1>&2 2>&3)

if [ -z "$CHOICES" ]; then
  echo "No option was selected or cancelled. Stopping script."
  exit 1
else
  for CHOICE in $CHOICES; do
    case "$CHOICE" in
    "1")
      do_upd_sys=true
      ;;
    "2")
      do_i2c=true
      ;;
    "3")
      do_mqtt=true
      ;;
    "4")
      do_user_grp=true
      ;;
    "5")
      do_log2ram=true
      ;;
    *)
      echo "Unsupported item $CHOICE!" >&2
      exit 1
      ;;
    esac
  done
fi

if (whiptail --title "Location" --yesno "Install OSPy in /opt or the $current_user homedir?" --no-button "homedir" --yes-button "opt" 8 45); then
    echo "installing in /opt"
    mkdir -p /opt
    install_location="/opt"
else
    echo "installing in homedir"
    install_location="/home/$current_user"
fi


if [ "$do_upd_sys" = true ]; then
  echo ===== Updating system =====
  sudo apt update && sudo apt upgrade -y
fi

echo ===== Installing git =====
sudo apt install git -y

if [ "$do_i2c" = true ]; then
  echo ===== Installing  i2c requirements =====
  sudo apt install -y python3-smbus i2c-tools -y
  echo ===== Enabling  i2c interface =====
  sudo raspi-config nonint do_i2c 0
fi

if [ "$do_mqtt" = true ]; then
  echo ===== Installing  mqtt broker and paho client =====
  sudo apt install mosquitto -y
  sudo apt install python3-paho-mqtt -y
fi

if [ "$do_user_grp" = true ]; then
  echo ===== adding user ${current_user} to hardware groups  =====
  sudo usermod -aG gpio ${current_user}
  sudo usermod -aG i2c ${current_user}
  sudo usermod -aG dialout ${current_user}
fi


echo ===== Installing cmarkgfm for OSPy core =====
sudo apt install python3-cmarkgfm -y


echo ===== Installing requests for OSPy core =====
sudo apt install python3-requests -y


echo ===== Installing packages for plugins pillow qrcode pygame =====
sudo apt install python3-pillow -y
sudo apt install python3-qrcode -y
sudo apt install python3-pygame -y


echo ===== Installing OSPy =====
cd $install_location
sudo git clone https://github.com/martinpihrt/OSPy


echo ===== Installing webpy =====
# from pipi.org
cd $install_location
sudo wget https://files.pythonhosted.org/packages/cd/6e/338a060bb5b52ee8229bdada422eaa5f71b13f8d33467f37f870ed2cae4b/web.py-0.62.tar.gz -O webpy.tar.gz
sudo tar xf webpy.tar.gz
sudo cp -r web.py-0.62/web OSPy


echo ===== Installing cheroot =====
# from pipi.org
cd $install_location
sudo wget https://files.pythonhosted.org/packages/63/e2/f85981a51281bd30525bf664309332faa7c81782bb49e331af603421dbd1/cheroot-10.0.1.tar.gz -O cheroot.tar.gz
sudo tar xf cheroot.tar.gz
sudo cp -r cheroot-10.0.1/cheroot OSPy


echo ===== Creating and installing SystemD service =====
cat << EOF >> /tmp/ospy.service
#Service for OSPy running on a SystemD service
#
[Unit]
Description=OSPy for Python3
After=syslog.target network.target
[Service]
ExecStart=/usr/bin/python3 -u ${install_location}/OSPy/run.py
Restart=on-abort
WorkingDirectory=${install_location}/OSPy/
SyslogIdentifier=ospy
[Install]
WantedBy=multi-user.target
EOF

sudo cp /tmp/ospy.service /etc/systemd/system/
sudo systemctl enable ospy.service


if [ "$do_log2ram" = true ]; then
  echo ===== Installing log2ram =====
  cd /home/${current_user}
  wget https://github.com/azlux/log2ram/archive/master.tar.gz -O log2ram.tar.gz
  tar xf log2ram.tar.gz
  cd /home/${current_user}/log2ram-master
  sudo ./install.sh
  echo ===== Increasing logsize to 100M =====
  sed -i "s/40M/100M/g" /etc/log2ram.conf
  cd ~
fi

echo ===== Done installing OSPy and requirements. Please check the output above and reboot the Pi =====

if (whiptail --title "Setup finished" --yesno "Done installing OSPy and requirements.\n\nReboot now or choose Exit to review the output of the setup " --no-button "Exit" --yes-button "Reboot" 10 65); then
    echo "Restarting....."
    sudo reboot
else
    exit 1
fi
