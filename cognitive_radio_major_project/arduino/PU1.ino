#include <SPI.h>
#include <RH_RF95.h>

#define RFM95_CS 10
#define RFM95_RST 9
#define RFM95_INT 2

#define PU_FREQ 865.3
#define CN_FREQ 867.3

RH_RF95 rf95(RFM95_CS, RFM95_INT);

uint8_t PU_ADDR = 2;
uint8_t CN_ADDR = 1;

bool handshakeDone = false;
unsigned long cycleStart = 0;
bool transmitting = false;

void setup() {
  pinMode(RFM95_RST, OUTPUT);
  digitalWrite(RFM95_RST, HIGH);
  Serial.begin(9600);
  // Wait up to 3 seconds for serial monitor to open
  unsigned long start = millis();
  while (!Serial && millis() - start < 3000);

  Serial.println("PU1 Starting...");

  digitalWrite(RFM95_RST, LOW); delay(10);
  digitalWrite(RFM95_RST, HIGH); delay(10);

  if (!rf95.init()) {
    Serial.println("LoRa init failed!");
    while (1);
  }
  rf95.setTxPower(23, false);

  // Start with handshake
  performHandshake();
}

void loop() {
  if (!handshakeDone) {
    // If handshake failed, retry after delay
    performHandshake();
    return;
  }

  unsigned long now = millis();

  if (!transmitting && (now - cycleStart >= 4000)) {
    // Start transmitting for 10 seconds
    transmitting = true;
    rf95.setFrequency(PU_FREQ);
    cycleStart = now;
    // Send start notification to central node (optional but good)
    sendPacket(String(PU_ADDR) + ",start," + String(CN_ADDR));
    Serial.println("PU1 start transmission");
  }
  else if (transmitting && (now - cycleStart >= 10000)) {
    // Stop transmitting
    transmitting = false;
    sendPacket(String(PU_ADDR) + ",end," + String(CN_ADDR));
    Serial.println("PU1 end transmission");
    cycleStart = now;
    rf95.setFrequency(CN_FREQ);   // return to control channel
  }

  if (transmitting) {
    // Send a traffic packet every 500 ms
    static int pktNum = 0;
    char buf[25] = "PU1 traffic #   ";
    itoa(pktNum++, buf + 15, 10);
    rf95.send((uint8_t*)buf, strlen(buf));
    rf95.waitPacketSent();
    Serial.println("TX: " + String(buf));
    delay(500);
  }
}

void performHandshake() {
  rf95.setFrequency(CN_FREQ);
  for (int i = 0; i < 5; i++) {
    String msg = String(PU_ADDR) + ",PU," + String(CN_ADDR);
    sendPacket(msg);
    Serial.println("Handshake attempt " + String(i+1) + ": " + msg);

    uint8_t buf[RH_RF95_MAX_MESSAGE_LEN];
    uint8_t len = sizeof(buf);
    if (rf95.waitAvailableTimeout(2000) && rf95.recv(buf, &len)) {
      String reply = String((char*)buf);
      if (reply.startsWith(String(PU_ADDR))) {
        Serial.println("✅ Handshake OK: " + reply);
        handshakeDone = true;
        cycleStart = millis();   // start idle period (will wait 4s before first TX)
        return;
      }
    }
    delay(500);
  }
  Serial.println("❌ Handshake failed, retry later...");
  delay(5000);
}

void sendPacket(String msg) {
  rf95.send((uint8_t*)msg.c_str(), msg.length());
  rf95.waitPacketSent();
}