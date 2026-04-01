#include <SPI.h>
#include <RH_RF95.h>

#define RFM95_CS 10
#define RFM95_RST 9
#define RFM95_INT 2

#define PU_FREQ 866.3
#define CN_FREQ 867.3

RH_RF95 rf95(RFM95_CS, RFM95_INT);

uint8_t PU_ADDR = 3;
uint8_t CN_ADDR = 1;

unsigned long cycleStart = 0;
bool transmitting = false;
bool handshakeDone = false;

void setup() {
  pinMode(RFM95_RST, OUTPUT);
  digitalWrite(RFM95_RST, HIGH);
  Serial.begin(9600);

  digitalWrite(RFM95_RST, LOW); delay(10);
  digitalWrite(RFM95_RST, HIGH); delay(10);
  rf95.init();
  rf95.setTxPower(23, false);
  performHandshake();   // Register with central node
}

void loop() {
  unsigned long now = millis();
  if (!handshakeDone) {
    performHandshake();
    return;
  }

  if (!transmitting && (now - cycleStart >= 4000)) {
    // Start transmitting for 10 seconds
    transmitting = true;
    rf95.setFrequency(PU_FREQ);
    cycleStart = now;
    // Send start packet to central node
    sendPacket(String(PU_ADDR) + ",start," + String(CN_ADDR));
    Serial.println("PU2 start transmission");
  } else if (transmitting && (now - cycleStart >= 10000)) {
    // Stop transmitting
    transmitting = false;
    // Send end packet to central node
    sendPacket(String(PU_ADDR) + ",end," + String(CN_ADDR));
    Serial.println("PU2 end transmission");
    cycleStart = now;
    rf95.setFrequency(CN_FREQ);   // Return to control channel
  }

  if (transmitting) {
    // Send traffic data (simulated)
    char buf[20] = "PU2 traffic #";
    static int cnt = 0;
    itoa(cnt++, buf + 13, 10);
    rf95.send((uint8_t*)buf, strlen(buf));
    rf95.waitPacketSent();
    delay(500);   // pace the traffic
  }
}

void performHandshake() {
  rf95.setFrequency(CN_FREQ);
  for (int i = 0; i < 5; i++) {
    sendPacket(String(PU_ADDR) + ",PU," + String(CN_ADDR));
    uint8_t buf[RH_RF95_MAX_MESSAGE_LEN];
    uint8_t len = sizeof(buf);
    if (rf95.waitAvailableTimeout(2000) && rf95.recv(buf, &len)) {
      String msg = String((char*)buf);
      if (msg.startsWith(String(PU_ADDR))) {
        Serial.println("Handshake OK");
        handshakeDone = true;
        cycleStart = millis();
        return;
      }
    }
    delay(500);
  }
  Serial.println("Handshake failed, retry later");
  delay(5000);
}

void sendPacket(String msg) {
  rf95.send((uint8_t*)msg.c_str(), msg.length());
  rf95.waitPacketSent();
}