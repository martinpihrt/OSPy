Remote Controller for OSPy based on M5stick-C
====
This controller allows you to select a program stored in the OSPy on the LCD display and start it with the button. The controller is connected to the home Wi-Fi network. We do not even need a mobile phone or a computer to quickly select programs. We will use this miniature controller.

### Start 
- Push power button + left button > 2 sec, next release power button. The Controller creates a Wi-Fi network (AP) called *OSPy-Controller-M5stick*. In AP mode we have 10 minutes to set.
- The LCD will show AP and the time remaining until the restart.
- We will connect to the *OSPy-Controller-M5stick* network using a mobile phone (tablet, laptop). The connection password is *ospy-m5stick-c*.  
- After connecting, open a web browser and enter the IP address: *http://192.168.1.1*. Then a web page will open where we will set up a connection to your Wi-Fi network (STA mode).  

### Wi-Fi Settings
- The website will display the available Wi-Fi networks in our area. Click on the displayed network to select our desired network.  
- Fill in the password for connecting to the network. After filling in, press the *Save* button.  

### Remote Controller Settings 
- Wi-Fi AP password = enter your password for access to Wi-Fi in AP mode (AP manager). Default is: "ospy-m5stick-c".
- FW upload password = enter your password for access to firmware uploading to Controller. Default is: "fg4s5b.s,trr7sw8sgyvrDfg".
- OSPy address = enter the IP address on which the OSPy server is running and api patch. For example: *https://192.168.88.247:8080/api/*.
- OSPy Authorization name = user name for access to OSPy (default is *admin*).  
- OSPy Authorization password = user password for access to OSPy (default is *opendoor*).
- NTP time server = enter NTP server for read (default is *europe.pool.ntp.org*).
- NTP GMT Offset = Greenwich Mean Time (GMT). GMT offset in seconds (default is *3600*). You need to adjust the UTC offset for your timezone in milliseconds.
    For UTC -5.00 : -5 * 60 * 60 : -18000
    For UTC +1.00 : 1 * 60 * 60 : 3600
    For UTC +0.00 : 0 * 60 * 60 : 0
- NTP Day Offset = Change the Daylight offset in milliseconds (default is *3600*). If your country observes Daylight saving time set it to 3600. Otherwise, set it to 0. Daylight saving time (DST), also known as daylight savings time or daylight time (the United States and Canada), and summer time (United Kingdom, European Union, and some others), is the practice of advancing clocks (typically by one hour) during warmer months so that darkness falls at a later clock time. The typical implementation of DST is to set clocks forward by one hour in the spring ("spring forward") and set clocks back by one hour in autumn ("fall back") to return to standard time. As a result, there is one 23-hour day in late winter or early spring and one 25-hour day in the autumn.

### Controller Settings - Finish
- After setting all parameters, press the *Save* button and press the *Restart* button in the main menu.  
- After switching on, the driver will try to connect to the set Wi-Fi network, download the network time, download the list of programs from OSPy.
- All statuses are displayed on the LCD display.

Remote Controller M5STICK-C
====

The Controller connects to the OSPy API and runs stored programs.
http(s)://[ip|name]:[port]/api/..
In Header for http GET/POST response: Header("Authorization", "Basic " "Username:Password") 
Example: program 8 runnow ->  https://192.168.88.247:8080/api/programs/7 POST do=runnow

#### Top
[![](https://github.com/martinpihrt/OSPy/blob/master/ospy/images/m5stick-c_1.png?raw=true)](https://github.com/martinpihrt/OSPy/blob/master/ospy/images/m5stick-c_1.png)

#### Bottom
[![](https://github.com/martinpihrt/OSPy/blob/master/ospy/images/m5stick-c_2.png?raw=true)](https://github.com/martinpihrt/OSPy/blob/master/ospy/images/m5stick-c_2.png)

#### Hand strap
[![](https://github.com/martinpihrt/OSPy/blob/master/ospy/images/m5stick-c_3.png?raw=true)](https://github.com/martinpihrt/OSPy/blob/master/ospy/images/m5stick-c_3.png)

### About M5STICK-C
M5stick-C https://shop.m5stack.com/products/stick-c

#### Power switch
- Power on: Press power button for 2 seconds
- Power off: Press power button for 6 seconds

#### Specification
Resources-Parameter

- ESP32-240MHz dual core, 600 DMIPS, 520KB SRAM, Wi-Fi, dual mode Bluetooth
- Flash Memory-4MB
- Power Input-5V @ 500mA
- Port-TypeC x 1, GROVE (I2C+I/0+UART) x 1
- LCD screen-0.96 inch, 80x160 Colorful TFT LCD, ST7735S
- Button-Custom button x 2
- LED-RED LED
- MEMS-MPU6886
- IR-Infrared transmission
- MIC-SPM1423
- RTC-BM8563
- PMU-AXP192
- Battery-95 mAh @ 3.7V
- Antenna-2.4G 3D Antenna
- PIN port-G0, G26, G36
- Operating Temperature-32°F to 104°F (0°C to 40°C)
- Net weight-15.1g
- Gross weight-33g
- Product Size-48.2x25.5x13.7mm
- Package Size-55x55x20mm
- Case Material-Plastic (PC)

#### FTDI driver
UnitV/M5StickV/M5StickC/ATOM may not work without driver in some systems. Users can manually install FTDI driver to fix this problem.
https://ftdichip.com/drivers/vcp-drivers/