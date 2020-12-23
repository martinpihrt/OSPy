/*
 * Sensor for OSPy system 
 * Martin Pihrt - 23.12.2020
 * Arduino IDE >= 1.8.13
 * board ESP32 1.0.4 (https://github.com/espressif/arduino-esp32)
 * DOIT
 * checked: 
 *  1=Dry Contact OK
 *  2=Leak Detector TODO
 *  3=Moisture TODO
 *  4=Motion OK 
 *  5=Temperature OK
 *  
 *  TODO: webserver with setings page in AP mode, ssl (https) connection
*/
#define DEBUG            // Comment this line when DEBUG mode is not needed 

// ESP32
#include "WiFi.h"
#include "HTTPClient.h"
#include "base64.h"
#include <driver/adc.h>  // A/D converter on ESP32

// AES 
#include "mbedtls/aes.h" // https://tls.mbed.org/api/aes_8h.html#a0e59fdda18a145e702984268b9ab291a
mbedtls_aes_context aes; // https://www.dfrobot.com/blog-911.html
unsigned char aesoutput[16];

//USER SETUP ********************************************************************************************************************
char * aeskey          = "f99b5b744afcfc44";     // AES key for sensors. 16 character len (for all used sensors - the same code must be used in ospy option/sensors)
char * aesinput        = "0123456789abcdff";     // len 16 character (each sensor must have its own code!)                 
// Wi-Fi 
const char* ssid       = "ssid";
const char* password   = "pass";
// OSPy api login
byte   use_auth        = 0;                      // 0= no auth (1=authorisation name:pass in base64 code)
String authUsername    = "admin";                // name user for access to ospy only if use_auth=1
String authPassword    = "opendoor";             // password user for access to ospy only if use_auth=1
// OSPy address and port
String serverIP        = "192.168.88.217";
String port            = "8080";
byte use_ssl           = 0;                      // 0=http (1=https)   
// sensor type and communication
String sensorname      = "Icebox ESP32";         // name for this sensor
byte stype             = 5;                      // 5 is temperature sensor (1=Dry Contact, 2=Leak Detector, 3=Moisture, 4=Motion, 5=temperature)
byte scom              = 0;                      // 0 is Wi-Fi/Lan (1=Radio)
// send interval 
long wait_send         = 30000;                  // 30 sec loop for sending data 
// FW version
int fw_version         = 101;                    // ex: FW version 101 is 1.01
// input form sensors pin
byte input_sensor      = 26;                     // pin for all used sensors

//************************************************************************************************************************
// DS18B20
#include <OneWire.h>
#include <DallasTemperature.h>
#define ONE_WIRE_BUS input_sensor                // for one wire bus (DS18B20)
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

int curRssi, curPercent, curMoti, curDrcon;      // current RSSI, RSSI in percent, motion, dry contact
int LastCurMoti, LastCurDrcon;                   // last value for motion, dry contact 
unsigned long prevTikTime, prevTime, nowTime, interval;   // previous time for sec timer (millis), send data timer (millis), current time (millis)  
float curTemp, curVdd, curLkdet, curHumi;        // current temperature, voltage, leak detector, moisture
bool send_to_OSPy = true;                        // if true -> send data to api OSPy web page
String IPadr  = "";                              // current IP address
String MACadr = "";                              // current MAC address
String serverName = "";                          // server address

#ifdef DEBUG
 #define DEBUG_PRINT(x)     Serial.print(x)
 #define DEBUG_PRINTDEC(x)  Serial.print(x, DEC)
 #define DEBUG_PRINTLN(x)   Serial.println(x)
#else
 #define DEBUG_PRINT(x)
 #define DEBUG_PRINTDEC(x)
 #define DEBUG_PRINTLN(x)
#endif

//************************************************************************************************************************   
void setup() {
#ifdef DEBUG 
  Serial.begin(115200);
#endif  
  sensors.begin();
  delay(500);
  sensors.setResolution(11); // 11 bit. The resolution of the DS18B20 is configurable (9, 10, 11, or 12 bits), with 12-bit readings the factory default state. This equates to a temperature resolution of 0.5°C, 0.25°C, 0.125°C, or 0.0625°C
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    #ifdef DEBUG
       Serial.println(F("Wi-Fi Connecting"));
    #endif   
  }// end while
  #ifdef DEBUG
     Serial.println(F("Connected"));
  #endif   
  interval = wait_send;

  mbedtls_aes_init( &aes );
  mbedtls_aes_setkey_enc( &aes, (const unsigned char*) aeskey, strlen(aeskey) * 8 );
  mbedtls_aes_crypt_ecb(&aes, MBEDTLS_AES_ENCRYPT, (const unsigned char*)aesinput, aesoutput);
  mbedtls_aes_free( &aes );
  #ifdef DEBUG
    Serial.print(F("AES key: "));
    Serial.println(aeskey);
    Serial.print(F("AES secret: "));
    Serial.println(aesinput);
    Serial.print(F("AES: "));
    for (int i = 0; i < 16; i++) {
       char str[3];
       sprintf(str, "%02x", (int)aesoutput[i]);
       Serial.print(str);
    }
    Serial.println("");
  #endif  
  if(use_ssl == 1){
     serverName      = "https://"+serverIP+":"+port+"/api/sensor";
  }
  else{   
     serverName      = "http://"+serverIP+":"+port+"/api/sensor";
  }   
}// end setup
 
void loop() {
   nowTime = millis();                                          // actual millis time
   if(nowTime - prevTime >= interval){
    send_to_OSPy = true;                                        // timer for sending data
    prevTime = nowTime;
   }// end timer

   if(nowTime - prevTikTime >= 1000){                           // second timer
    prevTikTime = nowTime;
    if(stype==1){
       get_dry_contact();
    }     
    else if(stype==2){
      get_leak_detector();
    }     
    else if(stype==3){
      get_moisture();
    }     
    else if(stype==4){
      get_motion();
    }     
    else if(stype==5){
      get_temp();
    } 
   }// end timer
      
   if((WiFi.status() == WL_CONNECTED) && send_to_OSPy){         // if Wi-Fi connected and is time for sending
     get_rssi();
     get_mac();
     get_ip();
     get_vdd();

     HTTPClient http;
     http.begin(serverName);
     if(use_auth==1){                                           // if enabled authorisation 
        String auth = base64::encode(authUsername + ":" + authPassword);
        #ifdef DEBUG
           Serial.print(F("Login: "));  Serial.print(authUsername); Serial.print(F(":")); Serial.println(authPassword);
           Serial.print(F("Login base64: ")); Serial.println(auth);
        #endif   
        http.addHeader("Authorization", "Basic " + auth);
     }   
     String httpRequestData  = "do={\"ip\":\"";
           httpRequestData += IPadr;
           httpRequestData += "\",\"name\":\"";
           httpRequestData += sensorname;           
           httpRequestData += "\",\"mac\":\"";
           httpRequestData += MACadr;
           httpRequestData += "\",\"rssi\":\"";
           httpRequestData += int(curPercent);
           httpRequestData += "\",\"batt\":\"";
           httpRequestData += int(curVdd*10.0);         // ex: 125 is 12.5V
           httpRequestData += "\",\"stype\":\"";
           httpRequestData += int(stype);
           httpRequestData += "\",\"scom\":\"";
           httpRequestData += int(scom);  
           httpRequestData += "\",\"fw\":\"";
           httpRequestData += int(fw_version);   
           if(stype==1){      // dry contact
              httpRequestData += "\",\"drcon\":\"";
              httpRequestData += int(curDrcon);        // ex: 0 or 1 
           }           
           else if(stype==2){ // leak detector
              httpRequestData += "\",\"lkdet\":\"";
              httpRequestData += int(curLkdet*10.0);   // ex: 245 is 24.5%
           }           
           else if(stype==3){ // moisture
              httpRequestData += "\",\"humi\":\"";
              httpRequestData += int(curHumi*10.0);    // ex: 245 is 24.5%  
           }           
           else if(stype==4){ // motion
              httpRequestData += "\",\"moti\":\"";
              httpRequestData += int(curMoti);         // ex: 0 or 1
           }                                       
           else if(stype==5){ // temperature
              httpRequestData += "\",\"temp\":\"";
              httpRequestData += int(curTemp*10.0);    // ex: 245 is 24.5CS
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
         
    #ifdef DEBUG       
       Serial.println(httpRequestData);       
       int httpResponseCode = http.POST(httpRequestData);
       Serial.print(F("HTTP Response code: "));
       Serial.println(httpResponseCode);
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
  }// end sending data  
}// end loop

//*************************************************************************************

void get_dry_contact(){
  pinMode(input_sensor, INPUT_PULLUP);
  delay(100);
  int test = digitalRead(input_sensor);
  delay(100);
  //Serial.print(F("INPUT DRY CONTACT: "));
  //Serial.println(test);
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
  #ifdef DEBUG
     Serial.print(F("LEAK DETECTOR: "));
     Serial.println(curLkdet);
  #endif   
  curLkdet = 100;
}//end void

void get_moisture(){
// todo measure
  #ifdef DEBUG
     Serial.print(F("MOISTURE: "));
     Serial.println(curHumi);
  #endif 
  curHumi = 100;
}//end void

void get_motion(){
  pinMode(input_sensor, INPUT_PULLUP);
  delay(100);
  int test = digitalRead(input_sensor);
  delay(100);
  //Serial.print(F("INPUT MOTION: "));
  //Serial.println(test);
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
  int timeout = 10; // 10x trying read temperature
  do{
     sensors.requestTemperatures();
     delay(100);
     curTemp = sensors.getTempCByIndex(0);
     #ifdef DEBUG
        Serial.print(curTemp);
        Serial.println(F(" C")); 
     #endif   
     timeout--;
     if(timeout == 0) break;
  }while(curTemp == -127 or curTemp == -85);   
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

    float R1 = 100000.0; // resistance of R1 (100K)
    float R2 = 10000.0;  // resistance of R2 (10K)

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
    #ifdef DEBUG
       Serial.print(F("Voltage: "));
       Serial.println(voltage, 2);
    #endif   
    //output = ((voltage - battery_min) / (battery_max - battery_min)) * 100;
    /*if (output < 100)
        return output;
    else
        return 100.0f;
    */
    return voltage;
}//end void
