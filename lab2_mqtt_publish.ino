/*
 * EE 288 Laboratory Report 1, Lab Session 2
 * ESP32 MQTT Publisher (DHT11 temperature and humidity)
 *
 * Publishes temperature and humidity to a local Mosquitto broker on the
 * topics esp32/sensors/temperature and esp32/sensors/humidity.
 *
 * Before uploading, set:
 *   ssid / password : your Wi-Fi network
 *   mqtt_server     : the IP address of the PC running Mosquitto
 *
 * Libraries (Arduino Library Manager): PubSubClient, DHT sensor library,
 * Adafruit Unified Sensor.  Board: ESP32 Dev Module.
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include "DHT.h"

#define DHTPIN 4
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

// Wi-Fi Credentials
const char* ssid = "Gelo";
const char* password = "cazoo717";

// MQTT Broker IP
const char* mqtt_server = "10.117.56.12"; 

WiFiClient espClient;
PubSubClient client(espClient);

void setup_wifi() {
  delay(100);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500); Serial.print(".");
  }
  Serial.println("WiFi connected");
}

void setup() {
  Serial.begin(115200);
  dht.begin();
  setup_wifi();
  client.setServer(mqtt_server, 1883);
}

void loop() {
  if (!client.connected()) {
    while (!client.connected()) {
      String clientId = "ESP32Client-";
      clientId += String(random(0xffff), HEX);
      if (client.connect(clientId.c_str())) {
        Serial.println("Connected to MQTT");
      } else {
        delay(2000);
      }
    }
  }

  float temp = dht.readTemperature();
  float hum = dht.readHumidity();

  char tempStr[8], humStr[8];
  dtostrf(temp, 1, 2, tempStr);
  dtostrf(hum, 1, 2, humStr);

  client.publish("esp32/sensors/temperature", tempStr);
  client.publish("esp32/sensors/humidity", humStr);

  Serial.println("Published to MQTT");
  delay(5000);
}
