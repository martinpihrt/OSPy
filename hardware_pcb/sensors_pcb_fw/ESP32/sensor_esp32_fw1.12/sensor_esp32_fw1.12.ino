/*
 * Sensor for OSPy system 
 * Martin Pihrt - 21.06.2021
 * Arduino IDE >= 1.8.15
 * board ESP32 1.0.6 (https://github.com/espressif/arduino-esp32)
 * 
 *  AP manager: password for AP Wi-Fi "ospy-sensor-esp32" open browser "192.168.1.1"
 *  BUTTON AP MANAGER -> It must be held for at least >2 seconds when switching on (for starting AP manager) on time 10 minutes
 *  Manual switch relay to on/off with AP button (if press time <2 seconds)
 *  
 *  First uploading sketch to ESP32 from Arduino via programmer (vcc 3.3V, rx, tx, 0V): push EN and KEY button in same time. 
 *  Now switch power for board to ON. Click in Arduino "upload". If in Arduino text is "uploading" release EN button and next KEY button.
 *  
 *  Or command line in Windows:
 *  C:\Users\xxxxx\AppData\Local\Arduino15\packages\esp32\tools\esptool_py\3.0.0/esptool.exe --chip esp32 --port COMxxxx --baud 921600 --before default_reset --after hard_reset write_flash -z --flash_mode dio --flash_freq 80m --flash_size detect 0xe000 C:\Users\xxxx\AppData\Local\Arduino15\packages\esp32\hardware\esp32\1.0.6/tools/partitions/boot_app0.bin 0x1000 C:\Users\xxxx\AppData\Local\Arduino15\packages\esp32\hardware\esp32\1.0.6/tools/sdk/bin/bootloader_dio_80m.bin 0x10000 C:\Users\xxxx/sensor_esp32_fw1.07.ino.bin 0x8000 C:\Users\xxxx/sensor_esp32_fw1.07.ino.partitions.bin
 * 
*/

// Debug
                             // In esp32 the space is running out, leave out commented! May be unstable 
#define DEBUG                // Comment this line when DEBUG mode is not needed 

// FW version
int fw_version = 112;        // ex: FW version 112 is 1.12
/* 
 * FW 1.12: Possibility of tuning (calibration of temperature sensors + -) DS1-DS4 in menu AP manager.
 * FW 1.11: Fix ultrasonic probe, Disable Wi-Fi sleep (set maximal power "WIFI_PS_NONE").
 * FW 1.10: Added function to webserver for starting AP manager from OSPy. ( http://ip:port/AP_password)
 * FW 1.09: Added fake test for DS18B20 sensors (China clone sensors) Source:  https://github.com/cpetrich/counterfeit_DS18B20/, Documentation:  https://github.com/cpetrich/counterfeit_DS18B20/
   ex on serial monitor:
   12:47:33.161 -> DS18B20 nr. 1 is connected
   12:47:33.161 -> 28-FF-B1-5E-61-16-03-AD: ROM does not follow expected pattern 28-xx-xx-xx-xx-00-00-crc. Error.
   12:47:33.214 ->   Scratchpad Register: 08/01/01/01/7F/FF/7F/10/3E
   12:47:33.214 ->   Info only: Scratchpad bytes 2,3,4 (01/01/7F):  not Maxim default values 4B/46/7F.
   12:47:33.214 ->   Scratchpad byte 5 (0xFF):  ok.
   12:47:33.214 ->   Scratchpad byte 6 (0x7F):  unexpected value. Error.
   12:47:33.214 ->   Scratchpad byte 7 (0x10):  ok.
   12:47:33.214 ->   0x4E modifies alarm registers:  ok.
   12:47:33.214 ->   0x4E accepts 10 bit resolution:  ok.
   12:47:33.214 ->   0x4E preserves reserved bytes:  no, got: FF/3F/10. Error.
   12:47:33.261 ->   0x4E accepts 12 bit resolution:  ok.
   12:47:33.261 ->   0x4E preserves reserved bytes:  no, got: FF/7F/10. Error.
   12:47:33.261 ->   Checking byte 6 upon temperature change: not necessary. Skipped.
   12:47:33.261 ->   --> Sensor appears to be counterfeit based on 4 deviations.
 * FW 1.08: Added flash blink state to LED when the sensor is connecting to a Wi-Fi network. 
   Added new parameter running time for relay outputs (ex: http://192.168.88.207/0123456789abcdef?re=1&run=120 re=1 is relay on and run=xxx is time in seconds 0123456789abcdff is secure code from sensor. If the run parameter is not specified, it will be ignored).
   Added reboot sensor if Wi-Fi disconnect. Added median filter for average sonic distance (5 samples average).   
 * FW 1.07: Fix time for AP manager to 10 minutes. Fix message in serial print.
   Add calibration for voltage divider in to AP settings. Add LED ON if relay is ON.
   Add ultrasonic support for distance level (not tested yet). Tested probe DHT22 and DHT11 for moisture measuring.
 * FW 1.06: Add time limit for sending data (if it was not sent to the OSPy within 2 minutes, then restart the sensor). Sensor freeze prevention. 
 * FW 1.05: Add selector for moisture probe type - user changeable (in AP mode). 
   Add password for access to upload new firmware via http in STA (normal) mode - user changeable.
   For uploading in STA mode use html post "/FW_YOURUPLOADPASSWORD".
   Add password for Wi-Fi access - user changeable (in AP mode).
   Add moisture sensors DHT22 (AM2302, AM2321), DHT 21 (AM2301), DHT11 - used SDA pin GPIO33 (not used I2C bus).
   Add moisture sensor SHT21 (HTU21D) used I2C bus.
 * FW 1.04: Add leak detector to input via interrupt routine. If leak pulses > 0 sending data in cycle 3 seconds. 
   Add I2C scanner routine for find I2C addreses (for moisture and more)
 * FW 1.03: Add upload new firmware via web. Dry contact and motion now support pull-up or pull-down connection. Add manual relay on/off with AP button (if press time < 2 sec).Voltage check with R1=100K and R2=10K as divider from source to analog pin ESP32 ADC1_CH0 (GPIO36). Add CSS style (OpenSprinkler design). Add print time to reboot on pages. Fix read temperature 85C from 4x DS18B20.
 * FW 1.02: Add AP manager for settings sensor from phone, tablet (4 minutes timeout). Saving to eeprom memory. Fast blinking LED if AP manager is run. Slow blinking LED if normal run
   control relay: ex: http://192.168.88.207/0123456789abcdff?re=1 (or re=0) 0123456789abcdff is secure code from sensor
   FW 1.01: Initial version
 */

// SN
const char *SNnum = "001";   // sensor serial number

// CPU core is
byte cpu_core     = 0;       // CPU is 0=ESP32, 1=ESP8266 ...

// Wire
#include <Wire.h>

// ESP32
#include "WiFi.h"
#include <esp_wifi.h>        // for Wi-Fi mode, see setWiFiPowerMode() at end sketch
#include <WiFiMulti.h>
WiFiMulti wifiMulti;
#include "HTTPClient.h"
#include "base64.h"

//HTTP SERVER************
#include <WebServer.h>
WebServer server(80);
#include <WiFiAP.h>
#include <DNSServer.h>
const byte DNS_PORT = 53;
DNSServer dnsServer;

//HTTP UPDATE***********
#define UPLOAD_BIN_VIA_HTTP  // add # for disabling web uploads

#ifdef UPLOAD_BIN_VIA_HTTP
  #include <Update.h>
#endif // end upload 

#include <driver/adc.h>      // A/D converters
/* ESP32 support 18 analog channels (12 bit). Each voltage level is between 0 and 4095.
  3.3 volt at the input, the digital value will be 4095. So the maximum voltage limit is 3.3 volt.
  -> ADC1_CH0 – GPIO36
  ADC1_CH1 – GPIO37
  ADC1_CH2 – GPIO38
  ADC1_CH3 – GPIO39
  ADC1_CH4 – GPIO32
  ADC1_CH5-  GPIO33
  ADC1_CH6 – GPIO34
  ADC1_CH7 – GPIO35
  ADC2_CH0 – GPIO4
  ADC2_CH1 – GPIO0
  ADC2_CH2 – GPIO2
  ADC2_CH3 – GPIO15
  ADC2_CH4 – GPIO13
  ADC2_CH5 – GPIO12
  ADC2_CH6 – GPIO14
  ADC2_CH7 – GPIO27
  ADC2_CH8 – GPIO25
  ADC2_CH9 – GPIO26
*/

// AES 
#include "mbedtls/aes.h"     // https://tls.mbed.org/api/aes_8h.html#a0e59fdda18a145e702984268b9ab291a
mbedtls_aes_context aes;     // https://www.dfrobot.com/blog-911.html
unsigned char aesoutput[16];

// AP manager button
byte input_ap_manager  = 18;                     // pin for button

// 4x DS18B20 temperature
byte input_sensor_1    = 26;                     // pin for DS1 sensors
byte input_sensor_2    = 25;                     // pin for DS2 sensors
byte input_sensor_3    = 17;                     // pin for DS3 sensors
byte input_sensor_4    = 16;                     // pin for DS4 sensors

// Dry Contact, Motion contact
byte input_sensor_dry  = 27;                     // pin for dry contact
byte input_sensor_mot  = 14;                     // pin for motion contact

// Leak detector
byte input_sensor_leak = 12;                     // pin for leak contact

// Sonic distance
byte pin_trig          = 23;                     // trig pin on the JSN-SR04 probe
byte pin_echo          = 22;                     // echo pin on the JSN-SR04 probe

// Wi-Fi LED
byte out_led           = 2;                      // blue LED on the board

// RELAY
byte out_relay         = 19;                     // relay for control on/off from OSPy
bool revers            = false;                  // if true is active out in LOW, false is active out in HIGH (for inversion relay logic)

// I2C
byte I2C_SDA           = 23;                     // SDA (and not I2C moisture probe DHT22...)
byte I2C_SCL           = 22;                     // SCL

// Moisture probe
#include "DHT.h"                                 // DHT22 (AM2302, AM2321), DHT 21 (AM2301), DHT11 - used pin GPIO33 (if not used I2C SDA)
#include "SparkFunHTU21D.h"                      // SHT21 (HTU21D) - use I2C bus
HTU21D htu;
#define dht_pin         23                       // same as SDA PIN
DHT dht22(dht_pin, DHT22);
DHT dht21(dht_pin, DHT21);
DHT dht11(dht_pin, DHT11);

#include "MedianFilter.h"                        // https://github.com/luisllamasbinaburo/Arduino-MedianFilter
MedianFilter filter(5,0);                        // 5 samples average for sonic distance

#include <OneWire.h>                             // https://github.com/stickbreaker/OneWire  This modifications supports the ESP32 under the Arduino-esp32 Environment.
#include "DallasTemperature.h"
OneWire oneWire_1(input_sensor_1);
DallasTemperature DS1sensors(&oneWire_1);
OneWire oneWire_2(input_sensor_2);
DallasTemperature DS2sensors(&oneWire_2);
OneWire oneWire_3(input_sensor_3);
DallasTemperature DS3sensors(&oneWire_3);
OneWire oneWire_4(input_sensor_4);
DallasTemperature DS4sensors(&oneWire_4);

#ifdef DEBUG
 #define DEBUG_PRINT(x)     Serial.print(x)
 #define DEBUG_PRINTDEC(x)  Serial.print(x, DEC)
 #define DEBUG_PRINTLN(x)   Serial.println(x)
#else
 #define DEBUG_PRINT(x)
 #define DEBUG_PRINTDEC(x)
 #define DEBUG_PRINTLN(x)
#endif

// EEPROM saving and reading data
#include <EEPROM.h>
#define elementSize(type, element) sizeof(((type *)0)->element) 

typedef struct{
  char WiFi_SSID[33];     // max 32 char SSID for Wi-Fi
  char WiFi_PASS[33];     // max 32 char PASS for Wi-Fi
  char AES_KEY[17];       // max 16 char AES key
  char AES_SEC[17];       // max 16 char AES secret
  char USE_SSL[2];        // 0,1 enable or disable SSL for https
  char USE_AUTH[2];       // 0,1 enable or disable OSPy authorisation
  char AUTH_NAME[17];     // max 16 char user name for access to OSPy
  char AUTH_PASS[17];     // max 16 char user password for access to OSPy
  char SERV_IP[33];       // max 32 char OSPy server IP ex: 192.168.88.215
  char SERV_PORT[8];      // max 5 char OSPy server port ex: 8080
  char SEN_NAME[33];      // max 32 char sensor name ex: sensor 1
  char SEN_TYPE[4];       // 5 is temperature sensor (1=Dry Contact, 2=Leak Detector, 3=Moisture, 4=Motion, 5=temperature, 6=multisensor)
  char SEN_COM[4];        // 0 is Wi-Fi/Lan (1=Radio)
  char MAGICNR[4];        // for first sensor setup if not yed setuped. If setuped magic nbr is 666 :-)
  char INVERT_DRY[4];     // dry contact inverted logic 0->1
  char INVERT_MOTI[4];    // motion contact inverted logic 0->1
  char MOIST_TYPE[2];     // moisture probe type 0=DHT22, 1=DHT21, 2=DHT11
  char UPLOAD_PASS[33];   // max 32 char password for uploading access in STA mode via http from OSPy
  char AP_WIFI_PASS[33];  // max 32 char password for Wi-Fi in AP mode
  char DIVIDER_CORRECTION[6];  // max 5 char divider correction (for voltage probe) +- xxxx
  char SEL_MOIST_SONIC[3];     // pin for connector is 0 moisture, 1 sonic 
  char DS1_CALIB[4];           // calibration of temperature from sensors + -
  char DS2_CALIB[4];           // calibration of temperature from sensors + -
  char DS3_CALIB[4];           // calibration of temperature from sensors + -
  char DS4_CALIB[4];           // calibration of temperature from sensors + -
} eepromdata_t;

// date and time compilation
#define CompilerTIME __TIME__ // time hh:mm:ss 
#define CompilerDATE __DATE__ // date M mm dd yyyy

// throw compilation error if there board is not ESP32
#if not defined(ESP32)
   #error "Error! The selected board is not ESP32! Select: doit ESP32 devkit V1"
#endif

#define SECS_PER_MIN  (60UL)
#define SECS_PER_HOUR (3600UL)
#define SECS_PER_DAY  (SECS_PER_HOUR * 24L)
#define numberOfSeconds(_time_) (_time_ % SECS_PER_MIN)  
#define numberOfMinutes(_time_) ((_time_ / SECS_PER_MIN) % SECS_PER_MIN)
#define numberOfHours(_time_) (( _time_% SECS_PER_DAY) / SECS_PER_HOUR)
#define elapsedDays(_time_) ( _time_ / SECS_PER_DAY)

//  values from EEPROM
char WiFi_SSID[33];                             
char WiFi_PASS[33];                             
char AES_KEY[17];
char AES_SEC[17];      
byte USE_SSL;       
byte USE_AUTH;       
char AUTH_NAME[17];    
char AUTH_PASS[17];   
char SERV_IP[33];       
char SERV_PORT[7];     
char SEN_NAME[33];
char UPLOAD_PASS[33]; 
char AP_WIFI_PASS[33];    
int  DIVIDER_CORRECTION; 
byte SEN_TYPE;       
byte SEN_COM; 
byte INVERT_DRY; 
byte INVERT_MOTI;
byte MOIST_TYPE;
byte SEL_MOIST_SONIC;
float DS1_CALIB, DS2_CALIB, DS3_CALIB, DS4_CALIB;       

int curRssi, curPercent, curMoti, curDrcon;      // current RSSI, RSSI in percent, motion, dry contact
int curSon = -1;                                 // current sonic distance 
int LastCurMoti=1, LastCurDrcon=1;               // last value for motion, dry contact 
int LastcurSon = -1;                             // last value for sonic
unsigned long prevTikTime, prevTime, nowTime, interval;   // previous time for sec timer (millis), send data timer (millis), current time (millis)  
unsigned long prevTikTime_50ms;                  // previous millis for 50ms timer
float curTemp_1 = -127;                          // current temperature DS1
float curTemp_2 = -127;                          // current temperature DS2
float curTemp_3 = -127;                          // current temperature DS3
float curTemp_4 = -127;                          // current temperature DS4
float LastcurTemp_1, LastcurTemp_2, LastcurTemp_3, LastcurTemp_4; // last value temperature DS1-DS4
float curVdd, curHumi, curLkdet;                 // current voltage, moisture, leak detector
float LastcurVdd, LastcurLkdet, LastcurHumi;     // last value voltage, leak detector, moisture
bool send_to_OSPy = true;                        // if true -> send data to api OSPy web page
bool relay_status;                               // relay status (0=off, 1=on)
String IPadr  = "";                              // current IP address
String MACadr = "";                              // current MAC address
String serverName = "";                          // server address
String allSN = "";                               // sensor hostname
bool ap_manager = false;                         // AP manager
unsigned long APtime;                            // AP (ms now for timeout)
bool DS_1_OK, DS_2_OK, DS_3_OK, DS_4_OK;         // if DS sensor xx is present DS_xx_OK is true
bool change;                                     // manual relay on/off with AP button (if press time < 2000 sec)
unsigned long APtimeLCD;                         // time counter to reboot if AP manager is active
unsigned long last_send_to_ospy;                 // last send to OSPy (millis)
unsigned long set_to_on;                         // millis for run time parameter
unsigned long run_set_to;                        // miliseconds for run time from web server form &run=xxx

// interval settings 
unsigned long wait_send = 30000;                 // 30 sec loop for sending data 
unsigned long APtimeout = 600000;                // 10 minutes timeout for AP manager
unsigned long send_timeout = 120000;             // 2 minutes for timeout (for reboot if not send to ospy)

// INTERRUPT for blink LED
volatile bool en_led_blink;
// INTERRUPT for leak detector pulses
volatile unsigned int leakcounter;               // counter pulses per seconds via isr for leak detector

#define INTERRUPT_ATTR IRAM_ATTR                 // 1 sec tick for ESP32 CPU 80MHZ is T = 1/(80MHZ/80) = 1 us. 1000000 tick is 1 sec  
hw_timer_t * timer1 = NULL;                      // create timer nr 1
portMUX_TYPE timerMux0 = portMUX_INITIALIZER_UNLOCKED;
portMUX_TYPE mux = portMUX_INITIALIZER_UNLOCKED;

void IRAM_ATTR onTimer(){                        // blinking LED via interrupt (second timer in Wi-FI STA mode)
  portENTER_CRITICAL_ISR(&timerMux0);
  if(en_led_blink){   
     digitalWrite(out_led, !digitalRead(out_led));       
  }// end if
  portEXIT_CRITICAL_ISR(&timerMux0);
}// end void

void IRAM_ATTR isr(){                            // increment leak counter via interrupt   
  portENTER_CRITICAL_ISR(&mux);  
  leakcounter += 1;
  portEXIT_CRITICAL_ISR(&mux);
}// end void

// EEPROM HELPERS*********************************************************************************************************
String getEEPROMString(int start, int len){
  String string = "";
  for(int i = start; i < + start + len; ++i){
    uint8_t b = EEPROM.read(i);
    if ((0xff == b) || (0 == b)) break;
    string += char(b);
  }//end for
  return string;
}//end string

void setEEPROMString(int start, int len, String string){
  int si = 0;
  for(int i = start; i < start + len; ++i){
    char c;
    if(si < string.length()){
      c = string[si];
    }//end if
    else{
      c = 0;
    }//end else
    EEPROM.write(i, c);
    ++si;
  }//end for
}//end void

void setEEPROMdefault(){ 
   setEEPROMString(offsetof(eepromdata_t, WiFi_SSID), elementSize(eepromdata_t, WiFi_SSID), "none");
   setEEPROMString(offsetof(eepromdata_t, WiFi_PASS), elementSize(eepromdata_t, WiFi_PASS), "none");
   setEEPROMString(offsetof(eepromdata_t, AES_KEY), elementSize(eepromdata_t, AES_KEY),     "0123456789abcdef");
   setEEPROMString(offsetof(eepromdata_t, AES_SEC), elementSize(eepromdata_t, AES_SEC),     "0123456789abcdef");
   setEEPROMString(offsetof(eepromdata_t, USE_SSL), elementSize(eepromdata_t, USE_SSL),     "0");
   setEEPROMString(offsetof(eepromdata_t, USE_AUTH), elementSize(eepromdata_t, USE_AUTH),   "1");
   setEEPROMString(offsetof(eepromdata_t, AUTH_NAME), elementSize(eepromdata_t, AUTH_NAME), "admin");
   setEEPROMString(offsetof(eepromdata_t, AUTH_PASS), elementSize(eepromdata_t, AUTH_PASS), "opendoor");
   setEEPROMString(offsetof(eepromdata_t, SERV_IP), elementSize(eepromdata_t, SERV_IP),     "0.0.0.0"); 
   setEEPROMString(offsetof(eepromdata_t, SERV_PORT), elementSize(eepromdata_t, SERV_PORT), "8080"); 
   setEEPROMString(offsetof(eepromdata_t, SEN_NAME), elementSize(eepromdata_t, SEN_NAME),   "ESP32 Sensor");
   setEEPROMString(offsetof(eepromdata_t, SEN_TYPE), elementSize(eepromdata_t, SEN_TYPE),   "5");   // 1=Dry Contact, 2=Leak Detector, 3=Moisture, 4=Motion, 5=temperature, 6=multi sensor
   setEEPROMString(offsetof(eepromdata_t, SEN_COM), elementSize(eepromdata_t, SEN_COM),     "0");   // 0=Wi-Fi/Lan, 1=Radio
   setEEPROMString(offsetof(eepromdata_t, INVERT_MOTI), elementSize(eepromdata_t,INVERT_MOTI),"1"); // reversed (1=active in HIGH)
   setEEPROMString(offsetof(eepromdata_t, INVERT_DRY), elementSize(eepromdata_t, INVERT_DRY), "0"); // reversed (1=active in HIGH)
   setEEPROMString(offsetof(eepromdata_t, MAGICNR), elementSize(eepromdata_t, MAGICNR),    "666");
   setEEPROMString(offsetof(eepromdata_t, MOIST_TYPE), elementSize(eepromdata_t, MOIST_TYPE), "0"); // moisture probe type
   setEEPROMString(offsetof(eepromdata_t, UPLOAD_PASS), elementSize(eepromdata_t, UPLOAD_PASS),   "fg4s5b.s,trr7sw8sgyvrDfg"); // password for upload in STA mode
   setEEPROMString(offsetof(eepromdata_t, AP_WIFI_PASS), elementSize(eepromdata_t, AP_WIFI_PASS), "ospy-sensor-esp32");        // password for Wi-Fi access in AP mode
   setEEPROMString(offsetof(eepromdata_t, DIVIDER_CORRECTION), elementSize(eepromdata_t, DIVIDER_CORRECTION), "0");            // + or - coorection mV fo divider
   setEEPROMString(offsetof(eepromdata_t, SEL_MOIST_SONIC), elementSize(eepromdata_t, SEL_MOIST_SONIC), "0");                  // 0=moisture probe or 1=sonic probe
   setEEPROMString(offsetof(eepromdata_t, DS1_CALIB), elementSize(eepromdata_t, DS1_CALIB), "0.0");                            // calibration of temperature sensors + -
   setEEPROMString(offsetof(eepromdata_t, DS2_CALIB), elementSize(eepromdata_t, DS2_CALIB), "0.0");                            // calibration of temperature sensors + -
   setEEPROMString(offsetof(eepromdata_t, DS3_CALIB), elementSize(eepromdata_t, DS3_CALIB), "0.0");                            // calibration of temperature sensors + -
   setEEPROMString(offsetof(eepromdata_t, DS4_CALIB), elementSize(eepromdata_t, DS4_CALIB), "0.0");                            // calibration of temperature sensors + -

   EEPROM.commit();  // save to eeprom
   delay(500);
   
   #ifdef DEBUG 
      Serial.println(F("SET EEPROM to DEFAULT OK"));
      delay(1000);
   #endif  

   reboot();         // reboot this sensor 
}// end void

void initEEPROM(){  
   String  tmp;
   #ifdef DEBUG 
      Serial.println(F("INIT EEPROM"));
   #endif    
   
   tmp = getEEPROMString(offsetof(eepromdata_t, WiFi_SSID), elementSize(eepromdata_t, WiFi_SSID));   // load as string  
   strncpy(WiFi_SSID, tmp.c_str(), sizeof(WiFi_SSID));                                               // and copy as char  
   WiFi_SSID[sizeof(WiFi_SSID) - 1] = 0;

   tmp = getEEPROMString(offsetof(eepromdata_t, WiFi_PASS), elementSize(eepromdata_t, WiFi_PASS));  
   strncpy(WiFi_PASS, tmp.c_str(), sizeof(WiFi_PASS));                                                
   WiFi_PASS[sizeof(WiFi_PASS) - 1] = 0;  

   tmp = getEEPROMString(offsetof(eepromdata_t, AES_KEY), elementSize(eepromdata_t, AES_KEY));  
   strncpy(AES_KEY, tmp.c_str(), sizeof(AES_KEY));                                                
   AES_KEY[sizeof(AES_KEY) - 1] = 0;

   tmp = getEEPROMString(offsetof(eepromdata_t, AES_SEC), elementSize(eepromdata_t, AES_SEC));  
   strncpy(AES_SEC, tmp.c_str(), sizeof(AES_SEC));                                                
   AES_SEC[sizeof(AES_SEC) - 1] = 0;   

   USE_SSL = atoi(getEEPROMString(offsetof(eepromdata_t, USE_SSL), elementSize(eepromdata_t, USE_SSL)).c_str());

   USE_AUTH = atoi(getEEPROMString(offsetof(eepromdata_t, USE_AUTH), elementSize(eepromdata_t, USE_AUTH)).c_str());

   tmp = getEEPROMString(offsetof(eepromdata_t, AUTH_NAME), elementSize(eepromdata_t, AUTH_NAME));  
   strncpy(AUTH_NAME, tmp.c_str(), sizeof(AUTH_NAME));                                                
   AUTH_NAME[sizeof(AUTH_NAME) - 1] = 0;    

   tmp = getEEPROMString(offsetof(eepromdata_t, AUTH_PASS), elementSize(eepromdata_t, AUTH_PASS));  
   strncpy(AUTH_PASS, tmp.c_str(), sizeof(AUTH_PASS));                                                
   AUTH_PASS[sizeof(AUTH_PASS) - 1] = 0;   

   tmp = getEEPROMString(offsetof(eepromdata_t, SERV_IP), elementSize(eepromdata_t, SERV_IP));  
   strncpy(SERV_IP, tmp.c_str(), sizeof(SERV_IP));                                                
   SERV_IP[sizeof(SERV_IP) - 1] = 0; 

   tmp = getEEPROMString(offsetof(eepromdata_t, SERV_PORT), elementSize(eepromdata_t, SERV_PORT));  
   strncpy(SERV_PORT, tmp.c_str(), sizeof(SERV_PORT));                                                
   SERV_PORT[sizeof(SERV_PORT) - 1] = 0;  

   tmp = getEEPROMString(offsetof(eepromdata_t, SEN_NAME), elementSize(eepromdata_t, SEN_NAME));  
   strncpy(SEN_NAME, tmp.c_str(), sizeof(SEN_NAME));                                                
   SEN_NAME[sizeof(SEN_NAME) - 1] = 0;           

   SEN_TYPE = atoi(getEEPROMString(offsetof(eepromdata_t, SEN_TYPE), elementSize(eepromdata_t, SEN_TYPE)).c_str());
   SEN_COM = atoi(getEEPROMString(offsetof(eepromdata_t, SEN_COM), elementSize(eepromdata_t, SEN_COM)).c_str());
   INVERT_DRY = atoi(getEEPROMString(offsetof(eepromdata_t, INVERT_DRY), elementSize(eepromdata_t, INVERT_DRY)).c_str());
   INVERT_MOTI = atoi(getEEPROMString(offsetof(eepromdata_t, INVERT_MOTI), elementSize(eepromdata_t, INVERT_MOTI)).c_str());
   MOIST_TYPE = atoi(getEEPROMString(offsetof(eepromdata_t, MOIST_TYPE), elementSize(eepromdata_t, MOIST_TYPE)).c_str());
   SEL_MOIST_SONIC = atoi(getEEPROMString(offsetof(eepromdata_t, SEL_MOIST_SONIC), elementSize(eepromdata_t, SEL_MOIST_SONIC)).c_str());
   DIVIDER_CORRECTION = atoi(getEEPROMString(offsetof(eepromdata_t, DIVIDER_CORRECTION), elementSize(eepromdata_t, DIVIDER_CORRECTION)).c_str());

   String d1 = (getEEPROMString(offsetof(eepromdata_t, DS1_CALIB), elementSize(eepromdata_t, DS1_CALIB)).c_str());
   String d2 = (getEEPROMString(offsetof(eepromdata_t, DS2_CALIB), elementSize(eepromdata_t, DS2_CALIB)).c_str());
   String d3 = (getEEPROMString(offsetof(eepromdata_t, DS3_CALIB), elementSize(eepromdata_t, DS3_CALIB)).c_str());
   String d4 = (getEEPROMString(offsetof(eepromdata_t, DS4_CALIB), elementSize(eepromdata_t, DS4_CALIB)).c_str());
   DS1_CALIB = d1.toFloat(); // convert from string to float
   DS2_CALIB = d2.toFloat();
   DS3_CALIB = d3.toFloat();
   DS4_CALIB = d4.toFloat();

   tmp = getEEPROMString(offsetof(eepromdata_t, UPLOAD_PASS), elementSize(eepromdata_t, UPLOAD_PASS));    
   strncpy(UPLOAD_PASS, tmp.c_str(), sizeof(UPLOAD_PASS));                                                 
   UPLOAD_PASS[sizeof(UPLOAD_PASS) - 1] = 0;

   tmp = getEEPROMString(offsetof(eepromdata_t, AP_WIFI_PASS), elementSize(eepromdata_t, AP_WIFI_PASS));    
   strncpy(AP_WIFI_PASS, tmp.c_str(), sizeof(AP_WIFI_PASS));                                                
   AP_WIFI_PASS[sizeof(AP_WIFI_PASS) - 1] = 0;

   int mgc = atoi(getEEPROMString(offsetof(eepromdata_t, MAGICNR), elementSize(eepromdata_t, MAGICNR)).c_str());  
   if(mgc != 666) setEEPROMdefault();
}// end void   

// SETUP******************************************************************************************************************   
void setup() {
  pinMode(out_led, OUTPUT);  
  pinMode(out_relay, OUTPUT);
  digitalWrite(out_led, LOW);
  en_led_blink = false;  
  set_rele(0);                                 // relay off

  timer1 = timerBegin(0, 80, true);            // 80MHZ CPU
  timerAttachInterrupt(timer1, &onTimer, true);// connect function onTimer for timer (first available timer from 4 HW timers in ESP32)
  timerAlarmWrite(timer1, 1000000, true);      // set alarm for call function onTimer (1 us => 0.1 sec is 100000 us, 1 sec is 1000000 us)
  timerAlarmEnable(timer1);                    // enable second timer  
  
  #ifdef DEBUG 
    Serial.begin(115200);
    delay(100);
    Serial.println(F(""));
    Serial.flush();
  #endif  

  EEPROM.begin(sizeof(eepromdata_t) + 10);   // we start working with EEPROM (10 bytes is only a reserve)
  
  initEEPROM();                              // reading stored values from the eeprom memory

  DS1sensors.begin();
  DS2sensors.begin();
  DS3sensors.begin();
  DS4sensors.begin();
  delay(100);
  
  byte addr1[8];
  if(oneWire_1.search(addr1)){
     oneWire_1.reset_search();
     DS_1_OK = true;
     Serial.println(F("DS18B20 nr. 1 is connected"));
     Serial.flush();  
     test_fake_ds(oneWire_1); // test for faked sensor 1   
  }//end test oneWire search 
  byte addr2[8]; 
  if(oneWire_2.search(addr2)){
     oneWire_2.reset_search();         
     DS_2_OK = true;
     Serial.println(F("DS18B20 nr. 2 is connected"));
     Serial.flush();
     test_fake_ds(oneWire_2); // test for faked sensor 2 
  }//end test oneWire search
  byte addr3[8];
  if(oneWire_3.search(addr3)){
     oneWire_3.reset_search();     
     DS_3_OK = true;
     Serial.println(F("DS18B20 nr. 3 is connected"));
     Serial.flush();
     test_fake_ds(oneWire_3); // test for faked sensor 3     
  }//end test oneWire search
  byte addr4[8];
  if(oneWire_4.search(addr4)){
     oneWire_4.reset_search();         
     DS_4_OK = true;
     Serial.println(F("DS18B20 nr. 4 is connected"));
     Serial.flush();
     test_fake_ds(oneWire_4); // test for faked sensor 4     
  }//end test oneWire search  

  if(MOIST_TYPE==3 && SEL_MOIST_SONIC==0){
    Wire.begin(I2C_SDA,I2C_SCL);
    byte error, address;
    int nDevices;
    Serial.println(F("Find I2C..."));
    Serial.flush();
    nDevices = 0;
    for(address = 1; address < 127; address++){
      Wire.beginTransmission(address);
      error = Wire.endTransmission();
      if(error == 0){
        Serial.print(F("I2C found 0x"));
        if(address<16) Serial.print("0");
          Serial.println(address,HEX);
          Serial.flush();
          nDevices++;
        }
      else if (error==4){
        Serial.print(F("Error on address 0x"));
        if(address<16) Serial.print("0");
        Serial.println(address,HEX);
        Serial.flush();
      }    
    }// end for
    if(nDevices == 0) {Serial.println(F("Not found I2C devices")); Serial.flush();}   
  }//end if i2c
    
  if(get_ap_button()){                       // check if button pressed
     ap_manager = true;                      // enabling AP manager
     WIFIAP_setup();                         // AP manager routine
  }   

  if(!ap_manager){  
    WiFi.disconnect(true);        
    delay(200);
    WiFi.mode(WIFI_STA);          
    delay(200);                   
    WiFi.setSleep(false);
    delay(100);
    setWiFiPowerMode();

    allSN = ArduinoDateTimeCompile();            
    allSN += "SensorESP32sn"+String(SNnum); 
    #ifdef DEBUG 
       Serial.print(F("SN: "));
       Serial.println(SNnum);
       Serial.flush();
       // ex 107 to 1.07
       byte ones = (fw_version%10); 
       byte tens = ((fw_version/10)%10);
       byte hundreds = ((fw_version/100)%10);
       Serial.print(F("FW version: "));
       Serial.print(hundreds);
       Serial.print(F(".")); 
       Serial.print(tens);
       Serial.println(ones);
       Serial.flush();       
    #endif                        
    const char* Hostname_complete = allSN.c_str();       
    WiFi.setHostname(Hostname_complete);
    delay(100);                  
    
    wifiMulti.addAP(WiFi_SSID, WiFi_PASS);

    while(wifiMulti.run()!=WL_CONNECTED){
       digitalWrite(out_led, HIGH);
       delay(50);
       digitalWrite(out_led, LOW); 
       delay(2000);
       #ifdef DEBUG
          Serial.println(F("Wi-Fi Connecting"));
          Serial.flush();
       #endif 
       if(get_ap_button()){                      // check if button pressed
         ap_manager = true;                      // enabling AP manager
         WIFIAP_setup();                         // AP manager routine
         return;
       }         
    }// end while 
    
    if((wifiMulti.run() == WL_CONNECTED)){       // pokud je Wi-Fi pripojeno nastavime hostname, ukazeme RSSI, MAC a IP
       en_led_blink = true;
       #ifdef DEBUG
           Serial.println(F("Wi-Fi Connected"));
           Serial.print(F("Hostname: "));
           Serial.println(Hostname_complete);
           Serial.flush();
       #endif
       WiFi.enableIpV6();                         // enable sta ipv6
       delay(2000);
  
       char szRet[40];
       sprintf(szRet,"%02x%02x:%02x%02x:%02x%02x:%02x%02x:%02x%02x:%02x%02x:%02x%02x:%02x%02x",
       WiFi.localIPv6()[0], WiFi.localIPv6()[1], WiFi.localIPv6()[2], WiFi.localIPv6()[3],
       WiFi.localIPv6()[4], WiFi.localIPv6()[5], WiFi.localIPv6()[6], WiFi.localIPv6()[7],
       WiFi.localIPv6()[8], WiFi.localIPv6()[9], WiFi.localIPv6()[10], WiFi.localIPv6()[11],
       WiFi.localIPv6()[12], WiFi.localIPv6()[13], WiFi.localIPv6()[14], WiFi.localIPv6()[15]);
       #ifdef DEBUG
          get_ip();
          Serial.print(F("IPV6: "));
          Serial.println(szRet);
          Serial.flush();
       #endif    
    }// end connected
    
    interval = wait_send;
  }//end ap_manager  
  
  serverName = "http";
  if(USE_SSL == 1){
     serverName += "s";
  }
  serverName += "://"+String(SERV_IP)+":"+String(SERV_PORT)+"/api/sensor"; 

  server.on("/" + String(AES_SEC), [](){                      // ex for on: http://192.168.88.207/0123456789abcdff?re=1
    if(server.hasArg("re")){        
      int o = atoi(server.arg("re").c_str());
      if(server.hasArg("run")){                               // run time parameter in seconds ex for on: http://192.168.88.207/0123456789abcdff?re=1&run=10
         set_to_on = millis();                                // now runtime has theses millis()
         run_set_to = (atoi(server.arg("run").c_str()))*1000; // run time is in seconds -> convert to mseconds
         #ifdef DEBUG
           Serial.print(F("WEB RUNTIME: "));
           Serial.println(run_set_to);
           Serial.flush();
         #endif
      }
      else{
         run_set_to = 0;
      }
      if(o==1) {
         set_rele(1);                                         // relay on
         #ifdef DEBUG
           Serial.println(F("WEB RELAY ON"));
           Serial.flush();
         #endif
         en_led_blink = false;
         digitalWrite(out_led, HIGH);  
         server.send(200, "text/html", String(o));
      }
      else if(o==0) {
         run_set_to = 0;
         set_rele(0);                                         // relay off
         #ifdef DEBUG
           Serial.println(F("WEB RELAY OFF"));
           Serial.flush();
         #endif
         digitalWrite(out_led, LOW);
         en_led_blink = true;    
         server.send(200, "text/html", String(o));      
      }
    }
    else{
       server.send(404, "text/html", "ERR");                  // not found
    }
  });

  #ifdef UPLOAD_BIN_VIA_HTTP     
    server.on("/FW_" + String(UPLOAD_PASS), HTTP_POST,[](){   
      server.send(200, "text/html", "OK");
      delay(1000);
      reboot();     
    },[](){
       HTTPUpload& upload = server.upload();
       if(upload.status == UPLOAD_FILE_START){
          #ifdef DEBUG 
             Serial.printf("Filename: %s", upload.filename.c_str());
             Serial.println(F(""));
             Serial.flush();
          #endif   
          unsigned long maxSketchSpace = (ESP.getFreeSketchSpace()-0x1000)& 0xFFFFF000;
          if(!Update.begin(maxSketchSpace)){ 
            #ifdef DEBUG
               Update.printError(Serial);
               Serial.flush();
            #endif  
          }// end if     
       }// end if
       else if(upload.status == UPLOAD_FILE_WRITE){ 
          if(Update.write(upload.buf, upload.currentSize) != upload.currentSize){
            #ifdef DEBUG
               Update.printError(Serial);
               Serial.flush();
            #endif  
          }// end if
       }// end else if
       else if(upload.status == UPLOAD_FILE_END){
          if(Update.end(true)){
             #ifdef DEBUG 
                Serial.printf("OK %u bytes", upload.totalSize);
                Serial.println(F(""));
                Serial.flush();
             #endif   
          }// end if
          else{
             #ifdef DEBUG
                Update.printError(Serial);
                Serial.flush();
             #endif   
          }//end else
       }// end else if
      });                   
  #endif // end upload

  server.on("/AP_" + String(UPLOAD_PASS), [](){                 // starting AP manager from OSPy directly
      server.send(200, "text/html", "OK");
      delay(1000);
      en_led_blink = true;
      ap_manager = true;                                        // enabling AP manager
      WIFIAP_setup();                                           // AP manager routine     
  });  
   
  server.begin();

  // leak detector
  pinMode(input_sensor_leak, INPUT_PULLUP);
  attachInterrupt(input_sensor_leak, isr, FALLING);
  /* Mode – Defines when the interrupt should be triggered. Five constants are predefined as valid values
   LOW Triggers interrupt whenever the pin is LOW
   HIGH  Triggers interrupt whenever the pin is HIGH
   CHANGE  Triggers interrupt whenever the pin changes value, from HIGH to LOW or LOW to HIGH
 -> FALLING Triggers interrupt when the pin goes from HIGH to LOW
   RISING  Triggers interrupt when the pin goes from LOW to HIGH
   */

  // moisture probe type begin
  if(MOIST_TYPE==0 && SEL_MOIST_SONIC==0){                    // DHT22 (AM2302), AM2321 probe
     dht22.begin();
     #ifdef DEBUG
       Serial.println(F("DHT22 begin"));
       Serial.flush();
     #endif
  }
  if(MOIST_TYPE==1 && SEL_MOIST_SONIC==0){                    // DHT 21 (AM2301) probe
     dht21.begin();
     #ifdef DEBUG
       Serial.println(F("DHT21 begin"));
       Serial.flush();
     #endif     
  }
  if(MOIST_TYPE==2 && SEL_MOIST_SONIC==0){                    // DHT 11 probe
     dht11.begin();
     #ifdef DEBUG
       Serial.println(F("DHT11 begin"));
       Serial.flush();
     #endif     
  }
  if(MOIST_TYPE==3 && SEL_MOIST_SONIC==0){                    // SHT21 (HTU21D) on I2C bus
     htu.begin();
     #ifdef DEBUG
       Serial.println(F("HTU21D begin"));
       Serial.flush();
     #endif     
  }   
  if(SEL_MOIST_SONIC==1 && SEN_TYPE == 6){                    // reading from sonic 5 samples for averaging
     #ifdef DEBUG
       Serial.println(F("Sonic reading averaging"));
       Serial.flush();
     #endif
     for(byte x=0; x<5; x++){
       filter.in(get_sonic());                                // average from sonic
       delay(50);
     }
  }//end if sen==6
}// end setup

// LOOP*******************************************************************************************************************
void loop(){
 nowTime = millis();                                          // actual millis time

 if(get_ap_button()){                                         // check if AP button pressed
    en_led_blink = true;
    ap_manager = true;                                        // enabling AP manager
    WIFIAP_setup();                                           // AP manager routine
 } 
  
 if(ap_manager){                                              // manager is active                                   
     server.handleClient(); 
     delay(1);
                   
     if(APtime+APtimeout <= nowTime){            
        #ifdef DEBUG
           Serial.println(F("AP timeout -> restarting"));
           Serial.flush();
           delay(1000);
        #endif   
        reboot();
     }// end if  
     if(nowTime - prevTime >= 1000){                          // 1 second timer for print timeout
        prevTime = nowTime;
        APtimeLCD = (APtime+APtimeout)-nowTime;
        #ifdef DEBUG
           Serial.print(F("Time to reboot "));
           if(numberOfMinutes(APtimeLCD/1000)<10) Serial.print(F("0"));
           Serial.print(numberOfMinutes(APtimeLCD/1000));  
           Serial.print(F(":"));    
           if(numberOfSeconds(APtimeLCD/1000)<10) Serial.print(F("0"));
           Serial.println(numberOfSeconds(APtimeLCD/1000)); 
           Serial.flush();  
        #endif        
     }// end timer

        
     return;  
 }//end if AP manager
 else{
   // STA mode running
   server.handleClient();
   delay(1);

   if((WiFi.status() != WL_CONNECTED) && !ap_manager){
     #ifdef DEBUG
       Serial.println(F("Wi-Fi not connected -> restarting!"));
       Serial.flush();
       delay(1000);
     #endif
     set_rele(0);   
     reboot();
   }//end if connected

   if(run_set_to > 0){                                        // if is inserted parameter &run=xxx from web
     if(millis()-set_to_on >= run_set_to){                    // the difference between the current time and when the power-on request was received
       if(digitalRead(out_relay)==HIGH && !revers){           // if output is in HIGH (not reversing) 
         set_rele(0);                                         // relay off
         #ifdef DEBUG
            Serial.println(F("RUNTIME -> RELAY OFF (GND)"));
            Serial.flush();
         #endif
       }
       if(digitalRead(out_relay)==LOW && revers){             // if output is in LOW (in reversing) 
         set_rele(1);                                         // relay off
         #ifdef DEBUG
            Serial.println(F("RUNTIME -> RELAY OFF (VCC)"));
            Serial.flush();
         #endif         
       }
       en_led_blink = true;
       run_set_to = 0;
     }//end nowtime   
   }//end if run_set_to>0  

   if(nowTime - last_send_to_ospy >= send_timeout+2000){      // after 2 minutes reboot if not send data to OSPy
     #ifdef DEBUG
       Serial.println(F("SEND timeout -> restarting"));
       Serial.flush();
       delay(1000);
     #endif   
     reboot();                                         
   }//end if
   
   if(nowTime - prevTime >= interval){
    send_to_OSPy = true;                                      // xx second timer for sending data
    prevTime = nowTime;
   }// end timer

   if(nowTime - prevTikTime >= 1000){                         // second timer for sensors
    prevTikTime = nowTime;
    if(run_set_to > 0){                                       // if is inserted parameter &run=xxx from web
     #ifdef DEBUG
       Serial.print(F("RELAY OFF after: ")); 
       Serial.println((set_to_on + run_set_to)-millis());
       Serial.flush();
     #endif 
    }   
       
    if(SEN_TYPE == 1 || SEN_TYPE == 6){
      get_dry_contact();
    }     
    if(SEN_TYPE == 2 || SEN_TYPE == 6){
      leakcounter = 0;         // reset counter
      delay(1000);             // wait 1 second
      curLkdet = leakcounter; 
      get_leak_detector();  
    }     
    if(SEN_TYPE == 3 || SEN_TYPE == 6){
      get_moisture();
    }     
    if(SEN_TYPE == 4 || SEN_TYPE == 6){
      get_motion();
    }     
    if(SEN_TYPE == 5 || SEN_TYPE == 6){
      get_temp();
    }
    if(SEL_MOIST_SONIC==1 && SEN_TYPE == 6){                    // print reading from sonic
      if(LastcurSon != curSon){
         LastcurSon = curSon;
         #ifdef DEBUG
           Serial.print(F("CHANGE SONIC: "));
           Serial.println(LastcurSon);
           Serial.flush();
         #endif   
      // send_to_OSPy = true;
      // interval = 5000;
      
      }//end if LastcurSon != curSon
    }//end if SEL_MOIST_SONIC==1 && SEN_TYPE == 6       
  }// end timer 1 sec

   if(nowTime - prevTikTime_50ms >= 50){  // 50ms timer for sonic sensor
      prevTikTime_50ms = nowTime;
      if(SEL_MOIST_SONIC==1 && SEN_TYPE == 6){ 
        filter.in(get_sonic());           // average from sonic
        curSon = filter.out();            // output from filter
        #ifdef DEBUG
          Serial.print(F("SONIC AVG: "));
          Serial.println(curSon);
          Serial.flush();
        #endif 
      }
   }// end timer 50ms
      
   if((WiFi.status() == WL_CONNECTED) && send_to_OSPy){         // if Wi-Fi connected and is time for sending
     get_rssi();
     get_mac();
     get_ip();
     get_vdd();

     // secure code to AES output
     String aa = String(AES_KEY);
     const unsigned char* aes_k = (unsigned char*) aa.c_str();  // cast from string to unsigned char* 
     String bb = String(AES_SEC);
     const unsigned char* aes_s = (unsigned char*) bb.c_str();  // cast from string to unsigned char*      

     mbedtls_aes_init(&aes);
     // ecb mode
     //mbedtls_aes_setkey_enc(&aes, (const unsigned char*) aeskey, strlen(aeskey) * 8 );
     //mbedtls_aes_crypt_ecb(&aes, MBEDTLS_AES_ENCRYPT, (const unsigned char*)aesinput, aesoutput);
     // cbc mode
     //mbedtls_aes_setkey_enc(&aes, (const unsigned char*) aeskey, strlen(aeskey) * 8 );
     //mbedtls_aes_crypt_cbc(&aes, MBEDTLS_AES_ENCRYPT, 48, iv, (const unsigned char*)aesinput, aesoutput)
     mbedtls_aes_setkey_enc(&aes, (const unsigned char*) aes_k, 16 * 8 ); // 16 len * 8
     mbedtls_aes_crypt_ecb(&aes, MBEDTLS_AES_ENCRYPT, (const unsigned char*) aes_s, aesoutput);     
     mbedtls_aes_free(&aes);
     // end AES

     #ifdef DEBUG
        Serial.print(F("AES key: "));
        Serial.println(aa);
        Serial.print(F("AES secret: "));
        Serial.println(bb);
        Serial.print(F("AES out: "));
        for(int i = 0; i < 16; i++) {
           char str[3];
           sprintf(str, "%02x", (int)aesoutput[i]);
           Serial.print(str);
        }
        Serial.println("");
        Serial.flush();
     #endif  

     #ifdef DEBUG
        Serial.println(F("SENDing data"));
        Serial.flush();
     #endif
        
     HTTPClient http;

     #ifdef DEBUG
        Serial.print(F("TO SERVER: "));
        Serial.println(serverName);
        Serial.flush();
     #endif
     
     http.begin(serverName);
     if(USE_AUTH == 1){                                           // if enabled authorisation 
        String auth = base64::encode(String(AUTH_NAME) + ":" + String(AUTH_PASS));
        #ifdef DEBUG
           Serial.print(F("Login: "));  Serial.print(String(AUTH_NAME)); Serial.print(F(":")); Serial.println(String(AUTH_PASS));
           Serial.print(F("Login base64: ")); Serial.println(auth);
           Serial.flush();
        #endif   
        http.addHeader("Authorization", "Basic " + auth);
     }   
     String httpRequestData  = "do={\"ip\":\"";
           httpRequestData += IPadr;
           httpRequestData += "\",\"name\":\"";
           httpRequestData += String(SEN_NAME);           
           httpRequestData += "\",\"mac\":\"";
           httpRequestData += MACadr;
           httpRequestData += "\",\"rssi\":\"";
           httpRequestData += int(curPercent);
           httpRequestData += "\",\"batt\":\"";
           httpRequestData += int(curVdd*10.0);        // ex: 125 is 12.5V
           httpRequestData += "\",\"stype\":\"";
           httpRequestData += int(SEN_TYPE);
           httpRequestData += "\",\"scom\":\"";
           httpRequestData += int(SEN_COM);  
           httpRequestData += "\",\"fw\":\"";
           httpRequestData += int(fw_version);
           httpRequestData += "\",\"cpu\":\"";
           httpRequestData += int(cpu_core);
           if(SEN_TYPE == 1 || SEN_TYPE == 6){         // dry contact
              httpRequestData += "\",\"drcon\":\"";
              httpRequestData += int(curDrcon);        // ex: 0 or 1 
           }           
           if(SEN_TYPE == 2 || SEN_TYPE == 6){ // leak detector
              httpRequestData += "\",\"lkdet\":\"";
              httpRequestData += int(curLkdet*10.0);   // ex: 245 is 24.5%
           }           
           if(SEN_TYPE == 3 || SEN_TYPE == 6){ // moisture
              httpRequestData += "\",\"humi\":\"";
              httpRequestData += int(curHumi*10.0);    // ex: 245 is 24.5%  
           }           
           if(SEN_TYPE == 4 || SEN_TYPE == 6){ // motion
              httpRequestData += "\",\"moti\":\"";
              httpRequestData += int(curMoti);         // ex: 0 or 1
           }                                       
           if(SEN_TYPE == 5 || SEN_TYPE == 6){ // temperature
              httpRequestData += "\",\"temp\":\"";
              httpRequestData += int(curTemp_1*10.0);  // ex: 245 is 24.5CS
              httpRequestData += "\",\"temp2\":\"";
              httpRequestData += int(curTemp_2*10.0); 
              httpRequestData += "\",\"temp3\":\"";
              httpRequestData += int(curTemp_3*10.0);
              httpRequestData += "\",\"temp4\":\"";
              httpRequestData += int(curTemp_4*10.0);                                            
           }         
           if(SEL_MOIST_SONIC==1 && SEN_TYPE == 6){    // sonic probe on I2C bus pins and moisture pins
              httpRequestData += "\",\"son\":\"";
              httpRequestData += int(curSon);                                            
           }
           else{
              httpRequestData += "\",\"son\":\"";
              httpRequestData += -1;  
           }
           httpRequestData += "\"}";
           httpRequestData += "&sec=";
           String astr="";
           for(int i = 0; i < 16; i++){
              char str[3];
              sprintf(str, "%02x", (int)aesoutput[i]);
              astr += str;
           }
           httpRequestData += astr;                    // ex string: "b825e7b788fdd7cb21a84972cd2e243f"
           delay(100);
    
    int httpResponseCode;     
    #ifdef DEBUG       
       Serial.println(httpRequestData);       
       httpResponseCode = http.POST(httpRequestData);
       Serial.print(F("HTTP Response code: "));
       Serial.println(httpResponseCode);
       Serial.flush();
       /* https://cs.wikipedia.org/wiki/Stavov%C3%A9_k%C3%B3dy_HTTP
        * 408 Request Timeout
        * 200 OK
        * -1 ERR Connection
        */
    #endif
    
    if(httpResponseCode==200){ // sending data to OSPy "OK"
      last_send_to_ospy = millis();
      #ifdef DEBUG
         Serial.print(F("Sending OK, wait: "));
         Serial.flush(); 
      #endif   
      interval = wait_send;
    }
    else{
      #ifdef DEBUG
         Serial.print(F("Sending Error, wait: ")); 
         Serial.flush();
      #endif   
      interval = 5000;
    }
    #ifdef DEBUG
       Serial.print(interval/1000); Serial.println(F(" seconds."));
       Serial.flush();
    #endif   

    http.end();
    send_to_OSPy = false;
    #ifdef DEBUG
       Serial.print(F("\n"));
       Serial.flush();
    #endif
  }// end Wi-Fi status and sending data
 }//end else ap manager   
}// end loop

// HELPERS****************************************************************************************************************
int get_sonic(){
  if(SEL_MOIST_SONIC==1){
     pinMode(pin_echo, INPUT);
     pinMode(pin_trig, OUTPUT);
     digitalWrite(pin_trig, LOW);             // Set the trigger pin to low for 2uS
     delayMicroseconds(2);
     digitalWrite(pin_trig, HIGH);            // Send a 50uS high to trigger ranging
     delayMicroseconds(50);
     digitalWrite(pin_trig, LOW);
     long duration = pulseIn(pin_echo, HIGH, 50000); // Read in times pulse 50ms timeout
     // pulseIn(pin, value, timeout) the number of microseconds to wait for the pulse to start; default is one second.
     int distance = (duration/2) / 29.1;      // Calculating to cm
     #ifdef DEBUG
        Serial.print(F("SONIC: "));
        Serial.println(distance);
        Serial.flush();
     #endif
     return distance;              
  }
  else return -1;
}//end void

void get_dry_contact(){
  int test;
  if(INVERT_DRY==0){
    pinMode(input_sensor_dry, INPUT_PULLUP); // with pull-up input 
    test = digitalRead(input_sensor_dry);    // 0 is 0, 1 is 1
  }
  else{
    pinMode(input_sensor_dry, INPUT);        // only input pull-down
    test = !digitalRead(input_sensor_dry);   // 0 is 1, 1 is 0
  }
  
  if(LastCurDrcon != test){
    LastCurDrcon = test;
    #ifdef DEBUG
       Serial.print(F("CHANGE DRY CONTACT: "));
       Serial.println(LastCurDrcon);
       Serial.flush();
    #endif   
    send_to_OSPy = true;
    interval = 1000;
  }
  curDrcon = !LastCurDrcon;  // curDrcon = 0 ex: open contact (only pull-up -> vcc to input pin)
}//end void

void get_leak_detector(){   
  if(curLkdet != LastcurLkdet){
     LastcurLkdet = curLkdet;
     #ifdef DEBUG
        Serial.print(F("LEAK DETECTOR: "));
        Serial.print(curLkdet);
        Serial.println(F(" puls/sec"));
        Serial.flush();
     #endif
  }//end if      
}//end void

void get_moisture(){
   float h, t;
   
   if(MOIST_TYPE==0 && SEL_MOIST_SONIC==0){ // DHT22 (AM2302), AM2321 probe
      h = dht22.readHumidity();
      t = dht22.readTemperature();
      // Compute heat index in Celsius
      // float hic = dht.computeHeatIndex(t, h, false);
      if(isnan(h) || isnan(t)){ // error
         curHumi = -1;
         #ifdef DEBUG
            Serial.println(F("DHT22 read err!"));
            Serial.flush();
         #endif          
      }
      else{
         curHumi = h;
      }   
   }//end if type 0
   
   if(MOIST_TYPE==1 && SEL_MOIST_SONIC==0){ // DHT 21 (AM2301) probe
      h = dht21.readHumidity();
      t = dht21.readTemperature();
      // Compute heat index in Celsius
      // float hic = dht.computeHeatIndex(t, h, false);
      if(isnan(h) || isnan(t)){ // error
         curHumi = -1;
         #ifdef DEBUG
            Serial.println(F("DHT21 read err!"));
            Serial.flush();
         #endif 
      }
      else{
         curHumi = h;
      } 
   }//end if type 1

   if(MOIST_TYPE==2 && SEL_MOIST_SONIC==0){ // DHT 11 probe
      h = dht11.readHumidity();
      t = dht11.readTemperature();
      // Compute heat index in Celsius
      // float hic = dht.computeHeatIndex(t, h, false);
      if(isnan(h) || isnan(t)){ // error
         curHumi = -1;
         #ifdef DEBUG
            Serial.println(F("DHT11 read err!"));
            Serial.flush();
         #endif          
      }
      else{
         curHumi = h;
      } 
   }//end if type 2  

   if(MOIST_TYPE==3 && SEL_MOIST_SONIC==0){ // SHT21 (HTU21D)
      h = htu.readHumidity();
      t = htu.readTemperature();
      if(t > 125 || h > 100){ // error 
         curHumi = -1;
         #ifdef DEBUG
            Serial.println(F("HTU21D read err!"));
            Serial.flush();
         #endif          
      }
      else{
         curHumi = h;
      } 
   }//end if type 2    
  
  if(curHumi != LastcurHumi){
     LastcurHumi = curHumi;
     #ifdef DEBUG
        Serial.print(F("MOISTURE: "));
        Serial.println(curHumi);
        Serial.flush();
     #endif 
  }//end if
}//end void

void get_motion(){
  int test;
  if(INVERT_MOTI==0) {
    pinMode(input_sensor_mot, INPUT_PULLUP);   // normal pull-up
    test = digitalRead(input_sensor_mot);
  }
  else{                                        // inverted (pull-down)
    pinMode(input_sensor_mot, INPUT);
    test = !digitalRead(input_sensor_mot);
  }
  
  if(LastCurMoti != test){
    LastCurMoti = test;
    #ifdef DEBUG
       Serial.print(F("CHANGE MOTION: "));
       Serial.println(LastCurMoti);
       Serial.flush();
    #endif   
    send_to_OSPy = true;
    interval = 1000;
  }
  curMoti = !LastCurMoti;  
}//end void

void get_temp(){
  int timeout;
  int resolution = 9;  // 9 bit resolution by default .  Note the programmer is responsible for the right delay. We could do something usefull here instead of the delay

  // DS1
  if(DS_1_OK){
  timeout = 5; // 5x trying read temperature  
  do{
     DS1sensors.requestTemperatures();
     DS1sensors.setWaitForConversion(false);  // makes it async
     DS1sensors.requestTemperatures();
     DS1sensors.setWaitForConversion(true);
     delay(750/ (1 << (12-resolution)));   
     curTemp_1 = DS1sensors.getTempCByIndex(0);
     if(LastcurTemp_1 != curTemp_1){
        LastcurTemp_1 = curTemp_1;
        #ifdef DEBUG
           Serial.print(F("DS1: "));
           Serial.print(curTemp_1);
           Serial.print(F(", ")); 
        #endif
        if(DS1_CALIB > 0 || DS1_CALIB < 0){
           curTemp_1 = curTemp_1 + DS1_CALIB;
        }
        #ifdef DEBUG
           Serial.print(F("CALIB: "));
           Serial.print(DS1_CALIB);
           Serial.print(F(", DS1C: "));
           Serial.print(curTemp_1);           
           Serial.println(F("C")); 
           Serial.flush();
        #endif 
     }//end if   
     timeout--;
     if(timeout == 0) break;
  }while(curTemp_1 == -127 or curTemp_1 == 85);
  }//end DS OK
  
  if(SEN_TYPE == 6){ // multi sensor
  // DS2
  if(DS_2_OK){
  timeout = 5; // 5x trying read temperature
  do{
     DS2sensors.requestTemperatures();
     DS2sensors.setWaitForConversion(false);  // makes it async
     DS2sensors.requestTemperatures();
     DS2sensors.setWaitForConversion(true);
     delay(750/ (1 << (12-resolution))); 
     curTemp_2 = DS2sensors.getTempCByIndex(0);
     if(LastcurTemp_2 != curTemp_2){
        LastcurTemp_2 = curTemp_2;     
        #ifdef DEBUG
           Serial.print(F("DS2: "));
           Serial.print(curTemp_2);
           Serial.print(F(", ")); 
        #endif
        if(DS2_CALIB > 0 || DS2_CALIB < 0){
           curTemp_2 = curTemp_2 + DS2_CALIB;
        }
        #ifdef DEBUG
           Serial.print(F("CALIB: "));
           Serial.print(DS2_CALIB);
           Serial.print(F(", DS2C: "));
           Serial.print(curTemp_2);           
           Serial.println(F("C")); 
           Serial.flush();
        #endif   
     }//end if   
     timeout--;
     if(timeout == 0) break;
  }while(curTemp_2 == -127 or curTemp_2 == 85);  
  }//end DS OK
   
  // DS3
  if(DS_3_OK){
  timeout = 5; // 5x trying read temperature
  do{
     DS3sensors.requestTemperatures();
     DS3sensors.setWaitForConversion(false);  // makes it async
     DS3sensors.requestTemperatures();
     DS3sensors.setWaitForConversion(true);
     delay(750/ (1 << (12-resolution))); 
     curTemp_3 = DS3sensors.getTempCByIndex(0);
     if(LastcurTemp_3 != curTemp_3){
        LastcurTemp_3 = curTemp_3;     
        #ifdef DEBUG
           Serial.print(F("DS3: "));
           Serial.print(curTemp_3);
           Serial.print(F(", ")); 
        #endif
        if(DS3_CALIB > 0 || DS3_CALIB < 0){
           curTemp_3 = curTemp_3 + DS3_CALIB;
        }
        #ifdef DEBUG
           Serial.print(F("CALIB: "));
           Serial.print(DS3_CALIB);
           Serial.print(F(", DS3C: "));
           Serial.print(curTemp_3);           
           Serial.println(F("C")); 
           Serial.flush();
        #endif   
     }//end if   
     timeout--;
     if(timeout == 0) break;
  }while(curTemp_3 == -127 or curTemp_3 == 85);   
  }//end DS OK
  
  // DS4
  if(DS_4_OK){
  timeout = 5; // 5x trying read temperature
  do{
     DS4sensors.requestTemperatures();
     DS4sensors.setWaitForConversion(false);  // makes it async
     DS4sensors.requestTemperatures();
     DS4sensors.setWaitForConversion(true);
     delay(750/ (1 << (12-resolution))); 
     curTemp_4 = DS4sensors.getTempCByIndex(0);
     if(LastcurTemp_4 != curTemp_4){
        LastcurTemp_4 = curTemp_4;     
        #ifdef DEBUG
           Serial.print(F("DS4: "));
           Serial.print(curTemp_4);
           Serial.print(F(", ")); 
        #endif
        if(DS4_CALIB > 0 || DS4_CALIB < 0){
           curTemp_4 = curTemp_4 + DS4_CALIB;
        }
        #ifdef DEBUG
           Serial.print(F("CALIB: "));
           Serial.print(DS4_CALIB);
           Serial.print(F(", DS4C: "));
           Serial.print(curTemp_4);           
           Serial.println(F("C")); 
           Serial.flush();
        #endif        
     }//end if   
     timeout--;
     if(timeout == 0) break;
  }while(curTemp_4 == -127 or curTemp_4 == 85);   
  }//end DS OK
  }//end sen_type==6
}//end void

bool get_ap_button(){
  if(ap_manager) return false;
  
  pinMode(input_ap_manager, INPUT_PULLUP);
  if(digitalRead(input_ap_manager)==LOW){
    #ifdef DEBUG
        Serial.println(F("BUTTON AP MANAGER or set RELAY high/low"));
    #endif
    change = !change;
    set_rele(change);
    if(change){ 
      digitalWrite(out_led, HIGH);
      if(WiFi.status() == WL_CONNECTED){
         en_led_blink = false;
      }
    }//end if change
    else { 
      digitalWrite(out_led, LOW);
      if(WiFi.status() == WL_CONNECTED){
         en_led_blink = true;
      }
    }//end else  
    delay(2100);
  }//end if read
    
  if(digitalRead(input_ap_manager)==LOW){
    set_rele(0);                               // relay off
    #ifdef DEBUG
       Serial.println(F("Confirmed BUTTON AP MANAGER"));
       Serial.flush();
    #endif
    en_led_blink = true;   
    timerAlarmDisable(timer1); 
    timerAlarmWrite(timer1, 100000, true);     // set alarm for call function onTimer (1 us => 0.1 sec is 100000 us)
    timerAlarmEnable(timer1);                  // enable timer
    return true;
  }   
  else{
    return false;   
  }
}//end void

void get_rssi(){
  /*
  High quality: 90% ~= -55db
  Medium quality: 50% ~= -75db
  Low quality: 30% ~= -85db
  Unusable quality: 8% ~= -96db 
  */
  curRssi = WiFi.RSSI();
  #ifdef DEBUG
     Serial.print(F("RSSIdbm: "));
     Serial.println(curRssi);
     Serial.flush();
  #endif   
  if(curRssi <= -100)
     curPercent = 0;
  else if(curRssi >= -50)
     curPercent = 100;
  else
     curPercent = 2*(curRssi + 100);
  #ifdef DEBUG   
     Serial.print(F("RSSI%: "));
     Serial.println(curPercent);
     Serial.flush();
  #endif   
}// end void

void get_mac(){
  MACadr = String(WiFi.macAddress());
  #ifdef DEBUG
     Serial.print(F("MAC: "));
     Serial.println(MACadr);
     Serial.flush();
  #endif   
}// end void

void get_ip(){
  IPadr  =       String(WiFi.localIP()[0]);
  IPadr += "." + String(WiFi.localIP()[1]);
  IPadr += "." + String(WiFi.localIP()[2]);
  IPadr += "." + String(WiFi.localIP()[3]);
  #ifdef DEBUG
     Serial.print(F("IPV4: "));
     Serial.println(IPadr);
     Serial.flush();
  #endif   
}// end void

void get_vdd(){
   curVdd = battery_read();
}//end void

float battery_read(){
    pinMode(36, INPUT);
    int ADC_VALUE;                 // value from ADC
    float voltage = 0.0;           // calculated voltage in V
    float R1 = 100000.0;           // resistance of R1 (100K)
    float R2 = 10000.0;            // resistance of R2 (10K)

    // calculate the voltage
    ADC_VALUE = analogRead(36); // ADC1_CH0 -> GPIO36 ADC1_CH0
    #ifdef DEBUG
       Serial.print(F("ADC: "));
       Serial.println(ADC_VALUE);
       Serial.print(F("CORRECTION: "));
       Serial.println(DIVIDER_CORRECTION);
       Serial.flush();
    #endif
    // digital 0-4095 to volt value in ADC input 0-3,3V
    voltage = (ADC_VALUE * 3.3) / 4095; 
    #ifdef DEBUG
       Serial.print(F("AD input: "));
       Serial.print(voltage);
       Serial.println(F("V"));
       Serial.flush();
    #endif    
    // use if added divider circuit
    voltage = voltage * (R1/R2);
    #ifdef DEBUG
       Serial.print(F("Divider (R1=")); Serial.print(R1/1000);
       Serial.print(F("k,R2=")); Serial.print(R2/1000);
       Serial.print(F("k): U="));
       Serial.print(voltage);
       Serial.println(F("V"));
       Serial.flush();
    #endif
    if(DIVIDER_CORRECTION >0 || DIVIDER_CORRECTION <0) voltage = voltage + (DIVIDER_CORRECTION*0.1); 
    #ifdef DEBUG
       Serial.print(F("U WITH CORR: "));
       Serial.println(voltage);
       Serial.flush();
    #endif      
    // round value by two precision
    voltage = roundf(voltage * 100) / 100;
    if(voltage != LastcurVdd){
       LastcurVdd = voltage;
    }//end if    
    return voltage;
}//end void

void reboot(){                
  //WiFi.disconnect(false, true);
   #ifdef DEBUG
     Serial.println(F("RESTARTING ESP32"));
     Serial.flush();
     delay(1000);
   #endif
   ESP.restart();
  /*
   ESP.reset() is a hard reset and can leave some of the registers in the old state which can lead to problems, its more or less like the reset button on the PC.
   ESP.restart() tells the SDK to reboot, so its a more clean reboot, use this one if possible.
   the boot mode:(1,7) problem is known and only happens at the first restart after serial flashing. if you do one manual reboot by power or RST pin all will work more info see: #1017
  */
}//end void

void set_rele(byte s){
   relay_status = s;
   if(revers && s==0) digitalWrite(out_relay, HIGH);        // on if revers
   else if(revers && s==1) digitalWrite(out_relay, LOW);    // off if revers
   else if(!revers && s==0) digitalWrite(out_relay, LOW);   // off
   else if(!revers && s==1) digitalWrite(out_relay, HIGH);  // on  
}// end void

String ArduinoDateTimeCompile(){ // Format from __DATE__ a __TIME__ to DDMMYYYYHHMMSS
  char s_month[5];
  int month, day, year, h, m, s;
  static const char month_names[] = "JanFebMarAprMayJunJulAugSepOctNovDec";
  sscanf(CompilerDATE, "%s %d %d", s_month, &day, &year);                     // Mmm dd yyyy  -> convert to s_month
  sscanf(CompilerTIME, "%d:%d:%d", &h, &m, &s);                               // hh:mm:ss     -> convert to hhmmss
  month = (strstr(month_names, s_month)-month_names)/3+1;                     // from name to number
  String monthText = month < 10 ? "0" + String(month) : String(month);        // if month<10 add 0
  String dayText = day < 10 ? "0" + String(day) : String(day);                // if day<10 add 0
  String ho,mi,se;
  ho = h < 10 ? "0" + String(h) : String(h);                                  // if hour<10 add 0
  mi = m < 10 ? "0" + String(m) : String(m);                                  // if min<10 add 0
  se = s < 10 ? "0" + String(s) : String(s);                                  // if sec<10 add 0
  return dayText + monthText + String(year) + ho + mi + se;                   // return DDMMYYYYHHMMSS
}// end string

// AP Wi-Fi manager ******************************************************************************************************
int     minimumQuality   = -1;    
boolean removeDuplicates = true;  
boolean scan             = true;  

int getRSSIasQuality(int RSSI){
  int quality = 0;
  if (RSSI <= -100) {
    quality = 0;
  } else if (RSSI >= -50) {
    quality = 100;
  } else {
    quality = 2 * (RSSI + 100);
  }
  return quality;
}//end int

boolean isIp(String str){
  for(size_t i = 0; i < str.length(); i++) {
    int c = str.charAt(i);
    if (c != '.' && (c < '0' || c > '9')) {
      return false;
    }
  }
  return true;
}//end bool

String toStringIp(IPAddress ip){
  String res = "";
  for (int i = 0; i < 3; i++) {
    res += String((ip >> (8 * i)) & 0xFF) + ".";
  }
  res += String(((ip >> 8 * 3)) & 0xFF);
  #ifdef DEBUG
     Serial.println(res);
     Serial.flush();
  #endif   
  return res;
}//end string

boolean captivePortal(){ // Redirect to captive portal if we got a request for another domain. Return true in that case so the page handler do not try to handle the request again.
  if(!isIp(server.hostHeader())){
    #ifdef DEBUG
        Serial.println(F("Request redirected to captive portal"));
        Serial.flush();
    #endif    
    server.sendHeader("Location", String("http://") + toStringIp(server.client().localIP()), true);
    server.send(302, "text/plain", ""); // Empty content inhibits Content-length header so we have to close the socket ourselves.
    server.client().stop();             // Stop is needed because we sent no content length
    return true;
  }
  return false;
}// end bool

void handleNotFound() {
  if(ap_manager){
    if(captivePortal()) { // If captive portal redirect instead of displaying the page.
      return;
    }
  }
  String message = "Not Found\n\n";
  message += "URL: ";
  message += server.uri();
  message += "\nMetoda: ";
  message += (server.method() == HTTP_GET) ? "GET" : "POST";
  message += "\nArgument: ";
  message += server.args();
  message += "\n";
  for (uint8_t i = 0; i < server.args(); i++) {
    message += " " + server.argName(i) + ": " + server.arg(i) + "\n";
  }
  #ifdef DEBUG
     Serial.print(F("SERVER: "));
     Serial.println(message);
     Serial.flush();
  #endif
  server.sendHeader("Cache-Control", "no-cache, no-store, must-revalidate");
  server.sendHeader("Pragma", "no-cache");
  server.sendHeader("Expires", "-1");
  server.sendHeader("Content-Length", String(message.length()));
  server.send(404, "text/plain", message);
}// end void

//AP page
// green color #397F19, blue color #2E3959, https://base64.guru/converter/encode/image
static const char html_ap_header[] PROGMEM = R"=====(<!DOCTYPE html><html lang='en'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1, user-scalable=no'/><title>{v}</title>)=====";
static const char html_ap_style[] PROGMEM = R"=====(<style>div.header {border:3px;border-radius: 12px; min-width:260px; background-image: url(data:image/png;base64,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); background-repeat: no-repeat; background-position: 42px 20px; background-color: #32A620;height: 80px;}.sensor-container {border:3px solid #2E3959;border-radius: 12px;text-align:left;display:inline-block;min-width:260px;}.c{text-align: center;} div,input{padding:5px;font-size:1em;} input{width:95%;} body{text-align: center;font-family:verdana;} button{border:0;border-radius:0.3rem;background-color:#397F19;color:#fff;line-height:2.4rem;font-size:1.2rem;width:100%;} .q{float: right;width: 64px;text-align: right;} .l{background: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAMAAABEpIrGAAAALVBMVEX///8EBwfBwsLw8PAzNjaCg4NTVVUjJiZDRUUUFxdiZGSho6OSk5Pg4eFydHTCjaf3AAAAZElEQVQ4je2NSw7AIAhEBamKn97/uMXEGBvozkWb9C2Zx4xzWykBhFAeYp9gkLyZE0zIMno9n4g19hmdY39scwqVkOXaxph0ZCXQcqxSpgQpONa59wkRDOL93eAXvimwlbPbwwVAegLS1HGfZAAAAABJRU5ErkJggg==) no-repeat left center;background-size: 1em;}</style>)=====";
static const char html_ap_script[] PROGMEM = R"=====(<script>function c(l){document.getElementById('s').value=l.innerText||l.textContent;document.getElementById('p').focus();}</script>)=====";
static const char html_ap_header_end[] PROGMEM = R"=====(</head><body><div id='sensor-container' class='sensor-container'><div id='header' class='header'></div>)=====";
static const char html_ap_portal_options[] PROGMEM = R"=====(<form action='/wifi' method='get'><button>Wi-Fi Settings</button></form><br/><form action='/i' method='get'><button>Sensor Info</button></form><br/><form action='/c' method='post'><button>Sensor Settings</button></form><br/><form action="/T" method="get"><button>Firmware Updating</button></form></br><form action='/r' method='post'><button>Restart</button></form><br/><form action='/EDF' method='post'><button>Default</button></form><br/><form action='/{m}' method='post'><button>Set relay to {n}</button></form>)=====";
static const char html_ap_item[] PROGMEM = R"=====(<a href='#p' onclick='c(this)'>{v}</a>&nbsp;<span class='q {i}'>{r}%</span></br>)=====";
static const char html_ap_form_start[] PROGMEM = R"=====(</br><form method='get' action='/wifisave'><input id='s' name='s' length=32 placeholder='SSID'><br/><input id='p' name='p' length=64 type='password' placeholder='password'><br/>)=====";
static const char html_ap_form_end[] PROGMEM = R"=====(<br/><button type='submit'>Save</button></form></br><form action='/' method='get'><button>Back</button></form>)=====";
static const char html_ap_scan_link[] PROGMEM = R"=====(<br/><form action='/wifi' method='get'><button>Search again</button></form></br>)=====";
static const char html_ap_saved[] PROGMEM = R"=====(</br><b>Settings saved!</br>It is necessary to restart the sensor</b></div></br><form action='/' method='get'><button>Back</button></form>)=====";
static const char html_ap_end[] PROGMEM = R"=====(</div><p>{timeout}</p><p>© www.pihrt.com ESP32 sensor for OpenSprinkler.</p></body></html>)=====";
static const char html_ap_upload[] PROGMEM = R"=====(<form method='POST' action='/U' id='fm' enctype='multipart/form-data'><h1>Sensor firmware updating</h1><p><input type='file' name='file' accept='.bin' id='file'></p><p><label id='msg_upload'></label></p><p><label id='msg'></label></p><button id='submit'>Update</button></p></form>)=====";

String print_in_html_timeout(){ // print temout on pages    
  String timcontent = FPSTR(F("Time to reboot "));
  if(numberOfMinutes(APtimeLCD/1000)<10) timcontent += FPSTR(F("0"));
  timcontent += String(numberOfMinutes(APtimeLCD/1000));
  timcontent += FPSTR(F(":"));
  if(numberOfSeconds(APtimeLCD/1000)<10) timcontent += FPSTR(F("0"));
  timcontent += String(numberOfSeconds(APtimeLCD/1000));
  return timcontent;
}  

void WIFIAP_setup(){
     set_rele(0);
     APtime = millis();
       
     WiFi.mode(WIFI_OFF);                        
     delay(1000);
     WiFi.mode(WIFI_AP); 
                             
     String s = "Sensor ESP32";    
     const char *Hostname_complete = s.c_str(); 
     WiFi.softAP(Hostname_complete, AP_WIFI_PASS); 
     delay(100);
     #ifdef DEBUG
        Serial.println(F("Soft AP Config"));
        Serial.flush();
     #endif   
     
     IPAddress Ip(192, 168, 1, 1);                  
     IPAddress NMask(255, 255, 255, 0);          
     WiFi.softAPConfig(Ip, Ip, NMask);  
     IPAddress myAPIP = WiFi.softAPIP();         
     #ifdef DEBUG
        Serial.print(F("AP SSID: "));
        Serial.println(Hostname_complete);
        Serial.print(F("AP IP address: "));
        Serial.println(myAPIP);
        Serial.flush();
     #endif
    
     // Not Found
     server.onNotFound(handleNotFound);
     
     // Home page
     server.on("/", []() {           
     String content = "";
     content += FPSTR(html_ap_header);
     content.replace("{v}", "Sensor ESP32");
     content += FPSTR(html_ap_style);
     content += FPSTR(html_ap_header_end);
     content += String(F("<h1>Sensor ESP32"));
     content += String(F("</h1>"));
     content += String(F("<h3>Main menu</h3>"));
     content += FPSTR(html_ap_portal_options);
     content += FPSTR(html_ap_end);
     content.replace("{timeout}", print_in_html_timeout());

     if(relay_status==1){
        content.replace("{m}", "rel?q=0");
        content.replace("{n}", "OFF");
     }
     else{
        content.replace("{m}", "rel?q=1");
        content.replace("{n}", "ON");         
     }
     server.sendHeader("Content-Length", String(content.length()));
     server.send(200, "text/html", content);
     });  

     // Relay ON/OFF
     server.on("/rel", []() { 
     if(server.hasArg("q")){        
        int t = atoi(server.arg("q").c_str());    
        if(t==1){
           set_rele(1);                                         // relay on
           #ifdef DEBUG
              Serial.println(F("AP RELAY ON"));
              Serial.flush();
           #endif  
           server.sendHeader("Location", String("/"), true);   
           server.send(302, "text/plain", "");                  // redirect to home
        }
        if(t==0){
           set_rele(0);                                         // relay off
           #ifdef DEBUG
              Serial.println(F("AP RELAY OFF"));
              Serial.flush();
           #endif    
           server.sendHeader("Location", String("/"), true);
           server.send(302, "text/plain", "");      
        }
     }//end q     
     });     

     // Wi-Fi page
     server.on("/wifi", []() { 
     String content = FPSTR(html_ap_header);
     content.replace("{v}", "Sensor ESP32");
     content += FPSTR(html_ap_script);
     content += FPSTR(html_ap_style);
     content += FPSTR(html_ap_header_end);
     content += String(F("<h3>Wi-Fi connection</h3>"));
     content += String(F("<h4>Click to select the Wi-Fi network to which you want to connect the sensor.</h4>"));

     if(scan) {
        int n = WiFi.scanNetworks();
        #ifdef DEBUG
            Serial.println(F("Network scan OK"));
            Serial.flush();
        #endif    
     if(n==0){
        #ifdef DEBUG
            Serial.println(F("No network found"));
            Serial.flush();
        #endif    
        content += F("No Wi-Fi network found.</br> Please repeat.");
     }else{
        // network sorting
        int indices[n];
        for (int i = 0; i < n; i++){
          indices[i] = i;
        }
        // classification according to RSSI
        for(int i = 0; i < n; i++) {
          for(int j = i + 1; j < n; j++) {
            if(WiFi.RSSI(indices[j]) > WiFi.RSSI(indices[i])){
              std::swap(indices[i], indices[j]);
            }
          }//end for2
        }//end for1

        // removal of duplicates (sorting according to RSSI)
        if(removeDuplicates){
          String cssid;
          for(int i = 0; i < n; i++){//for1
            if(indices[i] == -1) continue;
            cssid = WiFi.SSID(indices[i]);
            for(int j = i + 1; j < n; j++){//for2
              if(cssid == WiFi.SSID(indices[j])){
                #ifdef DEBUG
                    Serial.println("Duplicit network " + WiFi.SSID(indices[j]));
                    Serial.flush();
                #endif    
                indices[j] = -1; 
              }//end if
            }//end for2
          }//end for1
        }//end removeDuplicates

        // display networks on the page
        for(int i = 0; i < n; i++){
          if(indices[i] == -1) continue; // skip duplicate networks
          #ifdef DEBUG
              Serial.print(WiFi.SSID(indices[i]));
              Serial.println(WiFi.RSSI(indices[i]));
              Serial.flush();
          #endif    
          int quality = getRSSIasQuality(WiFi.RSSI(indices[i]));

          if(minimumQuality == -1 || minimumQuality < quality){
            String item = FPSTR(html_ap_item);
            String rssiQ;
            rssiQ += quality;
            item.replace("{v}", WiFi.SSID(indices[i]));
            item.replace("{r}", rssiQ);
            if(WiFi.encryptionType(indices[i]) != WIFI_AUTH_OPEN){ // ESP32 encryptionType: WIFI_AUTH_OPEN, WIFI_AUTH_WEP, WIFI_AUTH_WPA_PSK, WIFI_AUTH_WPA2_PSK, WIFI_AUTH_WPA_WPA2_PSK, WIFI_AUTH_WPA2_ENTERPRISE
              item.replace("{i}", "l");
            }else{
              item.replace("{i}", "");
            }//end else
            content += item;
            delay(0);
          }
      }//end for
      content += "<br/>";
      }//end else
    }//end if scan

    content += FPSTR(html_ap_scan_link);
    content += FPSTR(html_ap_form_start);
    content += FPSTR(html_ap_form_end);
    content += FPSTR(html_ap_end);
    content.replace("{timeout}", print_in_html_timeout());
    server.sendHeader("Content-Length", String(content.length()));
    server.send(200, "text/html", content);
    });     

    // Save Wi-Fi network
    server.on("/wifisave", []() {   
    #ifdef DEBUG
        Serial.print(F("SAVE SSID: "));
        Serial.println(server.arg("s").c_str());
        Serial.flush();
    #endif
    if(server.hasArg("s")){
      setEEPROMString(offsetof(eepromdata_t, WiFi_SSID), elementSize(eepromdata_t, WiFi_SSID), server.arg("s"));
    }        
    #ifdef DEBUG
        Serial.print(F("SAVE PASS: "));
        Serial.println(server.arg("p").c_str());
        Serial.flush();
    #endif    
    if(server.hasArg("p")){
      setEEPROMString(offsetof(eepromdata_t, WiFi_PASS), elementSize(eepromdata_t, WiFi_PASS), server.arg("p"));
    }      
    EEPROM.commit();
    delay(500);
    
    String content = FPSTR(html_ap_header);
    content.replace("{v}", "Sensor ESP32");
    content += FPSTR(html_ap_script);
    content += FPSTR(html_ap_style);
    content += FPSTR(html_ap_header_end);
    content += FPSTR(html_ap_saved);
    content += FPSTR(html_ap_end);
    content.replace("{timeout}", print_in_html_timeout());
    server.send(200, "text/html", content);
    });  

    // Information about sensor
    server.on("/i", []() {  
    String content = FPSTR(html_ap_header);
    content.replace("{v}", "Sensor Information");
    content += FPSTR(html_ap_script);
    content += FPSTR(html_ap_style);
    content += FPSTR(html_ap_header_end);
    content += String(F("<h4>Sensor Information</h4>"));
    content += F("<dl>");
    content += F("<dt><b>Sensor Name</b></dt><dd>");
    content += String(SEN_NAME);
    content += F("</dd>");
    content += F("<dt><b>Sensor SN</b></dt><dd>");
    content += String(SNnum);
    content += F("</dd>");        
    content += F("<dt><b>Wi-Fi SSID</b></dt><dd>");
    content += String(WiFi_SSID);
    content += F("</dd>");
    content += F("<dt><b>Sensor AP MAC</b></dt><dd>");
    content += WiFi.softAPmacAddress();
    content += F("</dd>");
    content += F("<dt><b>Sensor STA MAC</b></dt><dd>");
    content += WiFi.macAddress();
    content += F("</dd>");   
    content += F("<dt><b>Wi-Fi AP password</b></dt><dd>");
    content += String(AP_WIFI_PASS);
    content += F("</dd>");
    content += F("<dt><b>FW upload password</b></dt><dd>");
    content += String(UPLOAD_PASS);
    content += F("</dd>");             
    content += F("<dt><b>OSPy address</b></dt><dd>");
    content += String(SERV_IP); 
    content += F("</dd>");
    content += F("<dt><b>OSPy port</b></dt><dd>");
    content += String(SERV_PORT);
    content += F("</dd>");   
    content += F("<dt><b>Use SSL (https)</b></dt><dd>");
    if(USE_SSL==1)  content += F("Yes (https)");
    else content += F("No (http)");
    content += F("</dd>");
    content += F("<dt><b>AES key</b></dt><dd>");
    content += String(AES_KEY);
    content += F("</dd>");
    content += F("<dt><b>AES secret</b></dt><dd>");
    content += String(AES_SEC);
    content += F("</dd>");
    content += F("<dt><b>OSPy use authorization</b></dt><dd>");
    if(USE_AUTH==1)  content += F("Yes");
    else content += F("No"); 
    content += F("</dd>");   
    content += F("<dt><b>OSPy Authorization name</b></dt><dd>");
    content += String(AUTH_NAME);
    content += F("</dd>"); 
    content += F("<dt><b>OSPy Authorization password</b></dt><dd>");
    content += String(AUTH_PASS);
    content += F("</dd>");  
    content += F("<dt><b>Sensor type</b></dt><dd>");
    switch(SEN_TYPE){
      default: content += F("Unknown");  break;
      case 0: content += F("Unknown");  break;
      case 1: content += F("Dry Contact");  break;
      case 2: content += F("Leak Detector");  break;
      case 3: content += F("Moisture");  break;
      case 4: content += F("Motion");  break;
      case 5: content += F("Temperature");  break;
      case 6: content += F("Multi sensor");  break;
    }
    content += F("</dd>");   
    content += F("<dt><b>Sensor communication</b></dt><dd>");
    switch(SEN_COM){
      default: content += F("Unknown");  break;
      case 0: content += F("Wi-Fi/LAN");  break;
      case 1: content += F("Radio");  break;
    }    
    content += F("</dd>");   
    content += F("<dt><b>Divider correction mV</b></dt><dd>");
    content += String(DIVIDER_CORRECTION); 
    content += F("*0.1");   
    content += F("</dd>");
    content += F("<dt><b>DS1 correction (+-) °C</b></dt><dd>");
    content += String(DS1_CALIB);    
    content += F("</dd>");
    content += F("<dt><b>DS2 correction (+-) °C</b></dt><dd>");
    content += String(DS2_CALIB);    
    content += F("</dd>");
    content += F("<dt><b>DS3 correction (+-) °C</b></dt><dd>");
    content += String(DS3_CALIB);    
    content += F("</dd>");
    content += F("<dt><b>DS4 correction (+-) °C</b></dt><dd>");
    content += String(DS4_CALIB);    
    content += F("</dd>");            
    if(SEL_MOIST_SONIC==0){
      content += F("<dt><b>Moisture probe</b></dt><dd>");
      switch(MOIST_TYPE){
        default: content += F("Unknown");  break;
        case 0: content += F("DHT22 (AM2302, AM2321)");  break;
        case 1: content += F("DHT21 (AM2301)");  break;
        case 2: content += F("DHT11");  break;
        case 3: content += F("SHT21 (HTU21D)"); break;
      }    
      content += F("</dd>");
    }
    if(SEL_MOIST_SONIC==1){
      content += F("<dt><b>Sonic probe</b></dt><dd>");
      content += F("Yes</dd>");      
    }
    else{
      content += F("<dt><b>Sonic probe</b></dt><dd>");
      content += F("No (disabled)</dd>");        
    }
    content += F("<dt><b>Compilation</b></dt><dd>");
    content += "Date: " + String(CompilerDATE) + ", TIME " + String(CompilerTIME) + ", xtensa-esp32-elf-gcc: " + String(__VERSION__);
    content += F("</dd>");
    content += F("<dt><b>Flash memory</b></dt><dd>");
    content += ESP.getFlashChipSize();
    content += F(" byte</dd>");
    content += F("<dt><b>ESP32 free ram</b></dt><dd>");
    content += String(ESP.getFreeHeap()); 
    content += F(" byte</dd>"); 
    get_temp();
    get_motion();
    get_moisture();
    get_leak_detector();
    get_dry_contact();
    content += F("<dt><b>DS18B20 nr. 1</b></dt><dd>");
    content += String(curTemp_1)+"°C"; 
    content += F("</dd>");
    if(SEN_TYPE == 6){
    content += F("<dt><b>DS18B20 nr. 2</b></dt><dd>");
    content += String(curTemp_2)+"°C"; 
    content += F("</dd>");
    content += F("<dt><b>DS18B20 nr. 3</b></dt><dd>");
    content += String(curTemp_3)+"°C"; 
    content += F("</dd>");
    content += F("<dt><b>DS18B20 nr. 4</b></dt><dd>");
    content += String(curTemp_4)+"°C"; 
    content += F("</dd>");
    }
    content += F("<dt><b>Dry contact</b></dt><dd>");
    content += String(curDrcon); 
    content += F("</dd>");   
    content += F("<dt><b>Dry contact input</b></dt><dd>");
    if(INVERT_DRY==1)  content += F("PULL-DOWN");
    else content += F("PULL-UP"); 
    content += F("</dd>");    
    content += F("<dt><b>Leak detector</b></dt><dd>");
    content += String(curLkdet)+"%"; 
    content += F("</dd>");
    if(SEL_MOIST_SONIC==0){
       content += F("<dt><b>Moisture</b></dt><dd>");
       content += String(curHumi)+"%"; 
       content += F("</dd>"); 
    }
    if(SEL_MOIST_SONIC==1){
      content += F("<dt><b>Sonic distance</b></dt><dd>");
      content += String(curSon)+"cm";
      content += F("</dd>");      
    }       
    content += F("<dt><b>Motion</b></dt><dd>");
    content += String(curMoti); 
    content += F("</dd>"); 
    content += F("<dt><b>Motion input is</b></dt><dd>");
    if(INVERT_MOTI==1)  content += F("PULL-DOWN");
    else content += F("PULL-UP"); 
    content += F("</dd>");      
    content += F("</dl>");                     
    content += F("</br><form action=\"/\" method=\"get\"><button>Back</button></form>");
    content += FPSTR(html_ap_end);
    content.replace("{timeout}", print_in_html_timeout());
    server.sendHeader("Content-Length", String(content.length()));
    server.send(200, "text/html", content);
    });   

    // Sensor settings
    server.on("/c", []() {  
    // used id: abcdefghijkloqtvuxyz       
    String content = FPSTR(html_ap_header);
    content.replace("{v}", "Sensor settings");
    content += FPSTR(html_ap_script);
    content += FPSTR(html_ap_style);
    content += FPSTR(html_ap_header_end);
    content += F("<h4>Sensor Settings</h4>");
    content += F("</br><form method='get' action='/sensorsave'>");
    content += F("<dl>");
    content += F("<dt><b>Sensor Name</b></dt><dd>");
    content += F("<input id='o' name='o' length=16 maxlength='32' value='"); 
    content += String(SEN_NAME);  
    content += F("'></dd>");    
    content += F("<dt><b>Wi-Fi AP password</b></dt><dd>");
    content += F("<input id='y' name='y' length=16 maxlength='32' value='"); 
    content += String(AP_WIFI_PASS);  
    content += F("'></dd>"); 
    content += F("<dt><b>FW upload password</b></dt><dd>");
    content += F("<input id='q' name='q' length=16 maxlength='32' value='"); 
    content += String(UPLOAD_PASS);  
    content += F("'></dd>");            
    content += F("<dt><b>OSPy IP address</b></dt><dd>");
    content += F("<input id='a' name='a' length=16 maxlength='32' value='"); 
    content += String(SERV_IP);  
    content += F("'></dd>");
    content += F("<dt><b>OSPy port</b></dt><dd>");
    content += F("<input id='b' name='b' length=6 maxlength='6' value='");    
    content += String(SERV_PORT); 
    content += F("'></dd>");
    content += F("<dt><b>Use SSL (https)</b></dt><dd>");
    content += F("<input type='checkbox' id='e' name='e' ");    
    if(USE_SSL==1) content += F("checked >");  
    else           content += F(" >");
    content += F("<dt><b>AES key</b></dt><dd>");
    content += F("<input id='c' name='c' length=16 maxlength='16' value='");    
    content += String(AES_KEY);
    content += F("'></dd>"); 
    content += F("<dt><b>AES secure</b></dt><dd>");
    content += F("<input id='d' name='d' length=16 maxlength='16' value='");    
    content += String(AES_SEC); 
    content += F("'></dd>");
    content += F("<dt><b>Use OSPy authorisation</b></dt><dd>");
    content += F("<input type='checkbox' id='f' name='f' ");    
    if(USE_AUTH==1) content += F("checked >");  
    else            content += F(" >");
    content += F("</dd></dl>");    
    content += F("<dt><b>Authorisation name</b></dt><dd>");
    content += F("<input id='g' name='g' length=16 maxlength='16' value='");    
    content += String(AUTH_NAME);
    content += F("'></dd>");  
    content += F("</dl>");
    content += F("<dt><b>Authorisation password</b></dt><dd>");
    content += F("<input id='h' name='h' length=16 maxlength='16' value='");    
    content += String(AUTH_PASS);
    content += F("'></dd>");  
    content += F("</dl>");    
    content += F("<dt><b>Sensor type</b></dt><dd>");
    content += F("<select name=\"t\" id=\"t\">");
    content += F("<option value=\"0\" "); if(SEN_TYPE == 0) content += F("selected");
    content += F(">None</option>");
    content += F("<option value=\"1\" "); if(SEN_TYPE == 1) content += F("selected");
    content += F(">Dry Contact</option>");
    content += F("<option value=\"2\" "); if(SEN_TYPE == 2) content += F("selected");
    content += F(">Leak Detector</option>");
    content += F("<option value=\"3\" "); if(SEN_TYPE == 3) content += F("selected");
    content += F(">Moisture</option>");
    content += F("<option value=\"4\" "); if(SEN_TYPE == 4) content += F("selected");
    content += F(">Motion</option>");
    content += F("<option value=\"5\" "); if(SEN_TYPE == 5) content += F("selected");
    content += F(">Temperature</option>");
    content += F("<option value=\"6\" "); if(SEN_TYPE == 6) content += F("selected");
    content += F(">Multi sensor</option>");
    content += F("</select>");  
    content += F("</dd>");  
    content += F("</dl>");       
    content += F("<dt><b>Dry contact input is</b></dt><dd>");
    content += F("<select name=\"u\" id=\"u\">");
    content += F("<option value=\"0\" "); if(INVERT_DRY == 0) content += F("selected");
    content += F(">PULL-UP</option>");
    content += F("<option value=\"1\" "); if(INVERT_DRY == 1) content += F("selected");
    content += F(">PULL-DOWN</option>");
    content += F("</select>");  
    content += F("</dd>");  
    content += F("</dl>"); 
    content += F("<dt><b>Motion input is</b></dt><dd>");
    content += F("<select name=\"z\" id=\"z\">");
    content += F("<option value=\"0\" "); if(INVERT_MOTI == 0) content += F("selected");
    content += F(">PULL-UP</option>");
    content += F("<option value=\"1\" "); if(INVERT_MOTI == 1) content += F("selected");
    content += F(">PULL-DOWN</option>");
    content += F("</select>");  
    content += F("</dd>");  
    content += F("</dl>"); 
    content += F("<dt><b>Divider correction (+-) mV</b></dt><dd>");
    content += F("<input id='r' name='r' length=5 maxlength='5' value='");    
    content += String(DIVIDER_CORRECTION); 
    content += F("'></dd>"); 
    content += F("<dt><b>DS1 correction (+-) °C</b></dt><dd>");
    content += F("<input  id='i' name='i' length=4 maxlength='4' value='");    
    content += String(DS1_CALIB); 
    content += F("'></dd>");
    content += F("<dt><b>DS2 correction (+-) °C</b></dt><dd>");
    content += F("<input id='j' name='j' length=4 maxlength='4' value='");    
    content += String(DS2_CALIB); 
    content += F("'></dd>");
    content += F("<dt><b>DS3 correction (+-) °C</b></dt><dd>");
    content += F("<input id='k' name='k' length=4 maxlength='4' value='");    
    content += String(DS3_CALIB); 
    content += F("'></dd>");
    content += F("<dt><b>DS4 correction (+-) °C</b></dt><dd>");
    content += F("<input id='l' name='l' length=4 maxlength='4' value='");    
    content += String(DS4_CALIB); 
    content += F("'></dd>");            
    content += F("<dt><b>Moisture or sonic probe?</b></dt><dd>");
    content += F("<select name=\"i\" id=\"i\">");
    content += F("<option value=\"0\" "); if(SEL_MOIST_SONIC == 0) content += F("selected");
    content += F(">Moisture</option>");
    content += F("<option value=\"1\" "); if(SEL_MOIST_SONIC == 1) content += F("selected");
    content += F(">Sonic</option>");       
    content += F("</select>");  
    content += F("</dd>");  
    content += F("</dl>");      
    content += F("<dt><b>Moisture probe</b></dt><dd>");
    content += F("<select name=\"x\" id=\"x\">");
    content += F("<option value=\"0\" "); if(MOIST_TYPE == 0) content += F("selected");
    content += F(">DHT22 (AM2302, AM2321)</option>");
    content += F("<option value=\"1\" "); if(MOIST_TYPE == 1) content += F("selected");
    content += F(">DHT21 (AM2301)</option>");
    content += F("<option value=\"2\" "); if(MOIST_TYPE == 2) content += F("selected");
    content += F(">DHT11</option>"); 
    content += F("<option value=\"3\" "); if(MOIST_TYPE == 3) content += F("selected");
    content += F(">SHT21 (HTU21D)</option>");       
    content += F("</select>");  
    content += F("</dd>");  
    content += F("</dl>");          
    content += F("</br><button type='submit'>Save</button></form>");
    content += F("</br><form action=\"/\" method=\"get\"><button>Back</button></form>");
    content += FPSTR(html_ap_end);
    content.replace("{timeout}", print_in_html_timeout());
    server.sendHeader("Content-Length", String(content.length()));
    server.send(200, "text/html", content);
    });   

    // Sensor save
    server.on("/sensorsave", []() {   
    #ifdef DEBUG
      Serial.println(F("SAVING"));
      Serial.flush();
    #endif          
    if(server.hasArg("o")){
      setEEPROMString(offsetof(eepromdata_t, SEN_NAME), elementSize(eepromdata_t, SEN_NAME), server.arg("o"));
      #ifdef DEBUG
        Serial.print(F("Sensor name: "));
        Serial.println(server.arg("o"));
        Serial.flush();
      #endif
    }  

    if(server.hasArg("y")){
      setEEPROMString(offsetof(eepromdata_t, AP_WIFI_PASS), elementSize(eepromdata_t, AP_WIFI_PASS), server.arg("y"));
      #ifdef DEBUG
        Serial.print(F("Wi-Fi AP password: "));
        Serial.println(server.arg("y"));
        Serial.flush();
      #endif
    }

    if(server.hasArg("q")){
      setEEPROMString(offsetof(eepromdata_t, UPLOAD_PASS), elementSize(eepromdata_t, UPLOAD_PASS), server.arg("q"));
      #ifdef DEBUG
        Serial.print(F("FW upload password: "));
        Serial.println(server.arg("q"));
        Serial.flush();
      #endif
    } 

    if(server.hasArg("i")){
      setEEPROMString(offsetof(eepromdata_t, SEL_MOIST_SONIC), elementSize(eepromdata_t, SEL_MOIST_SONIC), server.arg("i"));
      #ifdef DEBUG
        Serial.print(F("Moist or Sonic: "));
        Serial.println(server.arg("i"));
        Serial.flush();
      #endif
    }           
    
    if(server.hasArg("c")){
      setEEPROMString(offsetof(eepromdata_t, AES_KEY), elementSize(eepromdata_t, AES_KEY), server.arg("c"));
      #ifdef DEBUG
        Serial.print(F("AES key: "));
        Serial.println(server.arg("c"));
        Serial.flush();
      #endif
    }  
    
    if(server.hasArg("d")){
      setEEPROMString(offsetof(eepromdata_t, AES_SEC), elementSize(eepromdata_t, AES_SEC), server.arg("d"));
      #ifdef DEBUG
        Serial.print(F("AES sec: "));
        Serial.println(server.arg("d"));
        Serial.flush();
      #endif
    }  
         
    if(server.hasArg("g")){
      setEEPROMString(offsetof(eepromdata_t, AUTH_NAME), elementSize(eepromdata_t, AUTH_NAME), server.arg("g"));
      #ifdef DEBUG
        Serial.print(F("Auth name: "));
        Serial.println(server.arg("g"));
        Serial.flush();
      #endif
    }   
      
    if(server.hasArg("h")){
      setEEPROMString(offsetof(eepromdata_t, AUTH_PASS), elementSize(eepromdata_t, AUTH_PASS), server.arg("h"));
      #ifdef DEBUG
        Serial.print(F("Auth pass: "));
        Serial.println(server.arg("h"));
        Serial.flush();
      #endif
    } 
       
    if(server.hasArg("a")){
      setEEPROMString(offsetof(eepromdata_t, SERV_IP), elementSize(eepromdata_t, SERV_IP), server.arg("a"));
      #ifdef DEBUG
        Serial.print(F("OSPy IP: "));
        Serial.println(server.arg("a"));
        Serial.flush();
      #endif
    }  
      
    if(server.hasArg("b")){
      setEEPROMString(offsetof(eepromdata_t, SERV_PORT), elementSize(eepromdata_t, SERV_PORT), server.arg("b"));
      #ifdef DEBUG
        Serial.print(F("OSPy PORT: "));
        Serial.println(server.arg("b"));
        Serial.flush();
      #endif
    } 
         
    if(server.hasArg("t")){
      setEEPROMString(offsetof(eepromdata_t, SEN_TYPE), elementSize(eepromdata_t, SEN_TYPE), server.arg("t"));
      #ifdef DEBUG
        Serial.print(F("SEN type: "));
        Serial.println(server.arg("t"));
        Serial.flush();
      #endif
    }  

    if(server.hasArg("r")){
      setEEPROMString(offsetof(eepromdata_t, DIVIDER_CORRECTION), elementSize(eepromdata_t, DIVIDER_CORRECTION), server.arg("r"));
      #ifdef DEBUG
        Serial.print(F("DIVIDER: "));
        Serial.println(server.arg("r"));
        Serial.flush();
      #endif
    }     

    if(server.hasArg("x")){
      setEEPROMString(offsetof(eepromdata_t, MOIST_TYPE), elementSize(eepromdata_t, MOIST_TYPE), server.arg("x"));
      #ifdef DEBUG
        Serial.print(F("MOIST type: "));
        Serial.println(server.arg("x"));
        Serial.flush();
      #endif
    }
           
    if(server.hasArg("e")){
      if(server.arg("e")=="on"){
        setEEPROMString(offsetof(eepromdata_t, USE_SSL), elementSize(eepromdata_t, USE_SSL), "1");
      }
    }  
    else {
        setEEPROMString(offsetof(eepromdata_t, USE_SSL), elementSize(eepromdata_t, USE_SSL), "0");
    }
    #ifdef DEBUG
      Serial.print(F("USE SSL: "));
      Serial.println(server.arg("e"));
      Serial.flush();
    #endif
     
    if(server.hasArg("f")){
      if(server.arg("f")=="on"){
        setEEPROMString(offsetof(eepromdata_t, USE_AUTH), elementSize(eepromdata_t, USE_AUTH), "1");
      }
    }  
    else {
        setEEPROMString(offsetof(eepromdata_t, USE_AUTH), elementSize(eepromdata_t, USE_AUTH), "0");
    }   
    #ifdef DEBUG
      Serial.print(F("USE auth: "));
      Serial.println(server.arg("f"));
      Serial.flush();
    #endif    

    if(server.hasArg("u")){
      setEEPROMString(offsetof(eepromdata_t, INVERT_DRY), elementSize(eepromdata_t, INVERT_DRY), server.arg("u"));
      #ifdef DEBUG
        Serial.print(F("DRY INPUT PULL-UP-DOWN: "));
        Serial.println(server.arg("u"));
        Serial.flush();
      #endif
    }  

    if(server.hasArg("z")){
      setEEPROMString(offsetof(eepromdata_t, INVERT_MOTI), elementSize(eepromdata_t, INVERT_MOTI), server.arg("z"));
      #ifdef DEBUG
        Serial.print(F("MOTION INPUT PULL-UP-DOWN: "));
        Serial.println(server.arg("z"));
        Serial.flush();
      #endif
    } 

    if(server.hasArg("i")){
      setEEPROMString(offsetof(eepromdata_t, DS1_CALIB), elementSize(eepromdata_t, DS1_CALIB), server.arg("i"));
      #ifdef DEBUG
        Serial.print(F("DS1_CALIB: "));
        Serial.println(server.arg("i"));
        Serial.flush();
      #endif
    } 

    if(server.hasArg("j")){
      setEEPROMString(offsetof(eepromdata_t, DS2_CALIB), elementSize(eepromdata_t, DS2_CALIB), server.arg("j"));
      #ifdef DEBUG
        Serial.print(F("DS2_CALIB: "));
        Serial.println(server.arg("j"));
        Serial.flush();
      #endif
    }                 

    if(server.hasArg("k")){
      setEEPROMString(offsetof(eepromdata_t, DS3_CALIB), elementSize(eepromdata_t, DS3_CALIB), server.arg("k"));
      #ifdef DEBUG
        Serial.print(F("DS3_CALIB: "));
        Serial.println(server.arg("k"));
        Serial.flush();
      #endif
    }   

    if(server.hasArg("l")){
      setEEPROMString(offsetof(eepromdata_t, DS4_CALIB), elementSize(eepromdata_t, DS4_CALIB), server.arg("l"));
      #ifdef DEBUG
        Serial.print(F("DS4_CALIB: "));
        Serial.println(server.arg("l"));
        Serial.flush();
      #endif
    }
         
    EEPROM.commit();
    initEEPROM(); 
    
    String content = FPSTR(html_ap_header);
    content.replace("{v}", "Settings Saved");
    content += FPSTR(html_ap_script);
    content += FPSTR(html_ap_style);
    content += FPSTR(html_ap_header_end);
    content += FPSTR(html_ap_saved);
    content += FPSTR(html_ap_end);
    content.replace("{timeout}", print_in_html_timeout());
    server.sendHeader("Content-Length", String(content.length()));
    server.send(200, "text/html", content);
    });  
       
    // Reboot 
    server.on("/r", [](){  
    String content = FPSTR(html_ap_header);
    content.replace("{v}", "Sensor Restart");
    content += FPSTR(html_ap_style);
    content += FPSTR(html_ap_header_end);
    content += F("<h4>The sensor restarts in 5 seconds.</h4></br>");
    content += F("</br><form action=\"/\" method=\"get\"><button>Back</button></form>");
    content += FPSTR(html_ap_end);
    content.replace("{timeout}", print_in_html_timeout());
    server.sendHeader("Content-Length", String(content.length()));
    server.send(200, "text/html", content);
    delay(5000);
    reboot();
    });  

    // EEPROM set to default ?
    server.on("/EDF", [](){  
    String content = FPSTR(html_ap_header);
    content.replace("{v}", "Sensor ESP32");
    content += FPSTR(html_ap_style);
    content += FPSTR(html_ap_header_end);
    content += F("<h4>Set the default sensor data?</h4></br>");
    content += F("</br><form action=\"/EDFSV\" method=\"get\"><button>Yes clean</button></form>");
    content += F("</br><form action=\"/\" method=\"get\"><button>No back</button></form>");
    content += FPSTR(html_ap_end);
    content.replace("{timeout}", print_in_html_timeout());
    server.sendHeader("Content-Length", String(content.length()));
    server.send(200, "text/html", content);
    }); 

    // EEPROM set to default  OK
    server.on("/EDFSV", [](){  
    String content = FPSTR(html_ap_header);
    content.replace("{v}", "The sensor memory is cleared");
    content += FPSTR(html_ap_style);
    content += FPSTR(html_ap_header_end);
    content += F("The sensor memory is cleared to the default settings!</br>");
    setEEPROMdefault();
    content += F("</br><form action=\"/r\" method=\"get\"><button>Yes restart</button></form>");
    content += F("</br><form action=\"/\" method=\"get\"><button>No back</button></form>");
    content += FPSTR(html_ap_end);
    content.replace("{timeout}", print_in_html_timeout());
    server.sendHeader("Content-Length", String(content.length()));
    server.send(200, "text/html", content);
    });    

#ifdef UPLOAD_BIN_VIA_HTTP     
    server.on("/U", HTTP_POST,[](){   
      String content = "";
      content = F("OK, Restarting...");
      server.send(200, "text/html", content);
      delay(1000);
      reboot();     
    },[](){
       HTTPUpload& upload = server.upload();
       if(upload.status == UPLOAD_FILE_START){
          #ifdef DEBUG 
             Serial.printf("Filename: %s", upload.filename.c_str());
             Serial.println(F(""));
             Serial.flush();
          #endif   
          unsigned long maxSketchSpace = (ESP.getFreeSketchSpace()-0x1000)& 0xFFFFF000;
          if(!Update.begin(maxSketchSpace)){ 
            #ifdef DEBUG
               Update.printError(Serial);
               Serial.flush();
            #endif  
          }// end if     
       }// end if
       else if(upload.status == UPLOAD_FILE_WRITE){ 
          if(Update.write(upload.buf, upload.currentSize) != upload.currentSize){
            #ifdef DEBUG
               Update.printError(Serial);
               Serial.flush();
            #endif  
          }// end if
       }// end else if
       else if(upload.status == UPLOAD_FILE_END){
          if(Update.end(true)){
             #ifdef DEBUG 
                Serial.printf("OK %u bytes", upload.totalSize);
                Serial.println(F(""));
                Serial.flush();
             #endif   
          }// end if
          else{
             #ifdef DEBUG
                Update.printError(Serial);
                Serial.flush();
             #endif   
          }//end else
       }// end else if
      });    
    
      server.on("/T", [](){
      String content = "";  
      content = FPSTR(html_ap_header);
      content.replace("{v}", "Firmware updating");
      content += FPSTR(html_ap_style);
      content += FPSTR(html_ap_header_end);
      content += FPSTR(html_ap_upload);
      content += F("</br><form action=\"/\" method=\"get\"><button>Back</button></form>");
      content += FPSTR(html_ap_end);
      content.replace("{timeout}", print_in_html_timeout());
      server.sendHeader("Content-Length", String(content.length()));
      server.send(200, "text/html", content);
      });               
#endif // end upload     
   
    server.begin();                         // starting http server
}//end WIFIAP_setup

// for DS18B20 fake testing
void print_hex(uint8_t value) {
  if (value < 16) Serial.write('0');
  Serial.print(value, HEX);
  Serial.flush();
}//end void

void print_array(uint8_t *data, int n, char sep = ',') {  
  int idx;
  for (idx=0; idx<n; idx++) {
    print_hex(data[idx]);
    if (idx != n-1)
      Serial.write(sep);
  }
  Serial.flush();
}//end void

bool read_scratchpad(uint8_t *addr, uint8_t *buff9, OneWire ow) {
  ow.reset();
  ow.select(addr);
  ow.write(0xBE); // read scratchpad
  int idx;
  for (idx=0; idx<9; idx++)
    buff9[idx] = ow.read();
  return 0 == OneWire::crc8(buff9, 9);
}//end bool

void test_fake_ds(OneWire ow){
   // ROM address of current sensor
  uint8_t addr[8];  
  // buffers for scratchpad register
  uint8_t buffer0[9];
  uint8_t buffer1[9];
  uint8_t buffer2[9];
  uint8_t buffer3[9];
  // flag to indicate if validation
  //  should be repeated at a different
  //  sensor temperature
  bool t_ok;

  ow.reset_search();
  while (ow.search(addr)) {
    int fake_flags = 0;
    
    print_array(addr, 8, '-');
    if (0 != OneWire::crc8(addr, 8)) {
      // some fake sensors can have their ROM overwritten with
      // arbitrary nonsense, so we don't expect anything good
      // if the ROM doesn't check out
      fake_flags += 1;
      Serial.print(F(" (CRC Error -> Error.)"));
      Serial.flush();
    }

    if ((addr[6] != 0) || (addr[5] != 0) || (addr[0] != 0x28)) {
      fake_flags += 1;
      Serial.print(F(": ROM does not follow expected pattern 28-xx-xx-xx-xx-00-00-crc. Error."));
    } else {
      Serial.print(F(": ROM ok."));
    }    
    Serial.println();
    Serial.flush();
    
    if (!read_scratchpad(addr, buffer0, ow)) read_scratchpad(addr, buffer0, ow);
    
    Serial.print(F("  Scratchpad Register: "));
    print_array(buffer0, 9, '/');
    if (0 != OneWire::crc8(buffer0, 9)) {
      // Unlikely that a sensor will mess up the CRC of the scratchpad.
      // --> Assume we're dealing with a bad connection rather than a bad 
      //     sensor, dump data, and move on to next sensor.
      Serial.println(F("  CRC Error. Check connections or replace sensor."));
      Serial.flush();
      continue;      
    }
    Serial.println();
    Serial.flush();

    // Check content of user EEPROM. Since the EEPROM may have been programmed by the user earlier
    // we do not use this as a test. Rather, we dump this as info.
    Serial.print(F("  Info only: Scratchpad bytes 2,3,4 ("));
    print_array(buffer0+2,3,'/');
    Serial.print(F("): "));
    if ((buffer0[2] != 0x4b) || (buffer0[3] != 0x46) || (buffer0[4] != 0x7f))
      Serial.println(F(" not Maxim default values 4B/46/7F."));
    else
      Serial.println(F(" Maxim default values."));


    Serial.print(F("  Scratchpad byte 5 (0x"));
    print_hex(buffer0[5]);
    Serial.print(F("): "));
    if (buffer0[5] != 0xff) {
      fake_flags += 1;
      Serial.println(F(" should have been 0xFF according to datasheet. Error."));
    } else {
      Serial.println(F(" ok."));
    }
    Serial.flush();

    Serial.print(F("  Scratchpad byte 6 (0x"));
    print_hex(buffer0[6]);
    Serial.print(F("): "));
    if ( ((buffer0[6] == 0x00) || (buffer0[6] > 0x10)) || // totall wrong value
         ( ((buffer0[0] != 0x50) || (buffer0[1] != 0x05)) && ((buffer0[0] != 0xff) || (buffer0[1] != 0x07)) && // check for valid conversion...
           (((buffer0[0] + buffer0[6]) & 0x0f) != 0x00) ) ) { //...before assessing DS18S20 compatibility.
      fake_flags += 1;
      Serial.println(" unexpected value. Error.");
    } else
      Serial.println(" ok.");

    Serial.flush();
    Serial.print(F("  Scratchpad byte 7 (0x"));
    print_hex(buffer0[7]);
    Serial.print(F("): "));
    if (buffer0[7] != 0x10) {
      fake_flags += 1;
      Serial.println(F(" should have been 0x10 according to datasheet. Error."));
    } else {
      Serial.println(F(" ok."));
    }
    
    Serial.flush();
    // set the resolution to 10 bit and modify alarm registers    
    ow.reset();
    ow.select(addr);
    ow.write(0x4E); // write scratchpad. MUST be followed by 3 bytes as per datasheet.
    ow.write(buffer0[2] ^ 0xff);
    ow.write(buffer0[3] ^ 0xff);
    ow.write(0x3F);
    ow.reset();

    if (!read_scratchpad(addr, buffer1, ow)) read_scratchpad(addr, buffer1, ow);
    
    Serial.print(F("  0x4E modifies alarm registers: "));
    if ((buffer1[2] != (buffer0[2] ^ 0xff)) || (buffer1[3] != (buffer0[3] ^ 0xff))) {
      fake_flags += 1;
      Serial.print(F(" cannot modify content as expected (want: "));
      print_hex(buffer0[2] ^ 0xff);
      Serial.write('/');
      print_hex(buffer0[3] ^ 0xff);
      Serial.print(F(", got: "));
      print_array(buffer1+2, 2, '/');
      Serial.println(F("). Error."));      
    } else
      Serial.println(F(" ok."));

    Serial.flush();
    Serial.print(F("  0x4E accepts 10 bit resolution: "));
    if (buffer1[4] != 0x3f) {
      fake_flags += 1;
      Serial.print(F(" rejected (want: 0x3F, got: "));
      print_hex(buffer1[4]);
      Serial.println(F("). Error."));
    } else
      Serial.println(F(" ok."));

    Serial.flush();
    Serial.print(F("  0x4E preserves reserved bytes: "));
    if ((buffer1[5] != buffer0[5]) || (buffer1[6] != buffer0[6]) || (buffer1[7] != buffer0[7])) {
      fake_flags += 1;
      Serial.print(F(" no, got: "));
      print_array(buffer1+5, 3, '/');
      Serial.println(F(". Error."));
    } else
      Serial.println(F(" ok."));    

    // set the resolution to 12 bit
    ow.reset();
    ow.select(addr);
    ow.write(0x4E); // write scratchpad. MUST be followed by 3 bytes as per datasheet.
    ow.write(buffer0[2]);
    ow.write(buffer0[3]);
    ow.write(0x7f);
    ow.reset();

    if (!read_scratchpad(addr, buffer2, ow)) read_scratchpad(addr, buffer2, ow);
    
    Serial.print(F("  0x4E accepts 12 bit resolution: "));
    if (buffer2[4] != 0x7f) {
      fake_flags += 1;
      Serial.print(F(" rejected (expected: 0x7F, got: "));
      print_hex(buffer2[4]);
      Serial.println(F("). Error."));
    } else
      Serial.println(F(" ok."));

    Serial.flush();
    Serial.print(F("  0x4E preserves reserved bytes: "));
    if ((buffer2[5] != buffer1[5]) || (buffer2[6] != buffer1[6]) || (buffer2[7] != buffer1[7])) {
      fake_flags += 1;
      Serial.print(F(" no, got: "));
      print_array(buffer2+5, 3, '/');
      Serial.println(F(". Error."));
    } else
      Serial.println(F(" ok."));

    Serial.flush();
    Serial.print("  Checking byte 6 upon temperature change: ");
    if (( ((buffer2[0] == 0x50) && (buffer2[1] == 0x05)) || ((buffer2[0] == 0xff) && (buffer2[1] == 0x07)) ||
         ((buffer2[6] == 0x0c) && (((buffer2[0] + buffer2[6]) & 0x0f) == 0x00)) ) &&
         ((buffer2[6] >= 0x00) && (buffer2[6] <= 0x10)) ){
      // byte 6 checked out as correct in the initial test but the test ambiguous.
      //   we need to check if byte 6 is consistent after temperature conversion
            
      // We'll do a few temperature conversions in a row.
      // Usually, the temperature rises slightly if we do back-to-back
      //   conversions.
      int count = 5;
      do {
        count -- ;
        if (count < 0)
          break;
        // perform temperature conversion
        ow.reset();
        ow.select(addr);
        ow.write(0x44);
        delay(750);
        
        if (!read_scratchpad(addr, buffer3, ow)) read_scratchpad(addr, buffer3, ow);
        
      } while ( ((buffer3[0] == 0x50) && (buffer3[1] == 0x05)) || ((buffer3[0] == 0xff) && (buffer3[1] == 0x07)) ||
                ((buffer3[6] == 0x0c) && (((buffer3[0] + buffer3[6]) & 0x0f) == 0x00)) );
      if (count < 0) {
        Serial.println(F(" Inconclusive. Please change sensor temperature and repeat."));
        Serial.flush();
        t_ok = false;
      } else {
        t_ok = true;
        if ((buffer3[6] != 0x0c) && (((buffer3[0] + buffer3[6]) & 0x0f) == 0x00)) {
          Serial.println(F(" ok."));
          Serial.flush();
        } else {
          fake_flags += 1;
          Serial.print(F(" Temperature LSB = 0x"));
          print_hex(buffer3[0]);
          Serial.print(F(" but byte 6 = 0x"));
          print_hex(buffer3[6]);
          Serial.println(F(". Error."));
          Serial.flush();
        }
      }
    } else {
      Serial.println(F("not necessary. Skipped."));
      Serial.flush();
      t_ok = true;
    }

    Serial.print(F("  --> "));
    if (!t_ok) {
      Serial.print(F("DS18S20 counterfeit test not completed, otherwise sensor"));
    } else 
      Serial.print(F("Sensor"));
      
    if (fake_flags == 0) {
      Serial.println(F(" responded like a genuie Maxim."));
      Serial.println(F("      Not tested: EEPROM, Parasite Power, and undocumented commands."));
      Serial.flush();
    } else {
      Serial.print(F(" appears to be counterfeit based on "));
      Serial.print(fake_flags, DEC);
      Serial.println(F(" deviations."));
      Serial.flush();
      if (fake_flags == 1) {
        Serial.println(F("  The number of deviations is unexpectedly small."));
        Serial.println(F("  Please see https://github.com/cpetrich/counterfeit_DS18B20/"));
        Serial.println(F("  to help interpret the result."));
        Serial.flush();
      }
    }
    Serial.println();
    Serial.flush();
  } // done with all sensors
}//end void

void setWiFiPowerMode(){
    //  esp_wifi_set_ps(WIFI_PS_MAX_MODEM);
        esp_wifi_set_ps(WIFI_PS_NONE);
    //  esp_wifi_set_ps(WIFI_PS_MIN_MODEM);
}
