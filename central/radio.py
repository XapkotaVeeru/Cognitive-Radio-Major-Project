import time
import config
import threading

class Radio:
    def __init__(self):
        self.lock = threading.Lock() # 🚀 FIX: Thread safety for SPI bus
        self.simulation = config.SIMULATION_MODE
        if not self.simulation:
            import busio
            import board
            import adafruit_rfm9x
            self.spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)
            self.rfm9x = adafruit_rfm9x.RFM9x(self.spi, config.CS, config.RESET, config.CONTROL_FREQ_MHZ)
            self.rfm9x.tx_power = 23
        else:
            print("Radio in simulation mode.")

    def send(self, data):
        with self.lock:
            if self.simulation:
                print(f"[SIM] SEND: {data}")
                return True
            try:
                self.rfm9x.send(bytes(data, "UTF-8"))
                return True
            except:
                return False

    def receive(self, timeout=1.0):
        with self.lock:
            if self.simulation:
                return None
            try:
                packet = self.rfm9x.receive(timeout=timeout)
                if packet:
                    return ''.join([chr(b) for b in packet])
            except:
                pass
            return None