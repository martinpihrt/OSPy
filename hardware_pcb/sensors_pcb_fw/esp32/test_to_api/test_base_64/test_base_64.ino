#include "WiFi.h"
#include "HTTPClient.h"
#include "base64.h"

 
const char* ssid = "...";
const char* password = "...";
 
String authUsername = "admin";
String authPassword = "opendoor";

const char* serverName = "http://your_ip:8080/api/sensor";
 
void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi..");
  }
   Serial.println("Connected to WiFi");
}
 
void loop() {
   if ((WiFi.status() == WL_CONNECTED)) { 
     Serial.print("Connected to WiFi network with IP Address: ");
     Serial.println(WiFi.localIP());
     HTTPClient http;
     http.begin(serverName);
     String auth = base64::encode(authUsername + ":" + authPassword);
     //Serial.println(authUsername);
     //Serial.println(authPassword);
     //Serial.println(auth);
     http.addHeader("Authorization", "Basic " + auth);
    String httpRequestData = "do={\"ip\":\"192.168.88.210\",\"mac\":\"aa:bb:cc:dd:ee:ff\",\"rssi\":\"100\",\"batt\":\"123\",\"stype\":\"5\",\"temp\":\"252\",\"secret\":\"5de5fbb767c2f802\"}";
    
    //http.addHeader("Content-Type", "application/json");          
    int httpResponseCode = http.POST(httpRequestData);

    Serial.print("HTTP Response code: ");
    Serial.println(httpResponseCode);

    http.end();
  }
  delay(20000);
 }