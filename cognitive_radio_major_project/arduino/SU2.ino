#include <SPI.h>
#include <RH_RF95.h>
#include <DHT.h>

// RFM95 / LoRa Pin definitions for Arduino (Uno/Mega)
#define RFM95_CS 10
#define RFM95_RST 9
#define RFM95_INT 2

// Sensor Pin Definitions
#define DHTPIN 4
#define DHTTYPE DHT11
#define MQ135PIN A0

// Cognitive Radio Configurations
#define CN_Frequency 867.3 // Control Channel frequency
#define CN_Address 1       // Address of the Central Node
#define SU_Address 5       // Set 4 for SU1, or 5 for SU2

#define SEND_DURATION_MS 10000 // How long the SU transmits data on the allocated channel
#define BREAK_DURATION_MS 4000 // Cool-down sleep interval

RH_RF95 rf95(RFM95_CS, RFM95_INT);
DHT dht(DHTPIN, DHTTYPE);

// 🏔️ Fallback Values (applied if physical sensors are inactive/fail)
const float DEFAULT_TEMP = 25.0;
const float DEFAULT_HUM = 45.0;
const int DEFAULT_MQ135 = 380;

float allocatedFreq = 0;
bool channelAllocated = false;
unsigned long transmissionStart = 0;
bool inTransmission = false;

void setup() {
  pinMode(RFM95_RST, OUTPUT);
  digitalWrite(RFM95_RST, HIGH);
  
  Serial.begin(9600);
  while (!Serial);

  dht.begin();
  
  digitalWrite(RFM95_RST, LOW); delay(10);
  digitalWrite(RFM95_RST, HIGH); delay(10);

  if (!rf95.init()) {
    Serial.println("❌ LoRa initialization failed!"); 
    while (1); 
  }
  
  rf95.setFrequency(CN_Frequency);
  rf95.setTxPower(23, false);
  Serial.print("✅ SU Ready (Address ID: ");
  Serial.print(SU_Address);
  Serial.println("). Listening on Control Channel.");
}

void loop() {
  // --- PHASE 1 & 2: REQUEST AND ACQUIRE SPECTRUM CHANNEL ---
  if (!channelAllocated) {
    sendAccessRequest();
    listenForChannelFrequency();
    delay(2000); // Give it some retry spacing
    if (channelAllocated) {
      transmissionStart = millis();
      inTransmission = true;
    }
  }

  // --- PHASE 3: TRANSMITTING SENSOR DATA ---
  if (channelAllocated && inTransmission) {
    if (millis() - transmissionStart < SEND_DURATION_MS) {
      sendSensorData();
      delay(1000); // Pulse data every 1 second
    } else {
      inTransmission = false;
      sendEndMessage();
      channelAllocated = false;
      allocatedFreq = 0;
      delay(BREAK_DURATION_MS);
    }
  }
}

void sendAccessRequest() {
  rf95.setFrequency(CN_Frequency);
  String dataToSend = String(SU_Address) + ",start," + String(CN_Address);
  
  Serial.println("📤 Requesting Channel...");
  rf95.send((uint8_t*)dataToSend.c_str(), dataToSend.length());
  rf95.waitPacketSent();
}

void listenForChannelFrequency() {
  rf95.setFrequency(CN_Frequency);
  uint8_t buf[RH_RF95_MAX_MESSAGE_LEN];
  uint8_t len = sizeof(buf);
  unsigned long startTime = millis();

  while (millis() - startTime < 8000) { // Wait up to 8 seconds for a channel grant
    if (rf95.waitAvailableTimeout(500)) {
      if (rf95.recv(buf, &len)) {
        String msg = "";
        for (int i = 0; i < len; i++) msg += (char)buf[i];

        if (msg.startsWith(String(SU_Address) + ",")) {
          int first = msg.indexOf(',');
          int second = msg.indexOf(',', first + 1);
          float newFreq = msg.substring(first + 1, second).toFloat();

          if (newFreq > 0) {
            allocatedFreq = newFreq;
            channelAllocated = true;
            Serial.println("✅ Frequency Allocated: " + String(newFreq) + " MHz");
            return;
          } else if (newFreq == -1) {
            Serial.println("❌ Central node says no channels free, retrying later...");
            delay(3000);
            return;
          }
        }
      }
    }
  }
}

void sendSensorData() {
  // 1. Read sensors
  float h = dht.readHumidity();
  float t = dht.readTemperature();
  int mq135Value = analogRead(MQ135PIN);

  // 🛡️ Sensor Reliability Protection
  if (isnan(h) || isnan(t)) {
    t = DEFAULT_TEMP;
    h = DEFAULT_HUM;
  }
  if (mq135Value < 0 || mq135Value > 1023) {
    mq135Value = DEFAULT_MQ135;
  }

  // Format matches Python: "Source_SU, DATA, Temp, Hum, MQ_Metric, Destination_CN"
  String payload = String(SU_Address) + ",DATA," + String(t,1) + "," + String(h,1) + "," + String(mq135Value) + "," + String(CN_Address);
  
  // 2. Report data to Central Node ON THE CONTROL CHANNEL so Dashboard updates
  rf95.setFrequency(CN_Frequency);
  delay(10);
  rf95.send((uint8_t*)payload.c_str(), payload.length());
  rf95.waitPacketSent(1000);
  
  // 3. Hop to the ALLOCATED CHANNEL and broadcast so the SDR detects the radio waves
  rf95.setFrequency(allocatedFreq);
  delay(10);
  String dummyPayload = "SU_TRANSMITTING_ON_ALLOCATED_SPECTRUM";
  rf95.send((uint8_t*)dummyPayload.c_str(), dummyPayload.length());
  rf95.waitPacketSent(1000);

  Serial.println("📤 Sent Dashboard Telemetry & Occupied " + String(allocatedFreq) + " MHz");
}

void sendEndMessage() {
  rf95.setFrequency(CN_Frequency);
  delay(10);
  String endMsg = String(SU_Address) + ",end," + String(CN_Address);
  
  for (int i = 0; i < 3; i++) {
    rf95.send((uint8_t*)endMsg.c_str(), endMsg.length());
    rf95.waitPacketSent(1000);
    delay(500);
  }
  Serial.println("🏁 Cycle complete, ending LoRa transmission.");
}