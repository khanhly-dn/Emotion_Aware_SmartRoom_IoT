/*
  esp32_emotion_led.ino
  ========================
  Emotion-Aware Smart Room — ESP32 Firmware
  
  - Kết nối WiFi
  - Subscribe MQTT topic: smartroom/emotion
  - Bật LED đúng GPIO theo cảm xúc nhận được
  - Blink pattern khác nhau cho từng cảm xúc
  
  Thư viện cần cài (Arduino IDE → Library Manager):
    - PubSubClient by Nick O'Leary  (v2.8)
    - ArduinoJson by Benoit Blanchon (v7.x)
  
  Board: ESP32 Dev Module
  
  ════════════════════════════════════════════
  SƠ ĐỒ ĐẤU DÂY:
  
  ESP32 GPIO2  → Điện trở 220Ω → LED(+) → LED(-) → GND
  ESP32 GPIO4  → Điện trở 220Ω → LED(+) → LED(-) → GND
  ESP32 GPIO5  → Điện trở 220Ω → LED(+) → LED(-) → GND
  ESP32 GPIO18 → Điện trở 220Ω → LED(+) → LED(-) → GND
  ESP32 GPIO19 → Điện trở 220Ω → LED(+) → LED(-) → GND
  ESP32 GPIO21 → Điện trở 220Ω → LED(+) → LED(-) → GND
  ESP32 GPIO22 → Điện trở 220Ω → LED(+) → LED(-) → GND
  
  Nếu chỉ có 1 LED: cắm vào GPIO2 là đủ để test.
  ════════════════════════════════════════════
*/

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// ─────────────────────────────────────────────
// CONFIG — chỉnh tại đây
// ─────────────────────────────────────────────
const char* WIFI_SSID     = "Khanh";
const char* WIFI_PASSWORD = "@133057k";

const char* MQTT_BROKER   = "broker.hivemq.com";
const int   MQTT_PORT     = 1883;
const char* MQTT_TOPIC    = "smartroom/emotion";
const char* MQTT_CLIENT_ID = "esp32-smartroom-001";
// ─────────────────────────────────────────────

// GPIO cho từng cảm xúc (phải khớp với Python)
const int PIN_HAPPY    = 2;
const int PIN_SAD      = 4;
const int PIN_ANGRY    = 5;
const int PIN_FEAR     = 18;
const int PIN_SURPRISE = 19;
const int PIN_NEUTRAL  = 21;
const int PIN_DISGUST  = 22;

const int ALL_PINS[]   = {2, 4, 5, 18, 19, 21, 22};
const int PIN_COUNT    = 7;

// Blink pattern: {số lần, thời gian ON (ms), thời gian OFF (ms)}
struct BlinkPattern {
  int times;
  int on_ms;
  int off_ms;
};

BlinkPattern PATTERNS[] = {
  {3, 200, 100},   // happy    — 3 lần, nhanh
  {1, 800, 0},     // sad      — 1 lần, chậm dài
  {5, 80,  80},    // angry    — 5 lần, rất nhanh
  {2, 300, 200},   // fear     — 2 lần, run run
  {4, 100, 100},   // surprise — 4 lần, nhanh
  {1, 500, 0},     // neutral  — 1 lần, trung bình
  {2, 150, 300},   // disgust  — 2 lần, chậm
};

String EMOTION_NAMES[] = {
  "happy", "sad", "angry", "fear", "surprise", "neutral", "disgust"
};

WiFiClient   wifiClient;
PubSubClient mqttClient(wifiClient);

String currentEmotion = "neutral";
int    activePin      = PIN_NEUTRAL;
bool   newEmotion     = false;
int    patternIndex   = 5; // neutral mặc định


// ══════════════════════════════════════════════
// WIFI
// ══════════════════════════════════════════════
void connectWiFi() {
  Serial.print("[WiFi] Connecting to ");
  Serial.println(WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[WiFi] Connected!");
    Serial.print("[WiFi] IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n[WiFi] Failed! Restarting…");
    ESP.restart();
  }
}


// ══════════════════════════════════════════════
// MQTT CALLBACK — nhận message
// ══════════════════════════════════════════════
void onMqttMessage(char* topic, byte* payload, unsigned int length) {
  // Parse JSON
  StaticJsonDocument<256> doc;
  DeserializationError err = deserializeJson(doc, payload, length);

  if (err) {
    Serial.print("[MQTT] JSON parse error: ");
    Serial.println(err.c_str());
    return;
  }

  const char* emotion = doc["emotion"];
  float confidence    = doc["confidence"];
  int gpio            = doc["gpio"];

  Serial.printf("[MQTT] Received → emotion: %s | confidence: %.1f%% | gpio: %d\n",
                emotion, confidence, gpio);

  currentEmotion = String(emotion);
  activePin      = gpio;
  newEmotion     = true;

  // Tìm pattern index
  patternIndex = 5; // default neutral
  for (int i = 0; i < 7; i++) {
    if (EMOTION_NAMES[i] == currentEmotion) {
      patternIndex = i;
      break;
    }
  }
}


// ══════════════════════════════════════════════
// MQTT CONNECT
// ══════════════════════════════════════════════
void connectMQTT() {
  while (!mqttClient.connected()) {
    Serial.print("[MQTT] Connecting to ");
    Serial.print(MQTT_BROKER);
    Serial.print("…");

    if (mqttClient.connect(MQTT_CLIENT_ID)) {
      Serial.println(" Connected!");
      mqttClient.subscribe(MQTT_TOPIC);
      Serial.printf("[MQTT] Subscribed to: %s\n", MQTT_TOPIC);
    } else {
      Serial.printf(" Failed (state=%d), retry in 3s\n", mqttClient.state());
      delay(3000);
    }
  }
}


// ══════════════════════════════════════════════
// LED HELPERS
// ══════════════════════════════════════════════
void allLedsOff() {
  for (int i = 0; i < PIN_COUNT; i++) {
    digitalWrite(ALL_PINS[i], LOW);
  }
}

void blinkLed(int pin, BlinkPattern& p) {
  allLedsOff();
  for (int i = 0; i < p.times; i++) {
    digitalWrite(pin, HIGH);
    delay(p.on_ms);
    digitalWrite(pin, LOW);
    if (i < p.times - 1) delay(p.off_ms);
  }
  // Sau khi blink xong: giữ sáng LED
  digitalWrite(pin, HIGH);
}


// ══════════════════════════════════════════════
// SETUP
// ══════════════════════════════════════════════
void setup() {
  Serial.begin(115200);
  Serial.println("\n[BOOT] Emotion-Aware Smart Room — ESP32");

  // Setup tất cả LED pins
  for (int i = 0; i < PIN_COUNT; i++) {
    pinMode(ALL_PINS[i], OUTPUT);
    digitalWrite(ALL_PINS[i], LOW);
  }

  // Boot animation: bật lần lượt tất cả LED
  Serial.println("[BOOT] LED test…");
  for (int i = 0; i < PIN_COUNT; i++) {
    digitalWrite(ALL_PINS[i], HIGH);
    delay(100);
  }
  delay(300);
  allLedsOff();

  connectWiFi();

  mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
  mqttClient.setCallback(onMqttMessage);
  mqttClient.setKeepAlive(60);

  connectMQTT();

  Serial.println("[BOOT] Ready! Waiting for emotions…");

  // Bật LED neutral mặc định
  digitalWrite(PIN_NEUTRAL, HIGH);
}


// ══════════════════════════════════════════════
// LOOP
// ══════════════════════════════════════════════
void loop() {
  // Reconnect nếu mất kết nối
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[WiFi] Lost connection, reconnecting…");
    connectWiFi();
  }

  if (!mqttClient.connected()) {
    connectMQTT();
  }

  mqttClient.loop();

  // Xử lý cảm xúc mới
  if (newEmotion) {
    newEmotion = false;
    Serial.printf("[LED] Blink pattern for: %s on GPIO%d\n",
                  currentEmotion.c_str(), activePin);
    blinkLed(activePin, PATTERNS[patternIndex]);
  }

  delay(10);
}
