Sensors Details
====

## ESP32 Sensor 

### HW Connection
* AP manager start button between GPIO18 pin and ground (the same button also controls the relay in STA mode, press <2s)  
* DS18B20-1 pin GPIO26 (3.3 V, data and pull-up 4k7 to 3.3V, ground)  
* DS18B20-2 pin GPIO25 (3.3 V, data and pull-up 4k7 to 3.3V, ground)  
* DS18B20-3 pin GPIO17 (3.3 V, data and pull-up 4k7 to 3.3V, ground)  
* DS18B20-4 pin GPIO16 (3.3 V, data and pull-up 4k7 to 3.3V, ground)  
* Dry Contact pin GPIO27 and ground (or pin and VCC 3.3V)  
* Motion contact pin GPIO14 and ground (or pin and VCC 3.3V)  
* Leak detector contact pin GPIO12 and ground (pulse input)
* Moisture detector via I2C bus SDA pin 33 and SCL pin 32
* Wi-Fi LED pin GPIO2 (in series via 220 Ohm resistor on LED and ground)  
* Relay pin GPIO19 (control voltage for the transistor that switches the relay)  
* Voltage input pin GPIO36 and ground (divider 100k/10k)  

Sensors Connection and Add into OSPy
====

### Start
- In the OSPy menu *settings* in the tab *sensors* we generate a new AES code with the button (or if we already know it from the sensors, we can enter it here).  
- Hold down the AP button on the sensor board (to call up the AP manager) for more than 3 seconds (the LED will start flashing quickly). The sensor creates a Wi-Fi network (AP) called *Sensor ESP32*.
- We will connect to the *Sensor ESP32* network using a mobile phone (tablet, laptop). The connection password is *ospy-sensor-esp32*.  
- After connecting, open a web browser and enter the IP address: *http://192.168.1.1*. Then a web page will open where we will set up a connection to your Wi-Fi network (STA mode).  

### Wi-Fi Settings
- The website will display the available Wi-Fi networks in our area. Click on the displayed network to select our desired network.  
- Fill in the password for connecting to the network. After filling in, press the *Save* button.  

### Sensor Settings
- Sensor Name = enter the name of this sensor (for example "pool temperature").  
- Wi-Fi AP password = enter your password for access to Wi-Fi in AP mode (AP manager). Default is: "ospy-sensor-esp32".
- FW upload password = enter your password for access to firmware uploading to sensor. Default is: "fg4s5b.s,trr7sw8sgyvrDfg".
- OSPy IP address = enter the IP address (or name) on which the OSPy server is running (for example: "192.168.88.202", or "sprinkler123.com").  
- OSPy port = port on which the OSPy server is available (default is "8080").  
- Use SSL (https) = if we do not have an encrypted connection via SSL set in the OSPs, then we will not check the box, otherwise (we will have an https connection) we will check the box.  
- AES key = from the OSP from the "sensors" tab we will use the generated 16-digit AES key. Within one OSP we will use the key in all sensors the same!  
- AES secure = a unique security code (16-digit) that each sensor has different!!! We choose a random combination.  
- Use OSPy authorization = not used yet (current FW version: 1.03 and OSPs 4.0.91 - 2021-01-11) do not have the function enabled. In the future, it will be used for user authentication (the sensor is already sending this data, but the OSPy are still ignoring it). If the box is checked, the name and password for logging in to the OSPy system will be sent. I recommend creating a new user in "settings" in OSPy and assigning him *sensor* permissions.  
- Authorization name = user name for access to OSPs (default is *admin*).  
- Authorization password = user password for access to OSPs (default is *opendoor*).  
- Sensor type = choose how this sensor should be reported (and send data to OSPy accordingly).  
- Sensor communication = Wi-Fi / LAN is so far the only available option that works (there will be other types of communication in the future. For example using an RF signal - radio).  
- Dry contact input is = select the option whether we want to connect a pull-up resistor at the ESP32 input (then the sensor is connected between pin and gnd) or as a pull-down (then the sensor is connected between pin and VCC 3.3V. sensor connect a 1 KOhm resistor between ground and pin).  
- Motion input is = select the option whether we want to connect a pull-up resistor at the ESP32 input (then the sensor is connected between pin and gnd) or as a pull-down (then the sensor is connected between pin and VCC 3.3 V. I recommend at the same time with the sensor connect a 1 KOhm resistor between ground and pin).  
- Moisture probe = select the option for used moisture probes: DHT22 (AM2302, AM2321), DHT 21 (AM2301), DHT11 - used SDA pin GPIO33 (not used I2C bus) and SHT21 (HTU21D) used I2C bus.

### Sensor Settings - Finish
- After setting all parameters, press the *Save* button and press the *Restart* button in the main menu.  
- If we have everything set up correctly, then after connecting to Wi-Fi, this sensor will appear in the OSPy in the *sensors / sensor search* tab.  
- Sensor search page. After clicking the *create from this* button, we can easily add a new sensor to the OSPy system.  
- If it is a *multi* type sensor, we can use it repeatedly. Once it will be assigned as, for example, sensor DS1 and the second time as a contact...  
- The sensors send data after 30 seconds. In case of unsuccessful sending, the interval is 5 seconds. In the case of a contact (motion) sensor, additional data is sent each time the input is changed. If no data arrives from the sensor within 2 minutes, the green circle in the OSPy change color to red! The time indicated for the circle shows the time since the last connection (sending data by the sensor).  