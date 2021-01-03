/*
 * Sensor for OSPy system 
 * Martin Pihrt - 02.01.2021
 * Arduino IDE >= 1.8.13
 * board ESP32 1.0.4 (https://github.com/espressif/arduino-esp32)
 * 
 *  AP manager: password for AP Wi-Fi "ospy-sensor-esp32" open browser "192.168.1.1"
 *  BUTTON AP MANAGER -> It must be held for at least >2 seconds when switching on (for starting AP manager)
 *  
 *  todo connecting voltage to source via resistors (max is 1.1V), moisture, leak detector
*/

// Debug
#define DEBUG                // Comment this line when DEBUG mode is not needed 

// FW version
int fw_version = 102;        // ex: FW version 102 is 1.02 
/* change compared to fw 1.01: Add AP manager for settings sensor from phone, tablet (4 minutes timeout). Saving to eeprom memory. Fast blinking LED if AP manager is run. Slow blinking LED if normal run
 * control relay: ex: http://192.168.88.207/0123456789abcdff?re=1 (or re=0) 0123456789abcdff is secure code from sensor
 */


// SN
const char *SNnum = "001";   // sensor serial number

// ESP32
#include "WiFi.h"
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

#include <driver/adc.h>      // A/D converter on ESP32

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

// Wi-Fi LED
byte out_led           = 2;                      // blue LED on the board

// RELAY
byte out_relay         = 19;                     // relay for control on/off from OSPy
bool revers            = false;                  // if true is active out in LOW, false is active out in HIGH (for inversion relay logic)

// I2C
byte I2C_SDA           = 33;                     // SDA
byte I2C_SCL           = 32;                     // SCL

#include <OneWire.h>                             // https://github.com/stickbreaker/OneWire  This modifications supports the ESP32 under the Arduino-esp32 Environment.
#include <DallasTemperature.h>
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
  char WiFi_SSID[32];     // max 32 char SSID for Wi-Fi
  char WiFi_PASS[32];     // max 32 char PASS for Wi-Fi
  char AES_KEY[17];       // max 16 char AES key
  char AES_SEC[17];       // max 16 char AES secret
  char USE_SSL[2];        // 0,1 enable or disable SSL for https
  char USE_AUTH[2];       // 0,1 enable or disable OSPy authorisation
  char AUTH_NAME[17];     // max 16 char user name for access to OSPy
  char AUTH_PASS[17];     // max 16 char user password for access to OSPy
  char SERV_IP[32];       // max 32 char OSPy server IP ex: 192.168.88.215
  char SERV_PORT[7];      // max 5 char OSPy server port ex: 8080
  char SEN_NAME[32];      // max 32 char sensor name ex: sensor 1
  char SEN_TYPE[3];       // 5 is temperature sensor (1=Dry Contact, 2=Leak Detector, 3=Moisture, 4=Motion, 5=temperature)
  char SEN_COM[3];        // 0 is Wi-Fi/Lan (1=Radio)
  char MAGICNR[3];        // for first sensor setup if not yed setuped. If setuped magic nbr is 666 :-)
} eepromdata_t;

// date and time compilation
#define CompilerTIME __TIME__ // time hh:mm:ss 
#define CompilerDATE __DATE__ // date M mm dd yyyy

// throw compilation error if there board is not ESP32
#if not defined(ESP32)
   #error "Error! The selected board is not ESP32! Select: doit ESP32 devkit V1"
#endif

//  values from EEPROM
char WiFi_SSID[32];                             
char WiFi_PASS[32];                             
char AES_KEY[17];
char AES_SEC[17];      
byte USE_SSL;       
byte USE_AUTH;       
char AUTH_NAME[17];    
char AUTH_PASS[17];   
char SERV_IP[32];       
char SERV_PORT[7];     
char SEN_NAME[32];      
byte SEN_TYPE;       
byte SEN_COM;       

int curRssi, curPercent, curMoti, curDrcon;      // current RSSI, RSSI in percent, motion, dry contact
int LastCurMoti=1, LastCurDrcon=1;               // last value for motion, dry contact 
unsigned long prevTikTime, prevTime, nowTime, interval;   // previous time for sec timer (millis), send data timer (millis), current time (millis)  
float curTemp_1 = -127;                          // current temperature DS1
float curTemp_2 = -127;                          // current temperature DS2
float curTemp_3 = -127;                          // current temperature DS3
float curTemp_4 = -127;                          // current temperature DS4
float LastcurTemp_1, LastcurTemp_2, LastcurTemp_3, LastcurTemp_4; // last value temperature DS1-DS4
float curVdd, curLkdet, curHumi;                 // current voltage, leak detector, moisture
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

// interval settings 
unsigned long wait_send = 30000;                 // 30 sec loop for sending data 
unsigned long APtimeout = 240000;                // 4 minutes timeout for AP manager
const char * APpasswd = "ospy-sensor-esp32";     // password for connecting to AP Wi-Fi network 192.168.1.1

// INTERRUPT for blink LED
volatile bool en_led_blink;
#define INTERRUPT_ATTR IRAM_ATTR                 // 1 sec tick for ESP32 CPU 80MHZ is T = 1/(80MHZ/80) = 1 us. 1000000 tick is 1 sec  
hw_timer_t * timer1 = NULL;                      // create timer 1
portMUX_TYPE timerMux0 = portMUX_INITIALIZER_UNLOCKED;

void IRAM_ATTR onTimer(){
  portENTER_CRITICAL_ISR(&timerMux0);

  if(en_led_blink){   
     digitalWrite(out_led, !digitalRead(out_led));       
  }// end if(enable_blinking)
  portEXIT_CRITICAL_ISR(&timerMux0);
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
   setEEPROMString(offsetof(eepromdata_t, WiFi_SSID), elementSize(eepromdata_t, WiFi_SSID), "");
   setEEPROMString(offsetof(eepromdata_t, WiFi_PASS), elementSize(eepromdata_t, WiFi_PASS), "");
   setEEPROMString(offsetof(eepromdata_t, AES_KEY), elementSize(eepromdata_t, AES_KEY),     "0123456789abcdef");
   setEEPROMString(offsetof(eepromdata_t, AES_SEC), elementSize(eepromdata_t, AES_SEC),     "0123456789abcdef");
   setEEPROMString(offsetof(eepromdata_t, USE_SSL), elementSize(eepromdata_t, USE_SSL),     "0");
   setEEPROMString(offsetof(eepromdata_t, USE_AUTH), elementSize(eepromdata_t, USE_AUTH),   "1");
   setEEPROMString(offsetof(eepromdata_t, AUTH_NAME), elementSize(eepromdata_t, AUTH_NAME), "admin");
   setEEPROMString(offsetof(eepromdata_t, AUTH_PASS), elementSize(eepromdata_t, AUTH_PASS), "opendoor");
   setEEPROMString(offsetof(eepromdata_t, SERV_IP), elementSize(eepromdata_t, SERV_IP),     "x.x.x.x"); 
   setEEPROMString(offsetof(eepromdata_t, SERV_PORT), elementSize(eepromdata_t, SERV_PORT), "8080"); 
   setEEPROMString(offsetof(eepromdata_t, SEN_NAME), elementSize(eepromdata_t, SEN_NAME),   "ESP32 Sensor");
   setEEPROMString(offsetof(eepromdata_t, SEN_TYPE), elementSize(eepromdata_t, SEN_TYPE),   "5"); // 1=Dry Contact, 2=Leak Detector, 3=Moisture, 4=Motion, 5=temperature, 6=multi sensor
   setEEPROMString(offsetof(eepromdata_t, SEN_COM), elementSize(eepromdata_t, SEN_COM),     "0"); // 0=Wi-Fi/Lan, 1=Radio
   setEEPROMString(offsetof(eepromdata_t, MAGICNR), elementSize(eepromdata_t,  MAGICNR),    "666"); 
  
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

   int mgc = atoi(getEEPROMString(offsetof(eepromdata_t, MAGICNR), elementSize(eepromdata_t, MAGICNR)).c_str());  
   if(mgc != 666) setEEPROMdefault();
}// end void   

// SETUP******************************************************************************************************************   
void setup() {
  pinMode(out_led, OUTPUT);     
  pinMode(out_relay, OUTPUT);
  digitalWrite(out_led, LOW);
  set_rele(0);                               // relay off

  timer1 = timerBegin(0, 80, true);          // 80MHZ CPU
  timerAttachInterrupt(timer1, &onTimer, true); // connect function onTimer for timer (first available timer from 4 HW timers in ESP32)
  timerAlarmWrite(timer1, 1000000, true);    // set alarm for call function onTimer (1 us => 0.1 sec is 100000 us, 1 sec is 1000000 us)
  timerAlarmEnable(timer1);                  // enable timer
  
  #ifdef DEBUG 
    Serial.begin(115200);
    delay(1000);
    Serial.println(F(""));
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
     DS1sensors.setResolution(11);           // The resolution of the DS18B20 is configurable (9, 10, 11, or 12 bits), with 12-bit readings the factory default state. This equates to a temperature resolution of 0.5°C, 0.25°C, 0.125°C, or 0.0625°C
     DS_1_OK = true;
     Serial.println(F("DS18B20 nr. 1 is connected"));     
  }//end test oneWire search 
  byte addr2[8]; 
  if(oneWire_2.search(addr2)){
     oneWire_2.reset_search();
     DS2sensors.setResolution(11);          
     DS_2_OK = true;
     Serial.println(F("DS18B20 nr. 2 is connected"));
  }//end test oneWire search
  byte addr3[8];
  if(oneWire_3.search(addr3)){
     oneWire_3.reset_search();
     DS3sensors.setResolution(11);         
     DS_3_OK = true;
     Serial.println(F("DS18B20 nr. 3 is connected"));
  }//end test oneWire search
  byte addr4[8];
  if(oneWire_4.search(addr4)){
     oneWire_4.reset_search();
     DS4sensors.setResolution(11);          
     DS_4_OK = true;
     Serial.println(F("DS18B20 nr. 4 is connected"));
  }//end test oneWire search    
  
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

    allSN = ArduinoDateTimeCompile();            
    allSN += "SensorESP32sn"+String(SNnum); 
    #ifdef DEBUG 
       Serial.print(F("SN: "));
       Serial.println(SNnum);
    #endif                        
    const char* Hostname_complete = allSN.c_str();       
    WiFi.setHostname(Hostname_complete);
    delay(100);                  
    
    wifiMulti.addAP(WiFi_SSID, WiFi_PASS);

    while(wifiMulti.run()!=WL_CONNECTED){
       delay(1000);
       #ifdef DEBUG
          Serial.println(F("Wi-Fi Connecting"));
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
       #endif    
    }// end connected
    
    interval = wait_send;
  }//end ap_manager  
  
  serverName = "http";
  if(USE_SSL == 1){
     serverName += "s";
  }
  serverName += "://"+String(SERV_IP)+":"+String(SERV_PORT)+"/api/sensor"; 

  server.on("/" + String(AES_SEC), [](){                      // ex for on: https://192.168.88.207/0123456789abcdff?re=1
    if(server.hasArg("re")){        
      int o = atoi(server.arg("re").c_str());    
      if(o==1) {
         set_rele(1);                                         // relay on
         #ifdef DEBUG
           Serial.println(F("WEB RELAY ON"));
         #endif  
         server.send(200, "text/html", String(o));
      }
      else if(o==0) {
         set_rele(0);                                         // relay off
         #ifdef DEBUG
           Serial.println(F("WEB RELAY OFF"));
         #endif    
         server.send(200, "text/html", String(o));      
      }
    }
    else{
       server.send(404, "text/html", "ERR");                  // not found
    }
     
  });
   
  server.begin();
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
     dnsServer.processNextRequest();       
     server.handleClient();               
     if(APtime+APtimeout <= nowTime){            
        #ifdef DEBUG
           Serial.println(F("AP timeout -> restarting"));
           delay(1000);
        #endif   
        reboot();
     }// end if  
     return;  
 }//end if AP manager
 else{
   server.handleClient();                                    
   
   if(nowTime - prevTime >= interval){
    send_to_OSPy = true;                                      // xx second timer for sending data
    prevTime = nowTime;
   }// end timer

   if(nowTime - prevTikTime >= 1000){                         // second timer
    prevTikTime = nowTime;
    if(SEN_TYPE == 1 || SEN_TYPE == 6){
      get_dry_contact();
    }     
    if(SEN_TYPE == 2 || SEN_TYPE == 6){
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
   }// end timer
      
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
     //mbedtls_aes_setkey_enc(&aes, (const unsigned char*) aeskey, strlen(aeskey) * 8 );
     //mbedtls_aes_crypt_ecb(&aes, MBEDTLS_AES_ENCRYPT, (const unsigned char*)aesinput, aesoutput);
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
     #endif  

     #ifdef DEBUG
        Serial.println(F("SENDing data"));
     #endif
        
     HTTPClient http;

     #ifdef DEBUG
        Serial.print(F("TO SERVER: "));
        Serial.println(serverName);
     #endif
     
     http.begin(serverName);
     if(USE_AUTH == 1){                                           // if enabled authorisation 
        String auth = base64::encode(String(AUTH_NAME) + ":" + String(AUTH_PASS));
        #ifdef DEBUG
           Serial.print(F("Login: "));  Serial.print(String(AUTH_NAME)); Serial.print(F(":")); Serial.println(String(AUTH_PASS));
           Serial.print(F("Login base64: ")); Serial.println(auth);
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
           if(SEN_TYPE == 1 || SEN_TYPE == 6){      // dry contact
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
              httpRequestData += int(curTemp_1*10.0);    // ex: 245 is 24.5CS
              httpRequestData += "\",\"temp2\":\"";
              httpRequestData += int(curTemp_2*10.0); 
              httpRequestData += "\",\"temp3\":\"";
              httpRequestData += int(curTemp_3*10.0);
              httpRequestData += "\",\"temp4\":\"";
              httpRequestData += int(curTemp_4*10.0);                                            
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
         
    #ifdef DEBUG       
       Serial.println(httpRequestData);       
       int httpResponseCode = http.POST(httpRequestData);
       Serial.print(F("HTTP Response code: "));
       Serial.println(httpResponseCode);
       /* https://cs.wikipedia.org/wiki/Stavov%C3%A9_k%C3%B3dy_HTTP
        * 408 Request Timeout
        * 200 OK
        * -1 ERR Connection
        */
    #endif
    
    if(httpResponseCode==200){
      #ifdef DEBUG
         Serial.print(F("Sending OK, wait: ")); 
      #endif   
      interval = wait_send;
    }
    else{
      #ifdef DEBUG
         Serial.print(F("Sending Error, wait: ")); 
      #endif   
      interval = 5000;
    }
    #ifdef DEBUG
       Serial.print(interval/1000); Serial.println(F(" seconds."));
    #endif   

    http.end();
    send_to_OSPy = false;
    #ifdef DEBUG
       Serial.print(F("\n"));
    #endif
  }// end sending data
 }//end else ap manager   
}// end loop

// HELPERS****************************************************************************************************************
void get_dry_contact(){
  pinMode(input_sensor_dry, INPUT_PULLUP);
  delay(100);
  int test = digitalRead(input_sensor_dry);
  delay(100);
  if(LastCurDrcon != test){
    LastCurDrcon = test;
    #ifdef DEBUG
       Serial.print(F("CHANGE MOTION: "));
       Serial.println(LastCurDrcon);
    #endif   
    send_to_OSPy = true;
    interval = 1000;
  }
  curDrcon = !LastCurDrcon;  // curDrcon = 0 ex: open contact (only pull-up -> vcc to input pin)
}//end void

void get_leak_detector(){
// todo measure
  curLkdet = -1;

  if(curLkdet != LastcurLkdet){
     LastcurLkdet = curLkdet;
     #ifdef DEBUG
        Serial.print(F("LEAK DETECTOR: "));
        Serial.println(curLkdet);
     #endif
  }//end if      

}//end void

void get_moisture(){
// todo measure
  curHumi = -1;
  
  if(curHumi != LastcurHumi){
     LastcurHumi = curHumi;
     #ifdef DEBUG
        Serial.print(F("MOISTURE: "));
        Serial.println(curHumi);
     #endif 
  }//end if
}//end void

void get_motion(){
  pinMode(input_sensor_mot, INPUT_PULLUP);
  delay(10);
  int test = digitalRead(input_sensor_mot);
  delay(10);
  if(LastCurMoti != test){
    LastCurMoti = test;
    #ifdef DEBUG
       Serial.print(F("CHANGE MOTION: "));
       Serial.println(LastCurMoti);
    #endif   
    send_to_OSPy = true;
    interval = 1000;
  }
  curMoti = !LastCurMoti;  
}//end void

void get_temp(){
  int timeout;
  // DS1
  if(DS_1_OK){
  timeout = 3; // 3x trying read temperature  
  do{
     DS1sensors.requestTemperatures();
     delay(100);
     curTemp_1 = DS1sensors.getTempCByIndex(0);
     if(LastcurTemp_1 != curTemp_1){
        LastcurTemp_1 = curTemp_1;
        #ifdef DEBUG
           Serial.print(F("DS1: "));
           Serial.print(curTemp_1);
           Serial.println(F(" C")); 
        #endif   
     }//end if   
     timeout--;
     if(timeout == 0) break;
  }while(curTemp_1 == -127 or curTemp_1 == -85); 
  }//end DS OK
  
  if(SEN_TYPE == 6){ // multi sensor
  // DS2
  if(DS_2_OK){
  timeout = 3; // 3x trying read temperature
  do{
     DS2sensors.requestTemperatures();
     delay(100);
     curTemp_2 = DS2sensors.getTempCByIndex(0);
     if(LastcurTemp_2 != curTemp_2){
        LastcurTemp_2 = curTemp_2;     
        #ifdef DEBUG
           Serial.print(F("DS2: "));
           Serial.print(curTemp_2);
           Serial.println(F(" C")); 
        #endif   
     }//end if   
     timeout--;
     if(timeout == 0) break;
  }while(curTemp_2 == -127 or curTemp_2 == -85); 
  }//end DS OK
   
  // DS3
  if(DS_3_OK){
  timeout = 3; // 3x trying read temperature
  do{
     DS3sensors.requestTemperatures();
     delay(100);
     curTemp_3 = DS3sensors.getTempCByIndex(0);
     if(LastcurTemp_3 != curTemp_3){
        LastcurTemp_3 = curTemp_3;     
        #ifdef DEBUG
           Serial.print(F("DS3: "));
           Serial.print(curTemp_3);
           Serial.println(F(" C")); 
        #endif   
     }//end if   
     timeout--;
     if(timeout == 0) break;
  }while(curTemp_3 == -127 or curTemp_3 == -85); 
  }//end DS OK
  
  // DS4
  if(DS_4_OK){
  timeout = 3; // 3x trying read temperature
  do{
     DS4sensors.requestTemperatures();
     delay(100);
     curTemp_4 = DS4sensors.getTempCByIndex(0);
     if(LastcurTemp_4 != curTemp_4){
        LastcurTemp_4 = curTemp_4;     
        #ifdef DEBUG
           Serial.print(F("DS4: "));
           Serial.print(curTemp_4);
           Serial.println(F(" C")); 
        #endif   
     }//end if   
     timeout--;
     if(timeout == 0) break;
  }while(curTemp_4 == -127 or curTemp_4 == -85);   
  }//end DS OK  
  }//end sen_type==6
}//end void

bool get_ap_button(){
  if(ap_manager) return false;
  
  pinMode(input_ap_manager, INPUT_PULLUP);
  delay(10);
  if(digitalRead(input_ap_manager)==LOW){
    #ifdef DEBUG
        Serial.println(F("BUTTON AP MANAGER?"));
    #endif
    delay(2000);
  }  
  if(digitalRead(input_ap_manager)==LOW){
    #ifdef DEBUG
       Serial.println(F("Confirmed BUTTON AP MANAGER"));
    #endif   
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
  #endif   
}// end void

void get_mac(){
  MACadr = String(WiFi.macAddress());
  #ifdef DEBUG
     Serial.print(F("MAC: "));
     Serial.println(MACadr);
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
  #endif   
}// end void

void get_vdd(){
   curVdd = battery_read();
}//end void

float battery_read(){
    //read battery voltage per %
    long sum = 0;                  // sum of samples taken
    float voltage = 0.0;           // calculated voltage
    float output = 0.0;            //output value
    //const float battery_max = 3.6; //maximum voltage of battery
    //const float battery_min = 3.3; //minimum voltage of battery before shutdown

    //float R1 = 100000.0; // resistance of R1 (100K)
    //float R2 = 10000.0;  // resistance of R2 (10K)

    for (int i = 0; i < 500; i++){
        sum += adc1_get_voltage(ADC1_CHANNEL_0);
        delayMicroseconds(1000);
    }
    // calculate the voltage
    voltage = sum / (float)500;
    voltage = (voltage * 1.1) / 4096.0; //for internal 1.1v reference
    // use if added divider circuit
    // voltage = voltage / (R2/(R1+R2));
    //round value by two precision
    voltage = roundf(voltage * 100) / 100;
    if(voltage != LastcurVdd){
       LastcurVdd = voltage;
       #ifdef DEBUG
          Serial.print(F("Voltage: "));
          Serial.println(voltage, 2);
       #endif  
    }//end if    
    //output = ((voltage - battery_min) / (battery_max - battery_min)) * 100;
    /*if (output < 100)
        return output;
    else
        return 100.0f;
    */
    return voltage;
}//end void

void reboot(){                
  //WiFi.disconnect(false, true);
   #ifdef DEBUG
     Serial.println(F("RESTARTING ESP32"));
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
  #endif   
  return res;
}//end string

boolean captivePortal(){ // Redirect to captive portal if we got a request for another domain. Return true in that case so the page handler do not try to handle the request again.
  if(!isIp(server.hostHeader())){
    #ifdef DEBUG
        Serial.println(F("Request redirected to captive portal"));
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
  #endif
  server.sendHeader("Cache-Control", "no-cache, no-store, must-revalidate");
  server.sendHeader("Pragma", "no-cache");
  server.sendHeader("Expires", "-1");
  server.sendHeader("Content-Length", String(message.length()));
  server.send(404, "text/plain", message);
}// end void

//AP page
// green color #397F19
static const char html_ap_header[] PROGMEM = R"=====(<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no"/><title>{v}</title>)=====";
static const char html_ap_style[] PROGMEM = R"=====(<style>.c{text-align: center;} div,input{padding:5px;font-size:1em;} input{width:95%;} body{text-align: center;font-family:verdana;} button{border:0;border-radius:0.3rem;background-color:#397F19;color:#fff;line-height:2.4rem;font-size:1.2rem;width:100%;} .q{float: right;width: 64px;text-align: right;} .l{background: url("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAMAAABEpIrGAAAALVBMVEX///8EBwfBwsLw8PAzNjaCg4NTVVUjJiZDRUUUFxdiZGSho6OSk5Pg4eFydHTCjaf3AAAAZElEQVQ4je2NSw7AIAhEBamKn97/uMXEGBvozkWb9C2Zx4xzWykBhFAeYp9gkLyZE0zIMno9n4g19hmdY39scwqVkOXaxph0ZCXQcqxSpgQpONa59wkRDOL93eAXvimwlbPbwwVAegLS1HGfZAAAAABJRU5ErkJggg==") no-repeat left center;background-size: 1em;}</style>)=====";
static const char html_ap_script[] PROGMEM = R"=====(<script>function c(l){document.getElementById('s').value=l.innerText||l.textContent;document.getElementById('p').focus();}</script>)=====";
static const char html_ap_header_end[] PROGMEM = R"=====(</head><body><div style='text-align:left;display:inline-block;min-width:260px;'>)=====";
static const char html_ap_portal_options[] PROGMEM = R"=====(<form action="/wifi" method="get"><button>Wi-Fi Settings</button></form><br/><form action="/i" method="get"><button>Sensor Info</button></form><br/><form action="/c" method="post"><button>Sensor Settings</button></form><br/><form action="/r" method="post"><button>Restart</button></form><br/><form action="/EDF" method="post"><button>Default</button></form><br/><form action="/{m}" method="post"><button>Set relay to {n}</button></form>)=====";
static const char html_ap_item[] PROGMEM = R"=====(<div><a href='#p' onclick='c(this)'>{v}</a>&nbsp;<span class='q {i}'>{r}%</span></div>)=====";
static const char html_ap_form_start[] PROGMEM = R"=====(</br><form method='get' action='/wifisave'><input id='s' name='s' length=32 placeholder='SSID'><br/><input id='p' name='p' length=64 type='password' placeholder='password'><br/>)=====";
static const char html_ap_form_end[] PROGMEM = R"=====(<br/><button type='submit'>Save</button></form></br><form action="/" method="get"><button>Back</button></form>)=====";
static const char html_ap_scan_link[] PROGMEM = R"=====(<br/><form action="/wifi" method="get"><button>Search again</button></form></br>)=====";
static const char html_ap_saved[] PROGMEM = R"=====(<div><b>Settings saved!</br>It is necessary to restart the sensor</b></div></br><form action="/" method="get"><button>Back</button></form>)=====";
static const char html_ap_end[] PROGMEM = R"=====(</div><p>© www.pihrt.com ESP32 sensor for OpenSprinkler.</p></body></html>)=====";
static const char html_os_image[] PROGMEM = R"=====(<img alt='' src='data:image/png;base64,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'/>)=====";
// https://base64.guru/converter/encode/image
  
void WIFIAP_setup(){
     APtime = millis();
       
     WiFi.mode(WIFI_OFF);                        
     delay(1000);
     WiFi.mode(WIFI_AP); 
                             
     String s = "Sensor ESP32";    
     const char *Hostname_complete = s.c_str(); 
     WiFi.softAP(Hostname_complete, APpasswd); 
     delay(100);
     #ifdef DEBUG
        Serial.println(F("Soft AP Config"));
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
     #endif
    
     // Setup the DNS server redirecting all the domains to the apIP
     dnsServer.setErrorReplyCode(DNSReplyCode::NoError);
     dnsServer.start(DNS_PORT, "*", WiFi.softAPIP()); 
     
     // Not Found
     server.onNotFound(handleNotFound);
     
     // Home page
     server.on("/", []() {           
     String content = "";
     content += FPSTR(html_ap_header);
     content.replace("{v}", "Sensor ESP32");
     content += FPSTR(html_ap_style);
     content += FPSTR(html_ap_header_end);
     content += FPSTR(html_os_image);
     content += String(F("<h1>Sensor ESP32"));
     content += String(F("</h1>"));
     content += String(F("<h3>Main menu</h3>"));
     content += FPSTR(html_ap_portal_options);
     content += FPSTR(html_ap_end);
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
           #endif  
           server.sendHeader("Location", String("/"), true);   
           server.send(302, "text/plain", "");                  // redirect to home
        }
        if(t==0){
           set_rele(0);                                         // relay off
           #ifdef DEBUG
              Serial.println(F("AP RELAY OFF"));
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
        #endif    
     if(n==0){
        #ifdef DEBUG
            Serial.println(F("No network found"));
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
    server.sendHeader("Content-Length", String(content.length()));
    server.send(200, "text/html", content);
    });     

    // Save Wi-Fi network
    server.on("/wifisave", []() {   
    #ifdef DEBUG
        Serial.print(F("SAVE SSID: "));
        Serial.println(server.arg("s").c_str());
    #endif
    if(server.hasArg("s")){
      setEEPROMString(offsetof(eepromdata_t, WiFi_SSID), elementSize(eepromdata_t, WiFi_SSID), server.arg("s"));
    }        
    #ifdef DEBUG
        Serial.print(F("SAVE PASS: "));
        Serial.println(server.arg("p").c_str());
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
    content += F("<dt><b>Leak detector</b></dt><dd>");
    content += String(curLkdet)+"%"; 
    content += F("</dd>");
    content += F("<dt><b>Moisture</b></dt><dd>");
    content += String(curHumi)+"%"; 
    content += F("</dd>"); 
    content += F("<dt><b>Motion</b></dt><dd>");
    content += String(curMoti); 
    content += F("</dd>");  
    content += F("</dl>");                     
    content += F("</br><form action=\"/\" method=\"get\"><button>Back</button></form>");
    content += FPSTR(html_ap_end);
    server.sendHeader("Content-Length", String(content.length()));
    server.send(200, "text/html", content);
    });   

    // Sensor settings
    server.on("/c", []() {  
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
    else           content += F(" ");
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
    else            content += F(" ");
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
    content += F("<dt><b>Sensor Communication</b></dt><dd>");
    content += F("<select name=\"v\" id=\"v\">");
    content += F("<option value=\"0\" "); if(SEN_TYPE == 0) content += F("selected");
    content += F(">Wi-Fi/LAN</option>");
    content += F("<option value=\"1\" "); if(SEN_TYPE == 1) content += F("selected");
    content += F(">Radio</option>");
    content += F("</select>");  
    content += F("</dd>");  
    content += F("</dl>");     
    content += F("</br><button type='submit'>Save</button></form>");
    content += F("</br><form action=\"/\" method=\"get\"><button>Back</button></form>");
    content += FPSTR(html_ap_end);
    server.sendHeader("Content-Length", String(content.length()));
    server.send(200, "text/html", content);
    });   

    // Sensor save
    server.on("/sensorsave", []() {   
    #ifdef DEBUG
      Serial.println(F("SAVING"));
    #endif          
    if(server.hasArg("o")){
      setEEPROMString(offsetof(eepromdata_t, SEN_NAME), elementSize(eepromdata_t, SEN_NAME), server.arg("o"));
      #ifdef DEBUG
        Serial.print(F("Sensor name: "));
        Serial.println(server.arg("o"));
      #endif
    }  
    
    if(server.hasArg("c")){
      setEEPROMString(offsetof(eepromdata_t, AES_KEY), elementSize(eepromdata_t, AES_KEY), server.arg("c"));
      #ifdef DEBUG
        Serial.print(F("AES key: "));
        Serial.println(server.arg("c"));
      #endif
    }  
    
    if(server.hasArg("d")){
      setEEPROMString(offsetof(eepromdata_t, AES_SEC), elementSize(eepromdata_t, AES_SEC), server.arg("d"));
      #ifdef DEBUG
        Serial.print(F("AES sec: "));
        Serial.println(server.arg("d"));
      #endif
    }  
         
    if(server.hasArg("g")){
      setEEPROMString(offsetof(eepromdata_t, AUTH_NAME), elementSize(eepromdata_t, AUTH_NAME), server.arg("g"));
      #ifdef DEBUG
        Serial.print(F("Auth name: "));
        Serial.println(server.arg("g"));
      #endif
    }   
      
    if(server.hasArg("h")){
      setEEPROMString(offsetof(eepromdata_t, AUTH_PASS), elementSize(eepromdata_t, AUTH_PASS), server.arg("h"));
      #ifdef DEBUG
        Serial.print(F("Auth pass: "));
        Serial.println(server.arg("h"));
      #endif
    } 
       
    if(server.hasArg("a")){
      setEEPROMString(offsetof(eepromdata_t, SERV_IP), elementSize(eepromdata_t, SERV_IP), server.arg("a"));
      #ifdef DEBUG
        Serial.print(F("OSPy IP: "));
        Serial.println(server.arg("a"));
      #endif
    }  
      
    if(server.hasArg("b")){
      setEEPROMString(offsetof(eepromdata_t, SERV_PORT), elementSize(eepromdata_t, SERV_PORT), server.arg("b"));
      #ifdef DEBUG
        Serial.print(F("OSPy PORT: "));
        Serial.println(server.arg("b"));
      #endif
    } 
     
    if(server.hasArg("v")){
      setEEPROMString(offsetof(eepromdata_t, SEN_COM), elementSize(eepromdata_t, SEN_COM), server.arg("v"));
      #ifdef DEBUG
        Serial.print(F("SEN com: "));
        Serial.println(server.arg("v"));
      #endif
    }
    
    if(server.hasArg("t")){
      setEEPROMString(offsetof(eepromdata_t, SEN_TYPE), elementSize(eepromdata_t, SEN_TYPE), server.arg("t"));
      #ifdef DEBUG
        Serial.print(F("SEN type: "));
        Serial.println(server.arg("t"));
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
    #endif        
    
    EEPROM.commit();
    initEEPROM(); 
    
    String content = FPSTR(html_ap_header);
    content.replace("{v}", "Settings Saved");
    content += FPSTR(html_ap_script);
    content += FPSTR(html_ap_style);
    content += FPSTR(html_ap_header_end);
    content += FPSTR(html_ap_saved);
    content += FPSTR(html_ap_end);
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
    server.sendHeader("Content-Length", String(content.length()));
    server.send(200, "text/html", content);
    });     
    
    server.begin();                         // starting http server
}//end WIFIAP_setup
