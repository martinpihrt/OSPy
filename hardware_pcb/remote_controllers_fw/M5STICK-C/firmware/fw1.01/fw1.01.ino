/* 
OSPy Controller for OSPy M5stick-C https://shop.m5stack.com/products/stick-c
Martin Pihrt
Arduino IDE: 1.8.15
Espressif verze 1.0.6 https://github.com/espressif/arduino-esp32

* FW:1.01 - 5.7.2021
  Add checker for enable or disable read NTP time. Add baterry status (percentage and rectangle).
  Added battery saving (after 10 seconds the brightness of the LCD display decreases). If the any button is pressed, the brightness is restored to maximal brightness.
 
* FW:1.00 - 2.6.2021
  Initial version. Run AP manager: push power button + left button >2sec, next release power button
  AP manager SSID: OSPy-Controller-M5stick, default password: ospy-m5stick-c, browser IP: 192.168.1.1
  Uploading new firmware default password: fg4s5b.s,trr7sw8sgyvrDfg

OSPy API
 http(s)://[ip|name]:[port]/api/..
 In Header for http GET/POST response: Header("Authorization", "Basic " "Username:Password") 
 ex: program 8 runnow ->  https://192.168.88.247:8080/api/programs/7 POST do=runnow
*/

#define DEBUG                                                            // serial debug
//#define PRINT_BATT                                                       // battery percent data
//#define PRINT_IMU                                                        // xyz data
//#define PRINT_RSSI                                                       // RSSI signal strength 
//#define PRINT_TIME                                                       // date time print

// FW version
int FW_VERSION = 101;                                                    // ex: FW version 101 is 1.01

#include <M5StickC.h>                                                    // https://github.com/m5stack/m5-docs/blob/master/docs/en/api/lcd.md
// docs https://docs.m5stack.com/en/arduino/arduino_home_page?id=m5stickc_api
#include <WiFi.h>
#include <WiFiMulti.h>
#include <HTTPClient.h>
#include "base64.h"
#include "time.h"                                                        // time.h is the ESP32 native time library which does graceful NTP server synchronization
#include <ArduinoJson.h>                                                 // https://arduinojson.org/?utm_source=meta&utm_medium=library.properties
#include <EEPROM.h>
#include <WebServer.h>
#include <WiFiAP.h>
#include <Update.h>

WebServer server(80);
WiFiMulti wifiMulti;

// IN, OUT
const int ext0 = 37;                                                     // button front on case (SEND)
const int ext1 = 39;                                                     // button left on case (SELECT)
const int led  = 10;                                                     // red led (LOW ON, HIGH OFF)
const byte brightness = 12;                                              // brightness LCD 8-12

// helpers
float accX, accY, accZ;                                                  // IMU x,y,z
float temperature;                                                       // IMU temperature
bool change_rotation = true;                                             // LCD rotation (from IMU x)
bool no_change_rotation = true;                                          // no LCD rotation (from IMU x)
bool last_json_read;                                                     // downloading from ospy (true = OK)
bool setup_ok;                                                           // if setup has end is true
bool last_ext0, last_ext1;                                               // last buttons state
bool send_cmd;                                                           // en or disable send to OSPy
bool is_ntp_ok;                                                          // true if NTP time is OK
int pgm_menu;                                                            // program menu on LCD
unsigned long last_millis;                                               // second timer
unsigned long last_btn_click;                                            // last millis if button clicked
unsigned long lcd_save_dimmer = 10000;                                   // decrease the brightness of the LCD after this time 
int try_sending = 3;                                                     // 3x repeating send cmd if err
String query_cmd, query_pgm, query_json;                                 // cmd do=xx, pgm nr for send, patch for read json from ospy

unsigned long APtimeout = 600000;                                        // 10 minutes timeout for AP manager
unsigned long APtime;                                                    // AP (ms now for timeout)
unsigned long APtimeLCD;                                                 // time counter to reboot if AP manager is active
bool ap_manager = false;                                                 // AP manager

// program name from OSPy...api/programs as JSON
char pgm_name[50][32] = {};                                              // here is max 50 programs with 32 char in name from JSON   
int pgm_count;

// settings from eeprom 
char WIFI_SSID[33];
char WIFI_PASS[33];   
char AUTH_NAME[33];      
char AUTH_PASS[33]; 
char NTP_SERVER[33]; 
long DAY_OFFSET; 
long GMT_OFFSET; 
char OSPY_ADDR[41]; 
char UPLOAD_PASS[33];   
char AP_WIFI_PASS[33];

#ifdef DEBUG
 #define DEBUG_PRINT(x)     Serial.print(x) 
 #define DEBUG_PRINTDEC(x)  Serial.print(x, DEC) 
 #define DEBUG_PRINTLN(x)   Serial.println(x)
 #define DEBUG_FLUSH()      Serial.flush()
#else
 #define DEBUG_PRINT(x)
 #define DEBUG_PRINTDEC(x)
 #define DEBUG_PRINTLN(x)
 #define DEBUG_FLUSH()
#endif

// date and time compilation
#define CompilerTIME __TIME__ // time hh:mm:ss 
#define CompilerDATE __DATE__ // date M mm dd yyyy

// throw compilation error if there board is not ESP32
#if not defined(ESP32)
   #error "Error! The selected board is not ESP32!"
#endif

#define SECS_PER_MIN  (60UL)
#define SECS_PER_HOUR (3600UL)
#define SECS_PER_DAY  (SECS_PER_HOUR * 24L)
#define numberOfSeconds(_time_) (_time_ % SECS_PER_MIN)  
#define numberOfMinutes(_time_) ((_time_ / SECS_PER_MIN) % SECS_PER_MIN)
#define numberOfHours(_time_) (( _time_% SECS_PER_DAY) / SECS_PER_HOUR)
#define elapsedDays(_time_) ( _time_ / SECS_PER_DAY)

// EEPROM 
#define elementSize(type, element) sizeof(((type *)0)->element)

typedef struct { // EEPROM
  char MAGICNR[3];      
  char WIFI_SSID[33];
  char WIFI_PASS[33];   
  char AUTH_NAME[33];      
  char AUTH_PASS[33]; 
  char NTP_SERVER[33]; 
  char DAY_OFFSET[9]; 
  char GMT_OFFSET[9]; 
  char OSPY_ADDR[41]; 
  char UPLOAD_PASS[33];   
  char AP_WIFI_PASS[33];
} eepromdata_t;
  
void setup() {
   pinMode(ext0, INPUT_PULLUP);
   pinMode(ext1, INPUT_PULLUP);
   pinMode(led, OUTPUT);
   digitalWrite(led, HIGH);
   
   Serial.begin(115200);
   delay(100);
   DEBUG_PRINTLN(F("SETUP"));
   DEBUG_FLUSH();   
   
   DEBUG_PRINT(F("FW:"));
   DEBUG_PRINTLN(FW_VERSION);
   DEBUG_FLUSH();
   delay(100);
   
   M5.begin();
   M5.Lcd.setRotation(1);
   M5.IMU.Init();
   M5.Axp.ScreenBreath(brightness);           // 7-12 (7 off, 12 max)
   //lcd_qr("https://github.com/martinpihrt/OSPy");
   //delay(3000);
   lcd_home();    // OSPy Controller

   EEPROM.begin(sizeof(eepromdata_t) + 10);   // we start working with EEPROM (10 bytes is only a reserve)
   get_EEPROM();

   if(digitalRead(ext1)==LOW){                // 2 sec confirm for AP manager
       M5.Lcd.setCursor(10, 45);
       M5.Lcd.setTextColor(WHITE);
       M5.Lcd.setTextSize(2);
       for(byte x=0; x<5; x++){
          M5.Lcd.printf(".");
          delay(100);
       } 
   }
   
   if(digitalRead(ext1)==LOW) {               // yes
      ap_manager = true;                      // enabling AP manager
   }

   if(!ap_manager){ 
      lcd_msg(0);    // lcd: Connecting to WI-FI
      lcd_home();    // OSPy Controller                 
      DEBUG_PRINTLN(F("WIFI-STA"));
      DEBUG_FLUSH();
      WiFi.disconnect(true);           
      delay(100);
      WiFi.mode(WIFI_STA);            
      delay(100);                     
      WiFi.setSleep(false);
      delay(100);
      String compile = ArduinoDateTimeCompile();            
      String SN;
      SN += "OSPy_M5STICK-C_";
      SN += String(compile);
      const char *Hostname_complete = SN.c_str();
      WiFi.setHostname(Hostname_complete);
      delay(100);
      DEBUG_PRINT(F("HOST:"));
      DEBUG_PRINTLN(Hostname_complete);
      DEBUG_FLUSH();
   
      wifiMulti.addAP(WIFI_SSID, WIFI_PASS);
   
      while (wifiMulti.run() != WL_CONNECTED) { 
         digitalWrite(led, LOW);
         delay(250);
         digitalWrite(led, HIGH);
         delay(250);
      }

      lcd_msg(4);                      // LCD: Reading NTP pls wait
      lcd_home();                      // OSPy Controller
      lcd_rssi();
      lcd_bat_perc();                  // LCD: show batt %
   
      configTime(GMT_OFFSET, DAY_OFFSET, NTP_SERVER);
      delay(1500);
      get_ntp_time();
      delay(1500);
      get_ntp_time();
   
      get_mac();
      get_ip();
   
      lcd_msg(3);                      // LCD: Reading PGM
      lcd_home();                      // OSPy Controller
      lcd_rssi();                      // LCD: show rssi %
      lcd_bat_perc();                  // LCD: show batt %
      if(is_ntp_ok) lcd_time();        // LCD: show time 
     
      if(get_ospy_pgm()) {
        lcd_msg(2);                    // LCD: Ready... select PGM
        last_json_read = true;
      }
      else lcd_msg(9);                 // LCD: Not reading any error

      lcd_home();                      // OSPy Controller
      lcd_rssi();                      // LCD: show rssi %
      lcd_bat_perc();                  // LCD: show batt %
      if(is_ntp_ok) lcd_time();        // LCD: show time 
      
      DEBUG_PRINTLN(F("SETUP-OK"));
      DEBUG_FLUSH();
   }//end not AP manager
   else{
      lcd_msg(10);   // lcd: Starting AP
      lcd_home();    // OSPy Controller
      delay(500);
      WIFIAP_setup();                                             // AP manager routine -> AP manager is active
   }//end
   setup_ok = true;
   last_btn_click = millis();
}//end void

void loop() {
  if(ap_manager){                                                 // manager is active                              
     server.handleClient();               
     if(APtime+APtimeout <= millis()){            
        DEBUG_PRINTLN(F("AP:timeout-restarting"));
        delay(1000);
        reboot();
     }// end if  
     if(millis() - last_millis >= 1000){                          // 1 second timer for print timeout
        last_millis = millis();
        get_IMU();                                                // get x,y,z and temperature
        APtimeLCD = (APtime+APtimeout)-millis();
        DEBUG_PRINT(F("AP:Time-to-reboot:"));
        if(numberOfMinutes(APtimeLCD/1000)<10) DEBUG_PRINT(F("0"));
        DEBUG_PRINT(numberOfMinutes(APtimeLCD/1000));  
        DEBUG_PRINT(F(":"));    
        if(numberOfSeconds(APtimeLCD/1000)<10) DEBUG_PRINT(F("0"));
        DEBUG_PRINTLN(numberOfSeconds(APtimeLCD/1000));
        digitalWrite(led, !digitalRead(led)); 
        lcd_ap_manager();
        lcd_battery();     
     }// end timer
     return;  
  }//end if AP manager
  else{
  // not AP manager 
  if((wifiMulti.run() != WL_CONNECTED)) {
    DEBUG_PRINTLN(F("NO-WIFI"));
    DEBUG_FLUSH();
    reboot();
  }// end if((wifiMulti.run()

  if(millis()-last_millis >= 1000){ // sec timer for refresh LCD display
     last_millis = millis();
     get_IMU();                     // get x,y,z and temperature
     lcd_home();                    // OSPy Controller
     lcd_rssi();                    // LCD: show rssi %
     lcd_bat_perc();                // LCD: show batt %
     if(is_ntp_ok) lcd_time();      // LCD: show time
  }

  if(millis() > (last_btn_click + lcd_save_dimmer)){
     M5.Axp.ScreenBreath(8);              // minimum brightness LCD (7=off)
  }
  else{
     M5.Axp.ScreenBreath(brightness);     // default brightness LCD (default is 12=maximum)    
  }// end brightness timmer

  byte inext0 = digitalRead(ext0);  // PGM start
  if (inext0) last_ext0 = true;           
  if (!inext0 && last_ext0) {             
    last_ext0 = false;                    
    DEBUG_PRINTLN(F("BTN-EXT0"));
    DEBUG_FLUSH();
    if(sizeof(pgm_name)>0){
       send_cmd = true;
       lcd_msg(6);                  // LCD: Starting PGM
       lcd_home();                  // OSPy Controller
       lcd_rssi();                  // LCD: show rssi %
       lcd_bat_perc();              // LCD: show batt %
       if(is_ntp_ok) lcd_time();    // LCD: show time
       // ex: "https://192.168.88.247:8080/api/programs/7"
       query_cmd  = "do=runnow";    // for testing "do=stop"
       query_pgm  = String(OSPY_ADDR) + "programs/" + String(pgm_menu);
       last_btn_click = millis();
    }//end sizeof   
  }
  
  byte inext1 = digitalRead(ext1);  // PGM shift
  if (inext1) last_ext1 = true;            
  if (!inext1 && last_ext1) {             
    last_ext1 = false;                     
    DEBUG_PRINTLN(F("BTN-EXT1"));
    DEBUG_FLUSH();
    pgm_menu++;
    DEBUG_PRINT(F("MENU-PGM:"));
    DEBUG_PRINTLN(pgm_menu+1);
    DEBUG_FLUSH();
    if(sizeof(pgm_name)>0) lcd_msg(8);  // LCD: PGM: number xx with name
    else lcd_msg(2);                    // LCD: Ready select PGM or Not program
    lcd_home();                         // LCD: OSPy Controller
    lcd_rssi();                         // LCD: show rssi %
    lcd_bat_perc();                     // LCD: show batt %
    if(is_ntp_ok) lcd_time();           // LCD: show time  
    last_btn_click = millis();
  }

  if(send_cmd){
    digitalWrite(led, LOW);
    DEBUG_PRINTLN(F("SEND-CMD"));
    DEBUG_PRINT(F("TRY:"));
    DEBUG_PRINTLN(try_sending);
    DEBUG_FLUSH();
        
    if(send_to_ospy(query_cmd) && try_sending>0){
       send_cmd = false;
       DEBUG_PRINTLN(F("SEND-OK"));
       DEBUG_FLUSH();
       try_sending = 3;
       digitalWrite(led, HIGH);
       lcd_msg(2);                      // LCD: Ready select PGM
       lcd_home();                      // OSPy Controller
       lcd_rssi();                      // LCD: show rssi %
       lcd_bat_perc();                  // LCD: show batt %
       if(is_ntp_ok) lcd_time();        // LCD: show time 
    }
    else{
       DEBUG_PRINTLN(F("ERR-SEND"));
       DEBUG_FLUSH();
       delay(2000);
       try_sending--;
    }//end else

    if(try_sending==0){
      send_cmd=false;
      try_sending = 3;
      digitalWrite(led, HIGH);
      lcd_msg(7);                       // LCD: Not sending any error
      lcd_home();                       // OSPy Controller
      lcd_rssi();                       // LCD: show rssi %
      lcd_bat_perc();                   // LCD: show batt %
      if(is_ntp_ok) lcd_time();         // LCD: show time       
    }//end try
  }//end send_cmd
  
  }//end not AP manager
}//end loop

bool send_to_ospy(String httpRequestData){
    String auth = base64::encode(String(AUTH_NAME) + ":" + String(AUTH_PASS));
    int httpResponseCode;
    
    DEBUG_PRINT(F("SERVER:"));
    DEBUG_PRINTLN(query_pgm);
    DEBUG_PRINT(F("LOGIN-NAME:"));
    DEBUG_PRINTLN(AUTH_NAME);
    DEBUG_PRINT(F("LOGIN-PASS:"));
    DEBUG_PRINTLN(AUTH_PASS);
    DEBUG_PRINT(F("LOGIN-BASE64:"));
    DEBUG_PRINTLN(auth); 
    DEBUG_PRINT(F("QUERY:"));
    DEBUG_PRINTLN(httpRequestData);
    DEBUG_FLUSH();
         
    HTTPClient http;
    http.setTimeout(10000); // 10 Seconds timeout
    http.begin(query_pgm);
    http.addHeader("Authorization", "Basic " + auth);
    httpResponseCode = http.POST(httpRequestData);
    DEBUG_PRINT(F("CODE:"));
    DEBUG_PRINTLN(httpResponseCode);   
    DEBUG_FLUSH(); 
    http.end();
                              // -11 ospy bug? 
    if(httpResponseCode==200 || httpResponseCode==-11) return true; // 200 OK, -11 timeout?
    else return false;
}//end bool

bool get_ospy_pgm(){
    String auth = base64::encode(String(AUTH_NAME) + ":" + String(AUTH_PASS));
    int httpResponseCode;
    query_json = String(OSPY_ADDR) + "programs/";
    
    DEBUG_PRINT(F("SERVER:"));
    DEBUG_PRINTLN(query_json);
    DEBUG_PRINT(F("LOGIN-NAME:"));
    DEBUG_PRINTLN(AUTH_NAME);
    DEBUG_PRINT(F("LOGIN-PASS:"));
    DEBUG_PRINTLN(AUTH_PASS);
    DEBUG_PRINT(F("LOGIN-BASE64:"));
    DEBUG_PRINTLN(auth); 
    DEBUG_FLUSH();
         
    HTTPClient http;
    http.setTimeout(10000); // 10 Seconds timeout
    http.begin(query_json);
    http.addHeader("Authorization", "Basic " + auth);
    httpResponseCode = http.GET();
    DEBUG_PRINT(F("CODE:"));
    DEBUG_PRINTLN(httpResponseCode);   
    DEBUG_FLUSH(); 
    String payload = http.getString();
    DEBUG_PRINT(F("PAYLOAD:"));
    DEBUG_PRINTLN(payload);
    /* OSPy api/program/ JSON data
            'id': program.index,
         -> 'name': program.name,
            'stations': program.stations,
            'enabled': program.enabled,
            'type': program.type,
            'type_name': ProgramType.NAMES.get(program.type, ''),
            'type_data': program.type_data,
            'summary': program.summary(),
            'schedule': program.schedule,
            'modulo': program.modulo,
            'manual': program.manual,
            'start': program.start,
     */
    http.end();
    
    const int pay_len = payload.length();
    DEBUG_PRINT(F("JSON-LEN:"));
    DEBUG_PRINTLN(pay_len);
    if((!payload.startsWith("[{")) && (!payload.endsWith("}]"))) {
       lcd_msg(11);                                 // LCD: Ready... select PGM
       lcd_home();                                  // LCD: OSPy Controller
       lcd_rssi();                                  // LCD: show rssi %
       lcd_bat_perc();                              // LCD: show batt %
       if(is_ntp_ok) lcd_time();                    // LCD: show time 
       return false;
    }
    
    //StaticJsonDocument<500> doc;                  // <- a little more than 500 bytes in the stack
    DynamicJsonDocument doc(ESP.getMaxAllocHeap()); // https://arduinojson.org/v6/how-to/determine-the-capacity-of-the-jsondocument/

    DeserializationError err = deserializeJson(doc, payload);
    if(err) { // ERR
      DEBUG_PRINT(F("JSON-DESERIALIZE-ERR:"));
      DEBUG_PRINTLN(err.c_str());                   // https://arduinojson.org/v6/api/misc/deserializationerror/
      return false;
    }
    else{     // OK
       /* example JSON data from ospy (api/programs/)
       * [{"modulo": 10080, "schedule": [[1251, 1255], [2691, 2695], [4131, 4135], [5571, 5575], [7011, 7015], [8451, 8455], [9891, 9895]], "enabled": true, "id": 0, "type_data": [1251, 4, 30, 0, [0, 1, 2, 3, 4, 5, 6]], "name": "Z\u00e1hon", "stations": [4], "type_name": "DAYS_SIMPLE", "manual": false, "summary": "Pl\u00e1nova\u010d ve dnech Po \u00dat St \u010ct P\u00e1 So Ne", "start": 1622412000, "type": 0}, {"modulo": 10080, "schedule": [[720, 780], [2160, 2220], [3600, 3660], [5040, 5100], [6480, 6540], [7920, 7980], [9360, 9420]], "enabled": false, "id": 1, "type_data": [720, 60, 30, 0, [0, 1, 2, 3, 4, 5, 6]], "name": "Filtrace", "stations": [6], "type_name": "DAYS_SIMPLE", "manual": false, "summary": "Pl\u00e1nova\u010d ve dnech Po \u00dat St \u010ct P\u00e1 So Ne", "start": 1622412000, "type": 0}, {"modulo": 10080, "schedule": [[1287, 1295], [2727, 2735], [4167, 4175], [5607, 5615], [7047, 7055], [8487, 8495], [9927, 9935]], "enabled": true, "id": 2, "type_data": [1287, 8, 30, 0, [0, 1, 2, 3, 4, 5, 6]], "name": "Th\u016fje", "stations": [0], "type_name": "DAYS_SIMPLE", "manual": false, "summary": "Pl\u00e1nova\u010d ve dnech Po \u00dat St \u010ct P\u00e1 So Ne", "start": 1622412000, "type": 0}, {"modulo": 10080, "schedule": [[1258, 1264], [2698, 2704], [4138, 4144], [5578, 5584], [7018, 7024], [8458, 8464], [9898, 9904]], "enabled": true, "id": 3, "type_data": [1258, 6, 30, 0, [0, 1, 2, 3, 4, 5, 6]], "name": "Jalovec a krm\u00edtko", "stations": [3], "type_name": "DAYS_SIMPLE", "manual": false, "summary": "Pl\u00e1nova\u010d ve dnech Po \u00dat St \u010ct P\u00e1 So Ne", "start": 1622412000, "type": 0}, {"modulo": 10080, "schedule": [[1268, 1272], [2708, 2712], [4148, 4152], [5588, 5592], [7028, 7032], [8468, 8472], [9908, 9912]], "enabled": true, "id": 4, "type_data": [1268, 4, 30, 0, [0, 1, 2, 3, 4, 5, 6]], "name": "Lavi\u010dka", "stations": [2], "type_name": "DAYS_SIMPLE", "manual": false, "summary": "Pl\u00e1nova\u010d ve dnech Po \u00dat St \u010ct P\u00e1 So Ne", "start": 1622412000, "type": 0}, {"modulo": 10080, "schedule": [[1277, 1283], [2717, 2723], [4157, 4163], [5597, 5603], [7037, 7043], [8477, 8483], [9917, 9923]], "enabled": true, "id": 5, "type_data": [1277, 6, 30, 0, [0, 1, 2, 3, 4, 5, 6]], "name": "Bor\u016fvky", "stations": [1], "type_name": "DAYS_SIMPLE", "manual": false, "summary": "Pl\u00e1nova\u010d ve dnech Po \u00dat St \u010ct P\u00e1 So Ne", "start": 1622412000, "type": 0}, {"modulo": 10080, "schedule": [[1240, 1246], [2680, 2686], [4120, 4126], [5560, 5566], [7000, 7006], [8440, 8446], [9880, 9886]], "enabled": true, "id": 6, "type_data": [1240, 6, 30, 0, [0, 1, 2, 3, 4, 5, 6]], "name": "Vchod a ryb\u00edz", "stations": [5], "type_name": "DAYS_SIMPLE", "manual": false, "summary": "Pl\u00e1nova\u010d ve dnech Po \u00dat St \u010ct P\u00e1 So Ne", "start": 1622412000, "type": 0}, {"modulo": 10080, "schedule": [[420, 425], [1860, 1865], [3300, 3305], [4740, 4745], [6180, 6185], [7620, 7625], [9060, 9065]], "enabled": false, "id": 7, "type_data": [420, 5, 30, 0, [0, 1, 2, 3, 4, 5, 6]], "name": "UV lampa", "stations": [7], "type_name": "DAYS_SIMPLE", "manual": false, "summary": "Pl\u00e1nova\u010d ve dnech Po \u00dat St \u010ct P\u00e1 So Ne", "start": 1621807200, "type": 0}]
       */
       pgm_count = 0;
       DEBUG_PRINTLN(F("PGM-NAMES"));
       for(int r=0; r<15; r++){
          const char* pgm = doc[r]["name"];
          if(doc[r]["name"]) {
            strcpy(pgm_name[r], pgm);
            pgm_count++;
            DEBUG_PRINTLN(pgm);
          }
          else break;    // not any next name in JSON 
       }
       DEBUG_PRINT(F("PGM-COUNT:"));
       DEBUG_PRINTLN(pgm_count);
       DEBUG_FLUSH();    
    }//end else JSON DESERIALIZE OK    
       
    if(httpResponseCode==200) return true; // 200 OK
    else return false;
}//end bool

void reboot() {
  lcd_msg(5);   // LCD: rebooting
  lcd_home();   // LCD: OSPy Controller
  WiFi.disconnect(true);
  DEBUG_PRINTLN(F("REBOOT"));
  DEBUG_FLUSH();
  delay(2000);
  ESP.restart();
  /*
    ESP.reset() is a hard reset and can leave some of the registers in the old state which can lead to problems, its more or less like the reset button on the PC.
    ESP.restart() tells the SDK to reboot, so its a more clean reboot, use this one if possible.
    the boot mode:(1,7) problem is known and only happens at the first restart after serial flashing. if you do one manual reboot by power or RST pin all will work more info see: #1017
  */
}// end void

int get_rssi() {
  int rssi, percent;
  rssi = WiFi.RSSI();
  if (rssi <= -100) percent = 0;
  else if (rssi >= -50) percent = 100;
  else percent = 2 * (rssi + 100);
  #ifdef PRINT_RSSI 
     DEBUG_PRINT(F("SIGNAL:"));
     DEBUG_PRINTLN(percent);
     DEBUG_FLUSH();
  #endif   
  return percent;
}// end void

String get_mac() {
  String MACadr = "";
  MACadr = String(WiFi.macAddress());
  DEBUG_PRINT(F("MAC-STA:"));
  DEBUG_PRINTLN(MACadr);
  DEBUG_FLUSH();
  return MACadr;
}// end void

String get_ip() {
  String IPadr = "";
  IPadr  = String(WiFi.localIP()[0]);
  IPadr += "." + String(WiFi.localIP()[1]);
  IPadr += "." + String(WiFi.localIP()[2]);
  IPadr += "." + String(WiFi.localIP()[3]);
  DEBUG_PRINT(F("IPV4:"));
  DEBUG_PRINTLN(IPadr);
  DEBUG_FLUSH();
  return IPadr;
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

void lcd_home(){
  get_IMU();
  M5.Lcd.setCursor(10, 5);  // sloupec, radek text shora
  M5.Lcd.setTextColor(GREEN);
  M5.Lcd.setTextSize(2);
  M5.Lcd.printf("OSPy");
  M5.Lcd.setCursor(62, 8);
  M5.Lcd.setTextSize(1);
  M5.Lcd.printf("Controller");
}

void lcd_ap_manager(){
  get_IMU();
  M5.Lcd.fillScreen(BLACK);
  M5.Lcd.setCursor(10, 5);  // sloupec, radek text shora
  M5.Lcd.setTextColor(GREEN);
  M5.Lcd.setTextSize(2);
  M5.Lcd.printf("OSPy");
  M5.Lcd.setCursor(62, 8);
  M5.Lcd.setTextSize(1);
  M5.Lcd.printf("Controller");
  M5.Lcd.setCursor(10, 45);
  M5.Lcd.setTextColor(WHITE);
  M5.Lcd.setTextSize(2);
  M5.Lcd.printf("AP ");
  if(numberOfMinutes(APtimeLCD/1000)<10) M5.Lcd.printf("0");
  M5.Lcd.print(numberOfMinutes(APtimeLCD/1000));  
  M5.Lcd.printf(":");    
  if(numberOfSeconds(APtimeLCD/1000)<10) M5.Lcd.printf("0");
  M5.Lcd.print(numberOfSeconds(APtimeLCD/1000));
}

void lcd_rssi(){
  get_IMU();
  M5.Lcd.setTextSize(1);
  M5.Lcd.fillRect(125, 8, 140, 8, BLACK);
  M5.Lcd.setCursor(125, 8);
  int r = get_rssi();
  if(r<25) M5.Lcd.setTextColor(RED);
  else if(r>24 && r<70) M5.Lcd.setTextColor(YELLOW);
  else M5.Lcd.setTextColor(GREEN);
  M5.Lcd.print(r);
  M5.Lcd.print("%");
}

void lcd_bat_perc(){
  M5.Lcd.setTextSize(1);
  M5.Lcd.fillRect(62, 16, 140, 16, BLACK);
  M5.Lcd.setCursor(125, 16);
  int r = int(get_batPercentage());
  if(r<25) M5.Lcd.setTextColor(RED);
  else if(r>24 && r<70) M5.Lcd.setTextColor(YELLOW);
  else M5.Lcd.setTextColor(GREEN);
  M5.Lcd.print(r);
  M5.Lcd.print("%");
  
  // rectangle with battery percentage
  int s = int(get_batPercentage());
  int e = map(s,0,100,0,58);
  if(s>=70)              M5.Lcd.fillRect(62, 16, e, 4, GREEN);  
  else if(s>24 && s<70) M5.Lcd.fillRect(62, 16, e, 4, YELLOW);
  else                  M5.Lcd.fillRect(62, 16, e, 4, RED); 
}  

void lcd_time(){
  get_IMU();
  M5.Lcd.setTextSize(1);
  M5.Lcd.fillRect(10, 23, 115, 11, BLACK);
  M5.Lcd.setCursor(10, 25);
  M5.Lcd.setTextColor(GREEN);
  M5.Lcd.print(get_ntp_time());
}

void lcd_battery(){
  get_IMU();
  int Vaps = M5.Axp.GetVapsData();
  M5.Lcd.setTextSize(1);
  M5.Lcd.fillRect(10, 21, 125, 21, BLACK);
  M5.Lcd.setCursor(10, 25);
  M5.Lcd.setTextColor(GREEN);
  M5.Lcd.printf("Battery: %d mW", Vaps);  
}

float get_batPercentage(){
    float batVoltage = M5.Axp.GetBatVoltage();
    float b = (batVoltage < 3.2) ? 0 : (batVoltage - 3.2) * 100;
    #ifdef PRINT_BATT 
       DEBUG_PRINT(F("BAT:"));
       DEBUG_PRINTLN(b);
       DEBUG_FLUSH();
    #endif
    return b;
}    

void get_IMU(){ // rotation LCD screen
  M5.IMU.getAccelData(&accX, &accY, &accZ);
  //M5.IMU.getTempData(&temperature);
  //DEBUG_PRINT(F("IMU Temperature:"));
  //DEBUG_PRINTLN(temperature);
  #ifdef PRINT_IMU
     DEBUG_PRINT(F("IMU XYZ:"));
     DEBUG_PRINT(accX); DEBUG_PRINT(F(","));
     DEBUG_PRINT(accY); DEBUG_PRINT(F(","));
     DEBUG_PRINTLN(accZ);
     DEBUG_FLUSH();
  #endif   
  /*
  The display control of M5Stack is rotated by 90 °, and setRotation (1) is executed in M5.Lcd.begin ().
  0 to 3 rotate, 4 to 7 reverse and rotate.
  M5.Lcd.setRotation(1); is default
  */
  if(accX >= 0.1 && no_change_rotation){
    M5.Lcd.fillScreen(BLACK);
    M5.Lcd.setRotation(1);
    change_rotation = true;
    no_change_rotation = false;
    DEBUG_PRINTLN(F("LCD-ROTATION:1"));
    DEBUG_FLUSH();
    if(last_json_read){
       lcd_msg(2);                    // LCD: Ready... select PGM
       lcd_home();                    // LCD: OSPy Controller
       lcd_rssi();                    // LCD: show rssi %
       lcd_bat_perc();                // LCD: show batt %
       if(is_ntp_ok) lcd_time();      // LCD: show time 
    }
    else{
       if(setup_ok){                  // show after setup 
          lcd_msg(9);                 // LCD: Not reading any error
          lcd_home();                 // LCD: OSPy Controller
          lcd_rssi();                 // LCD: show rssi %
          lcd_bat_perc();             // LCD: show batt %
          if(is_ntp_ok) lcd_time();   // LCD: show time
       }           
    }//end else
  }//end no change
  
  if(accX < 0 && change_rotation){
    M5.Lcd.fillScreen(BLACK);
    M5.Lcd.setRotation(3);
    change_rotation = false;
    no_change_rotation = true;
    DEBUG_PRINTLN(F("LCD-ROTATION:3"));
    DEBUG_FLUSH();
    if(last_json_read){
       lcd_msg(2);                    // LCD: Ready... select PGM
       lcd_home();                    // LCD: OSPy Controller
       lcd_rssi();                    // LCD: show rssi %
       lcd_bat_perc();                // LCD: show batt %
       if(is_ntp_ok) lcd_time();      // LCD: show time 
    }
    else{
       if(setup_ok){                  // show after setup 
          lcd_msg(9);                 // LCD: Not reading any error
          lcd_home();                 // LCD: OSPy Controller
          lcd_rssi();                 // LCD: show rssi %
          lcd_bat_perc();             // LCD: show batt %
          if(is_ntp_ok) lcd_time();   // LCD: show time
       }           
    }//end else   
  }//end change
}//end void

void lcd_shift_msg(String msg, int msg_line){
  msg += F(" ");
  int msg_len = msg.length();
  DEBUG_PRINT(F("LCD-MSG-LEN:"));
  DEBUG_PRINTLN(msg_len);
  DEBUG_FLUSH();

  int d = 0;
  String _msg = "";
   
  while(msg_len>d){                            // check if msg non asci -> convert to
     String s = msg.substring(d, d+1);         // string in range from to
     char c[3];
     s.toCharArray(c, sizeof(c));              // string to char
     int w = c[0]-'0';                         // char to number
     if(!isAscii(w)){                          // if the value is within ASCII range (0~127)
        DEBUG_PRINT(F("ASCI-REPLACING:"));
        DEBUG_PRINTLN(w);
        DEBUG_FLUSH();
        if(w==-16)      _msg += " ";   // space
/*TODO  else if(w==) _msg += "e";  // ě -> e 
        else if(w==) _msg += "s";  // š -> s
        else if(w==) _msg += "c";  // č -> c
        else if(w==) _msg += "r";  // ř -> r
        else if(w==) _msg += "z";  // ž -> z
        else if(w==) _msg += "y";  // ý -> y
        else if(w==) _msg += "a";  // á -> a
        else if(w==) _msg += "i";  // í -> i
        else if(w==) _msg += "e";  // é -> e
        else if(w==) _msg += "u";  // ů -> u
        else if(w==) _msg += "u";  // ú -> u
        else if(w==) _msg += "E";  // Ě -> E
        else if(w==) _msg += "S";  // Š -> S
        else if(w==) _msg += "C";  // Č -> C
        else if(w==) _msg += "R";  // Ř -> R
        else if(w==) _msg += "Z";  // Ž -> Z
        else if(w==) _msg += "Y";  // Ý -> Y
        else if(w==) _msg += "A";  // Á -> A
        else if(w==) _msg += "I";  // Í -> I
        else if(w==) _msg += "E";  // É -> E
        else if(w==) _msg += "U";  // Ů -> U
        else if(w==) _msg += "U";  // Ú -> U   
*/                                                                     
        else            _msg += "_";  // replace _
     }
     else _msg += s;                  // copy in 1:1 out
     d++;
  }// end while

  DEBUG_PRINT(F("LCD-MSG:"));
  DEBUG_PRINTLN(_msg);
  DEBUG_FLUSH();

  msg_len = _msg.length();
  if(msg_len>12){                                   // The message does not fit and must be scrolled
     int line = msg_len;
     int i = 0;
     while(line>12){
        lcd_home();                                 // LCD: OSPy Controller
        lcd_rssi();                                 // LCD: show rssi %
        lcd_bat_perc();                             // LCD: show batt %
        if(is_ntp_ok) lcd_time();                   // LCD: show time
        M5.Lcd.setTextColor(WHITE);
        M5.Lcd.setTextSize(2);
        if(msg_line==1){
           M5.Lcd.fillRect(5, 45, 160, 45, BLACK);  // Delete previous and move text 
           M5.Lcd.setCursor(10, 45);
        }        
        if(msg_line==2){
           M5.Lcd.fillRect(5, 65, 160, 65, BLACK);  // Delete previous and move text 
           M5.Lcd.setCursor(10, 65);
        }   
        M5.Lcd.print(_msg.substring(i, i+12));       // 0 to 12, 1 to 13...
        line--;
        i++;
        delay(300);
     }
     delay(500);
     M5.Lcd.setTextColor(WHITE);
     M5.Lcd.setTextSize(2);
     if(msg_line==1){     
         M5.Lcd.fillRect(5, 45, 160, 45, BLACK);   // Delete previous and move text
         M5.Lcd.setCursor(10, 45);
     }     
     if(msg_line==2){     
         M5.Lcd.fillRect(5, 65, 160, 65, BLACK);   // Delete previous and move text
         M5.Lcd.setCursor(10, 65);
     }    
     M5.Lcd.print(_msg.substring(0, 12));           // Display the beginning of the message again
  }
  else{                                            // OK the message will fit on the display line (12 character)
     M5.Lcd.print(_msg);
  }   
}//end void  

void lcd_msg(byte text) { 
  get_IMU();
  M5.Lcd.fillScreen(BLACK);
  // line 1
  M5.Lcd.setCursor(10, 45);
  M5.Lcd.setTextColor(WHITE);
  M5.Lcd.setTextSize(2);
  if (text == 0) M5.Lcd.printf("Connecting");
  if (text == 1) M5.Lcd.printf("Wi-Fi conn");
  if (text == 2){
    if(pgm_count>0){
      M5.Lcd.printf("Ready...");
    }
    else{
      M5.Lcd.printf("Not set PGM");
    }
  }
  if (text == 3) M5.Lcd.printf("Reading PGM");
  if (text == 4) M5.Lcd.printf("Reading NTP");
  if (text == 5) M5.Lcd.printf("Rebooting!");
  if (text == 6) M5.Lcd.printf("Starting");
  if (text == 7) M5.Lcd.printf("Not sending!");
  if (text == 8){
    if(pgm_menu > pgm_count-1) pgm_menu = 0;
    if(pgm_count>0){
       M5.Lcd.printf("PGM: "); M5.Lcd.print(pgm_menu+1);
    }
  }
  if (text == 9) M5.Lcd.printf("Not reading!");
  if (text == 10) M5.Lcd.printf("Starting AP");
  if (text == 11) M5.Lcd.printf("PGM data");
  
  // line 2
  M5.Lcd.setCursor(10, 65);
  M5.Lcd.setTextColor(WHITE);
  M5.Lcd.setTextSize(2);
  if (text == 0) M5.Lcd.printf("to Wi-Fi");
  if (text == 1) M5.Lcd.printf("failed!");
  if (text == 2){
     if(pgm_count>0){
        lcd_shift_msg(pgm_name[pgm_menu], 2); // scrolling text on line 2
     }
     else{
        M5.Lcd.printf("in OSPy!"); 
     }
  }
  if (text == 3) M5.Lcd.printf("Please wait."); 
  if (text == 4) M5.Lcd.printf("Please wait."); 
  if (text == 5) M5.Lcd.printf("Please wait."); 
  if (text == 6) {M5.Lcd.printf("PGM: "); M5.Lcd.print(pgm_menu+1);}
  if (text == 7) {
    M5.Lcd.printf("Any error!");
    //reboot();
  }
  if (text == 8){
    if(pgm_count>0){
       lcd_shift_msg(pgm_name[pgm_menu], 2);          // scrolling text on line 2
    }   
  }
  if (text == 9) M5.Lcd.printf("Any error.");
  if (text == 10) M5.Lcd.printf("manager.");
  if (text == 11) M5.Lcd.printf("not JSON!");
}

void lcd_qr(String msg){
  M5.Lcd.qrcode(msg,2,2,78,2);
  //qrcode(const char *string, uint16_t x, uint16_t y, uint8_t width, uint8_t version);
  /*
  val   string / String&  String to embed in QR
  x   uint16_t  Coordinate X(left corner)
  y   uint16_t  Coordinate Y(left corner)
  width   uint8_t   width (px)
  version   uint8_t   QR code version
  */
}//end void

String getEEPROMString(int start, int len) {
  String string = "";
  for (int i = start; i < + start + len; ++i) {
    uint8_t b = EEPROM.read(i);
    if ((0xff == b) || (0 == b)) break;
    string += char(b);
  }//end for
  return string;
}//end string

void setEEPROMString(int start, int len, String string) {
  int si = 0;
  for (int i = start; i < start + len; ++i) {
    char c;
    if (si < string.length()) {
      c = string[si];
    }//end if
    else {
      c = 0;
    }//end else
    EEPROM.write(i, c);
    ++si;
  }//end for
}//end void

void get_EEPROM() {
  String  tmp;
  DEBUG_PRINTLN(F("GET-EEPROM"));
  DEBUG_FLUSH();
  tmp = getEEPROMString(offsetof(eepromdata_t, WIFI_SSID), elementSize(eepromdata_t, WIFI_SSID));      // read as string
  strncpy(WIFI_SSID, tmp.c_str(), sizeof(WIFI_SSID));                                                  // copy to char
  WIFI_SSID[sizeof(WIFI_SSID) - 1] = 0;
  DEBUG_PRINT(F("EE-WIFI-SSID:"));
  DEBUG_PRINTLN(WIFI_SSID);
  DEBUG_FLUSH();
  if(String(WIFI_SSID) == "") default_EEPROM(); 
  
  tmp = getEEPROMString(offsetof(eepromdata_t, WIFI_PASS), elementSize(eepromdata_t, WIFI_PASS));      // read as string
  strncpy(WIFI_PASS, tmp.c_str(), sizeof(WIFI_PASS));                                                  // copy to char
  WIFI_PASS[sizeof(WIFI_PASS) - 1] = 0;
  DEBUG_PRINT(F("EE-WIFI-PASS:"));
  DEBUG_PRINTLN(WIFI_PASS);
  DEBUG_FLUSH();
  if(String(WIFI_PASS) == "") default_EEPROM(); 

  tmp = getEEPROMString(offsetof(eepromdata_t, AUTH_NAME), elementSize(eepromdata_t, AUTH_NAME));      // read as string
  strncpy(AUTH_NAME, tmp.c_str(), sizeof(AUTH_NAME));                                                  // copy to char
  AUTH_NAME[sizeof(AUTH_NAME) - 1] = 0;
  DEBUG_PRINT(F("EE-AUTH-NAME:"));
  DEBUG_PRINTLN(AUTH_NAME);
  DEBUG_FLUSH();
  if(String(AUTH_NAME) == "") default_EEPROM();

  tmp = getEEPROMString(offsetof(eepromdata_t, AUTH_PASS), elementSize(eepromdata_t, AUTH_PASS));      // read as string
  strncpy(AUTH_PASS, tmp.c_str(), sizeof(AUTH_PASS));                                                  // copy to char
  AUTH_PASS[sizeof(AUTH_PASS) - 1] = 0;
  DEBUG_PRINT(F("EE-AUTH-PASS:"));
  DEBUG_PRINTLN(AUTH_PASS);
  DEBUG_FLUSH();
  if(String(AUTH_PASS) == "") default_EEPROM(); 

  tmp = getEEPROMString(offsetof(eepromdata_t, NTP_SERVER), elementSize(eepromdata_t, NTP_SERVER));    // read as string
  strncpy(NTP_SERVER, tmp.c_str(), sizeof(NTP_SERVER));                                                // copy to char
  NTP_SERVER[sizeof(NTP_SERVER) - 1] = 0;
  DEBUG_PRINT(F("EE-NTP-SERVER:"));
  DEBUG_PRINTLN(NTP_SERVER); 
  DEBUG_FLUSH();
  if(String(NTP_SERVER) == "") default_EEPROM();

  DAY_OFFSET = atoi(getEEPROMString(offsetof(eepromdata_t, DAY_OFFSET), elementSize(eepromdata_t, DAY_OFFSET)).c_str());
  DEBUG_PRINT(F("EE-DAY-OFFSET:"));
  DEBUG_PRINTLN(DAY_OFFSET);
  DEBUG_FLUSH();

  GMT_OFFSET = atoi(getEEPROMString(offsetof(eepromdata_t, GMT_OFFSET), elementSize(eepromdata_t, GMT_OFFSET)).c_str());
  DEBUG_PRINT(F("EE-GMT-OFFSET:"));
  DEBUG_PRINTLN(GMT_OFFSET);
  DEBUG_FLUSH();

  tmp = getEEPROMString(offsetof(eepromdata_t, OSPY_ADDR), elementSize(eepromdata_t, OSPY_ADDR));      // read as string
  strncpy(OSPY_ADDR, tmp.c_str(), sizeof(OSPY_ADDR));                                                  // copy to char
  OSPY_ADDR[sizeof(OSPY_ADDR) - 1] = 0;
  DEBUG_PRINT(F("EE-OSPY-ADDR:"));
  DEBUG_PRINTLN(OSPY_ADDR);
  DEBUG_FLUSH();
  if(String(OSPY_ADDR) == "") default_EEPROM();

  tmp = getEEPROMString(offsetof(eepromdata_t, UPLOAD_PASS), elementSize(eepromdata_t, UPLOAD_PASS));  // read as string
  strncpy(UPLOAD_PASS, tmp.c_str(), sizeof(UPLOAD_PASS));                                              // copy to char
  UPLOAD_PASS[sizeof(UPLOAD_PASS) - 1] = 0;
  DEBUG_PRINT(F("EE-UPLOAD-PASS:"));
  DEBUG_PRINTLN(UPLOAD_PASS);
  DEBUG_FLUSH();
  if(String(UPLOAD_PASS) == "") default_EEPROM();

  tmp = getEEPROMString(offsetof(eepromdata_t, AP_WIFI_PASS), elementSize(eepromdata_t, AP_WIFI_PASS));// read as string
  strncpy(AP_WIFI_PASS, tmp.c_str(), sizeof(AP_WIFI_PASS));                                            // copy to char
  AP_WIFI_PASS[sizeof(AP_WIFI_PASS) - 1] = 0;
  DEBUG_PRINT(F("EE-AP-WIFI-PASS:"));
  DEBUG_PRINTLN(AP_WIFI_PASS);
  DEBUG_FLUSH();
  if(String(AP_WIFI_PASS) == "") default_EEPROM();    
             
  int mgc = atoi(getEEPROMString(offsetof(eepromdata_t, MAGICNR), elementSize(eepromdata_t, MAGICNR)).c_str());
  DEBUG_PRINT(F("EE-MAGICNR:"));
  DEBUG_PRINTLN(mgc);
  DEBUG_FLUSH();
  if(mgc != 666) {
     default_EEPROM();
  }
  DEBUG_PRINTLN(F("OK"));
  DEBUG_FLUSH();
}//end void  

void default_EEPROM() {
  DEBUG_PRINT(F("DEFAULT-EEPROM:"));
  DEBUG_FLUSH();
  setEEPROMString(offsetof(eepromdata_t,  WIFI_SSID), elementSize(eepromdata_t, WIFI_SSID),   "none");
  setEEPROMString(offsetof(eepromdata_t,  WIFI_PASS), elementSize(eepromdata_t, WIFI_PASS),   "none");
  setEEPROMString(offsetof(eepromdata_t,  AUTH_NAME), elementSize(eepromdata_t, AUTH_NAME),   "admin");
  setEEPROMString(offsetof(eepromdata_t,  AUTH_PASS), elementSize(eepromdata_t, AUTH_PASS),   "opendoor");
  setEEPROMString(offsetof(eepromdata_t,  NTP_SERVER), elementSize(eepromdata_t, NTP_SERVER), "europe.pool.ntp.org");
  setEEPROMString(offsetof(eepromdata_t,  DAY_OFFSET), elementSize(eepromdata_t, DAY_OFFSET), "3600");
  setEEPROMString(offsetof(eepromdata_t,  GMT_OFFSET), elementSize(eepromdata_t, GMT_OFFSET), "3600");
  setEEPROMString(offsetof(eepromdata_t,  OSPY_ADDR), elementSize(eepromdata_t, OSPY_ADDR),   "https://192.168.88.247:8080/api/");
  setEEPROMString(offsetof(eepromdata_t,  UPLOAD_PASS), elementSize(eepromdata_t, UPLOAD_PASS),   "fg4s5b.s,trr7sw8sgyvrDfg");
  setEEPROMString(offsetof(eepromdata_t,  AP_WIFI_PASS), elementSize(eepromdata_t, AP_WIFI_PASS), "ospy-m5stick-c");   
  setEEPROMString(offsetof(eepromdata_t,  MAGICNR), elementSize(eepromdata_t,  MAGICNR),  "666");    
  EEPROM.commit();         
  DEBUG_PRINTLN(F("OK"));
  DEBUG_FLUSH();
  reboot();
}//end void 

String get_ntp_time(){ 
  struct tm timeinfo;
  if(!getLocalTime(&timeinfo)){
    DEBUG_PRINTLN(F("ERR-NTP"));
    DEBUG_FLUSH();
    is_ntp_ok = false;
    return "Reading...";
  }
  else{
    //Serial.println(&timeinfo, "%A, %B %d %Y %H:%M:%S");
    char buftime[80];
    //strftime (buftime, 80, "%H:%M:%S", &timeinfo);
    strftime (buftime, 80, "%d.%m.%Y %H:%M:%S", &timeinfo);
    #ifdef PRINT_TIME
       DEBUG_PRINTLN(buftime);
       DEBUG_FLUSH();
    #endif   
    is_ntp_ok = true;
    return String(buftime);
  }  
}// end void

//AP page
// green color #397F19, blue color #2E3959, https://base64.guru/converter/encode/image
static const char html_ap_header[] PROGMEM = R"=====(<!DOCTYPE html><html lang='en'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1, user-scalable=no'/><title>{v}</title>)=====";
static const char html_ap_style[] PROGMEM = R"=====(<style>div.header {border:3px;border-radius: 12px; min-width:260px; background-image: url(data:image/png;base64,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); background-repeat: no-repeat; background-position: 42px 20px; background-color: #32A620;height: 80px;}.sensor-container {border:3px solid #2E3959;border-radius: 12px;text-align:left;display:inline-block;min-width:260px;}.c{text-align: center;} div,input{padding:5px;font-size:1em;} input{width:95%;} body{text-align: center;font-family:verdana;} button{border:0;border-radius:0.3rem;background-color:#397F19;color:#fff;line-height:2.4rem;font-size:1.2rem;width:100%;} .q{float: right;width: 64px;text-align: right;} .l{background: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAMAAABEpIrGAAAALVBMVEX///8EBwfBwsLw8PAzNjaCg4NTVVUjJiZDRUUUFxdiZGSho6OSk5Pg4eFydHTCjaf3AAAAZElEQVQ4je2NSw7AIAhEBamKn97/uMXEGBvozkWb9C2Zx4xzWykBhFAeYp9gkLyZE0zIMno9n4g19hmdY39scwqVkOXaxph0ZCXQcqxSpgQpONa59wkRDOL93eAXvimwlbPbwwVAegLS1HGfZAAAAABJRU5ErkJggg==) no-repeat left center;background-size: 1em;}</style>)=====";
static const char html_ap_script[] PROGMEM = R"=====(<script>function c(l){document.getElementById('s').value=l.innerText||l.textContent;document.getElementById('p').focus();}</script>)=====";
static const char html_ap_header_end[] PROGMEM = R"=====(</head><body><div id='sensor-container' class='sensor-container'><div id='header' class='header'></div>)=====";
static const char html_ap_portal_options[] PROGMEM = R"=====(<form action='/wifi' method='get'><button>Wi-Fi Settings</button></form><br/><form action='/i' method='get'><button>Controller Info</button></form><br/><form action='/c' method='post'><button>Controller Settings</button></form><br/><form action="/T" method="get"><button>Firmware Updating</button></form></br><form action='/r' method='post'><button>Restart</button></form><br/><form action='/EDF' method='post'><button>Default</button></form><br/><form action='/{m}' method='post'></form>)=====";
static const char html_ap_item[] PROGMEM = R"=====(<a href='#p' onclick='c(this)'>{v}</a>&nbsp;<span class='q {i}'>{r}%</span></br>)=====";
static const char html_ap_form_start[] PROGMEM = R"=====(</br><form method='get' action='/wifisave'><input id='s' name='s' length=32 placeholder='SSID'><br/><input id='p' name='p' length=64 type='password' placeholder='password'><br/>)=====";
static const char html_ap_form_end[] PROGMEM = R"=====(<br/><button type='submit'>Save</button></form></br><form action='/' method='get'><button>Back</button></form>)=====";
static const char html_ap_scan_link[] PROGMEM = R"=====(<br/><form action='/wifi' method='get'><button>Search again</button></form></br>)=====";
static const char html_ap_saved[] PROGMEM = R"=====(</br><b>Settings saved!</br>It is necessary to restart the OSPy Controller</b></br><form action='/' method='get'><button>Back</button></form></div>)=====";
static const char html_ap_end[] PROGMEM = R"=====(</div><p>{timeout}</p><p>© www.pihrt.com ESP32 Controller for OpenSprinkler.</p></body></html>)=====";
static const char html_ap_upload[] PROGMEM = R"=====(<form method='POST' action='/U' id='fm' enctype='multipart/form-data'><h1>Controller firmware updating</h1><p><input type='file' name='file' accept='.bin' id='file'></p><p><label id='msg_upload'></label></p><p><label id='msg'></label></p><button id='submit'>Update</button></p></form>)=====";

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
  DEBUG_PRINTLN(res);
  return res;
}//end string

String print_in_html_timeout(){ // print temout on pages    
  String timcontent = FPSTR(F("Time to reboot "));
  if(numberOfMinutes(APtimeLCD/1000)<10) timcontent += FPSTR(F("0"));
  timcontent += String(numberOfMinutes(APtimeLCD/1000));
  timcontent += FPSTR(F(":"));
  if(numberOfSeconds(APtimeLCD/1000)<10) timcontent += FPSTR(F("0"));
  timcontent += String(numberOfSeconds(APtimeLCD/1000));
  return timcontent;
} 

boolean captivePortal(){ // Redirect to captive portal if we got a request for another domain. Return true in that case so the page handler do not try to handle the request again.
  if(!isIp(server.hostHeader())){
    DEBUG_PRINTLN(F("AP:Request-redirected-to-captive-portal"));   
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
  DEBUG_PRINT(F("SERVER:"));
  DEBUG_PRINTLN(message);
  server.sendHeader("Cache-Control", "no-cache, no-store, must-revalidate");
  server.sendHeader("Pragma", "no-cache");
  server.sendHeader("Expires", "-1");
  server.sendHeader("Content-Length", String(message.length()));
  server.send(404, "text/plain", message);
}// end void

void WIFIAP_setup(){
     APtime = millis();  
     WiFi.mode(WIFI_OFF);                        
     delay(1000);
     WiFi.mode(WIFI_AP_STA);    
     String s = "OSPy-Controller-M5stick";    
     const char *Hostname_complete = s.c_str(); 
     WiFi.softAP(Hostname_complete, AP_WIFI_PASS); 
     delay(100);
     DEBUG_PRINTLN(F("AP-MANAGER")); 
     IPAddress Ip(192, 168, 1, 1);                  
     IPAddress NMask(255, 255, 255, 0);          
     WiFi.softAPConfig(Ip, Ip, NMask);  
     IPAddress myAPIP = WiFi.softAPIP();         
     DEBUG_PRINT(F("AP-SSID:"));
     DEBUG_PRINTLN(Hostname_complete);
     DEBUG_PRINT(F("AP-IP: "));
     DEBUG_PRINTLN(myAPIP);
         
     // Not Found
     server.onNotFound(handleNotFound);
     
     // Home page
     server.on("/", []() {           
     String content = "";
     content += FPSTR(html_ap_header);
     content.replace("{v}", "OSPy Controller");
     content += FPSTR(html_ap_style);
     content += FPSTR(html_ap_header_end);
     content += String(F("<h1>OSPy Controller"));
     content += String(F("</h1>"));
     content += String(F("<h3>Main menu</h3>"));
     content += FPSTR(html_ap_portal_options);
     content += FPSTR(html_ap_end);
     content.replace("{timeout}", print_in_html_timeout());
     server.sendHeader("Content-Length", String(content.length()));
     server.send(200, "text/html", content);
     });    

     // Wi-Fi page
     server.on("/wifi", []() { 
     String content = FPSTR(html_ap_header);
     content.replace("{v}", "OSPy Controller");
     content += FPSTR(html_ap_script);
     content += FPSTR(html_ap_style);
     content += FPSTR(html_ap_header_end);
     content += String(F("<h3>Wi-Fi connection</h3>"));
     content += String(F("<h4>Click to select the Wi-Fi network to which you want to connect the controller.</h4>"));

     if(scan) {
        int n = WiFi.scanNetworks();
        DEBUG_PRINTLN(F("AP:Network-scan-OK"));  
     if(n==0){
        DEBUG_PRINTLN(F("AP:No-network-found"));
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
                DEBUG_PRINT(F("AP:Duplicit-network:"));
                DEBUG_PRINTLN(WiFi.SSID(indices[j])); 
                indices[j] = -1; 
              }//end if
            }//end for2
          }//end for1
        }//end removeDuplicates

        // display networks on the page
        for(int i = 0; i < n; i++){
          if(indices[i] == -1) continue; // skip duplicate networks
          DEBUG_PRINT(WiFi.SSID(indices[i]));
          DEBUG_PRINTLN(WiFi.RSSI(indices[i])); 
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
    if(server.hasArg("s")){
      DEBUG_PRINT(F("AP:SAVE-SSID:")); DEBUG_PRINTLN(server.arg("s").c_str());
      setEEPROMString(offsetof(eepromdata_t, WIFI_SSID), elementSize(eepromdata_t, WIFI_SSID), server.arg("s"));
    }        

    if(server.hasArg("p")){
      DEBUG_PRINT(F("AP:SAVE-PASS:")); DEBUG_PRINTLN(server.arg("p").c_str());
      setEEPROMString(offsetof(eepromdata_t, WIFI_PASS), elementSize(eepromdata_t, WIFI_PASS), server.arg("p"));
    }      
    EEPROM.commit();
    delay(500);
    
    String content = FPSTR(html_ap_header);
    content.replace("{v}", "OSPy Controller");
    content += FPSTR(html_ap_script);
    content += FPSTR(html_ap_style);
    content += FPSTR(html_ap_header_end);
    content += FPSTR(html_ap_saved);
    content += FPSTR(html_ap_end);
    content.replace("{timeout}", print_in_html_timeout());
    server.send(200, "text/html", content);
    });  

    // Information about controller
    server.on("/i", []() {  
    String content = FPSTR(html_ap_header);
    content.replace("{v}", "OSPy Controller Information");
    content += FPSTR(html_ap_script);
    content += FPSTR(html_ap_style);
    content += FPSTR(html_ap_header_end);
    content += String(F("<h4>OSPy Controller Information</h4>"));
    content += F("<dl>");     
    content += F("<dt><b>Wi-Fi SSID</b></dt><dd>");
    content += String(WIFI_SSID);
    content += F("</dd>");
    content += F("<dt><b>Controller AP MAC</b></dt><dd>");
    content += WiFi.softAPmacAddress();
    content += F("</dd>");
    content += F("<dt><b>Controller STA MAC</b></dt><dd>");
    content += WiFi.macAddress();
    content += F("</dd>");   
    content += F("<dt><b>Wi-Fi AP password</b></dt><dd>");
    content += String(AP_WIFI_PASS);
    content += F("</dd>");
    content += F("<dt><b>FW upload password</b></dt><dd>");
    content += String(UPLOAD_PASS);
    content += F("</dd>");             
    content += F("<dt><b>OSPy address</b></dt><dd>");
    content += String(OSPY_ADDR); 
    content += F("</dd>");
    content += F("<dt><b>OSPy Authorization name</b></dt><dd>");
    content += String(AUTH_NAME);
    content += F("</dd>"); 
    content += F("<dt><b>OSPy Authorization password</b></dt><dd>");
    content += String(AUTH_PASS);
    content += F("</dd>"); 
    content += F("<dt><b>NTP time server</b></dt><dd>");
    content += String(NTP_SERVER);
    content += F("</dd>");   
    content += F("<dt><b>NTP GMT Offset</b></dt><dd>");
    content += String(GMT_OFFSET);
    content += F("</dd>"); 
    content += F("<dt><b>NTP Day Offset</b></dt><dd>");
    content += String(DAY_OFFSET);
    content += F("</dd>");             
    content += F("</dl>");                     
    content += F("</br><form action=\"/\" method=\"get\"><button>Back</button></form>");
    content += FPSTR(html_ap_end);
    content.replace("{timeout}", print_in_html_timeout());
    server.sendHeader("Content-Length", String(content.length()));
    server.send(200, "text/html", content);
    });   

    // Controller settings
    server.on("/c", []() {        
    String content = FPSTR(html_ap_header);
    content.replace("{v}", "OSPy Controller Settings");
    content += FPSTR(html_ap_script);
    content += FPSTR(html_ap_style);
    content += FPSTR(html_ap_header_end);
    content += F("<h4>OSPy Controller Settings</h4>");
    content += F("</br><form method='get' action='/sensorsave'>");
    content += F("<dl>");   
    content += F("<dt><b>Wi-Fi AP password</b></dt><dd>");
    content += F("<input id='a' name='a' length=16 maxlength='32' value='"); 
    content += String(AP_WIFI_PASS);  
    content += F("'></dd>"); 
    content += F("<dt><b>FW upload password</b></dt><dd>");
    content += F("<input id='b' name='b' length=16 maxlength='32' value='"); 
    content += String(UPLOAD_PASS);  
    content += F("'></dd>");            
    content += F("<dt><b>OSPy address</b></dt><dd>");
    content += F("<input id='c' name='c' length=16 maxlength='40' value='"); 
    content += String(OSPY_ADDR);  
    content += F("'></dd>");
    content += F("<dt><b>OSPy Authorization name</b></dt><dd>"); 
    content += F("<input id='d' name='d' length=16 maxlength='32' value='"); 
    content += String(AUTH_NAME);  
    content += F("'></dd>");
    content += F("<dt><b>OSPy Authorization password</b></dt><dd>"); 
    content += F("<input id='e' name='e' length=16 maxlength='32' value='"); 
    content += String(AUTH_PASS);  
    content += F("'></dd>");    
    content += F("<dt><b>NTP time server</b></dt><dd>"); 
    content += F("<input id='f' name='f' length=16 maxlength='32' value='"); 
    content += String(NTP_SERVER);  
    content += F("'></dd>"); 
    content += F("<dt><b>NTP GMT Offset</b></dt><dd>"); 
    content += F("<input type='number' id='g' name='g' length=9 maxlength='9' value='"); 
    content += String(GMT_OFFSET);  
    content += F("'></dd>");
    content += F("<dt><b>NTP Day Offset</b></dt><dd>"); 
    content += F("<input type='number' id='h' name='h' length=9 maxlength='9' value='"); 
    content += String(DAY_OFFSET);  
    content += F("'></dd>");    
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
    DEBUG_PRINTLN(F("AP:SAVING"));        
    if(server.hasArg("a")){
      setEEPROMString(offsetof(eepromdata_t, AP_WIFI_PASS), elementSize(eepromdata_t, AP_WIFI_PASS), server.arg("a"));
      DEBUG_PRINT(F("AP:AP-WIFI-PASS:")); DEBUG_PRINTLN(server.arg("a").c_str());
    }

    if(server.hasArg("b")){
      setEEPROMString(offsetof(eepromdata_t, UPLOAD_PASS), elementSize(eepromdata_t, UPLOAD_PASS), server.arg("b"));
      DEBUG_PRINT(F("AP:UPLOAD_PASS:")); DEBUG_PRINTLN(server.arg("b").c_str());
    } 
  
    if(server.hasArg("c")){
      setEEPROMString(offsetof(eepromdata_t, OSPY_ADDR), elementSize(eepromdata_t, OSPY_ADDR), server.arg("c"));
      DEBUG_PRINT(F("AP:OSPY_ADDR:")); DEBUG_PRINTLN(server.arg("c").c_str());
    }   
      
    if(server.hasArg("d")){
      setEEPROMString(offsetof(eepromdata_t, AUTH_NAME), elementSize(eepromdata_t, AUTH_NAME), server.arg("d"));
      DEBUG_PRINT(F("AP:AUTH_NAME:")); DEBUG_PRINTLN(server.arg("d").c_str());
    } 
       
    if(server.hasArg("e")){
      setEEPROMString(offsetof(eepromdata_t, AUTH_PASS), elementSize(eepromdata_t, AUTH_PASS), server.arg("e"));
      DEBUG_PRINT(F("AP:AUTH_NAME:")); DEBUG_PRINTLN(server.arg("e").c_str());
    }  

    if(server.hasArg("f")){
      setEEPROMString(offsetof(eepromdata_t, NTP_SERVER), elementSize(eepromdata_t, NTP_SERVER), server.arg("f"));
      DEBUG_PRINT(F("AP:NTP_SERVER:")); DEBUG_PRINTLN(server.arg("f").c_str());
    }     

    if(server.hasArg("g")){
      setEEPROMString(offsetof(eepromdata_t, GMT_OFFSET), elementSize(eepromdata_t, GMT_OFFSET), server.arg("g"));
      DEBUG_PRINT(F("AP:GMT_OFFSET:")); DEBUG_PRINTLN(server.arg("g").c_str());
    } 

    if(server.hasArg("h")){
      setEEPROMString(offsetof(eepromdata_t, DAY_OFFSET), elementSize(eepromdata_t, DAY_OFFSET), server.arg("h"));
      DEBUG_PRINT(F("AP:DAY_OFFSET:")); DEBUG_PRINTLN(server.arg("h").c_str());
    }         
 
    EEPROM.commit();
    get_EEPROM(); 
    
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
    content.replace("{v}", "OSPy Controller Restart");
    content += FPSTR(html_ap_style);
    content += FPSTR(html_ap_header_end);
    content += F("<h4>The OSPy Controller restarts in 5 seconds.</h4></br>");
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
    content.replace("{v}", "OSPy Controller");
    content += FPSTR(html_ap_style);
    content += FPSTR(html_ap_header_end);
    content += F("<h4>Set the default Controller data?</h4></br>");
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
    default_EEPROM();
    content += F("</br><form action=\"/r\" method=\"get\"><button>Yes restart</button></form>");
    content += F("</br><form action=\"/\" method=\"get\"><button>No back</button></form>");
    content += FPSTR(html_ap_end);
    content.replace("{timeout}", print_in_html_timeout());
    server.sendHeader("Content-Length", String(content.length()));
    server.send(200, "text/html", content);
    });    
   
    server.on("/U", HTTP_POST,[](){   
      String content = "";
      content = F("OK, Restarting...");
      server.send(200, "text/html", content);
      delay(1000);
      reboot();     
    },[](){
      HTTPUpload& upload = server.upload();
      if(upload.status == UPLOAD_FILE_START){
         DEBUG_PRINTLN(F("UPLOAD-FILENAME:"));
         DEBUG_PRINTLN(upload.filename.c_str());
         unsigned long maxSketchSpace = (ESP.getFreeSketchSpace()-0x1000)& 0xFFFFF000;
         if(!Update.begin(maxSketchSpace)){ 
            DEBUG_PRINTLN(F("ERR:MAX-SKETCH-SPACE"));
         }// end if     
      }// end if
      else if(upload.status == UPLOAD_FILE_WRITE){ 
         if(Update.write(upload.buf, upload.currentSize) != upload.currentSize){
           #ifdef DEBUG
              Update.printError(Serial);
              DEBUG_FLUSH();
           #endif   
         }// end if
      }// end else if
      else if(upload.status == UPLOAD_FILE_END){
         if(Update.end(true)){
            DEBUG_PRINT(F("FILE-SIZE:"));
            DEBUG_PRINTLN(upload.totalSize);
         }// end if
         else{
            #ifdef DEBUG
               Update.printError(Serial);
               DEBUG_FLUSH();
            #endif
         }//end else
      }// end else if
      });// end server.on    
    
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
      
    server.begin();                         // starting http server
}//end WIFIAP_setup
  
