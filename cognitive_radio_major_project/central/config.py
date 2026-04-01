import time

# ===== Simulation & Hardware mode =====
SIMULATION_MODE = False
USE_SDR = True  # Set to True to enable the RTL-SDR and ML Model
ENABLE_DUMMY_SU_REQUESTS = False

# ===== Hardware imports =====
if not SIMULATION_MODE:
    import board
    import digitalio
    CS = digitalio.DigitalInOut(board.CE1)
    RESET = digitalio.DigitalInOut(board.D25)
else:
    class MockDigitalInOut:
        pass
    CS = MockDigitalInOut()
    RESET = MockDigitalInOut()

# ===== Frequencies (MHz) =====
PU1_FREQ_MHZ = 865.3
PU2_FREQ_MHZ = 866.3
CONTROL_FREQ_MHZ = 867.3

OWN_ADDRESS = 1
PU_IDS = [2, 3]
SU_IDS = [4, 5]
ALL_USERS = PU_IDS + SU_IDS

PU_TIMEOUT = 10
TRANSMIT_INTERVAL = 2

# ===== Sub-channel configuration =====
BAND_START = 865.3
BAND_END = 866.3
NUM_SUBCHANNELS = 10                 # 10 sub-channels of 100 kHz each
SUBCHANNEL_WIDTH = 0.1               # 100 kHz

# PU allocation: first 5 sub-channels (0-4) for PU1, last 5 (5-9) for PU2
PU1_START = 0
PU1_END = 4
PU2_START = 5
PU2_END = 9

# SU allocation: each SU gets 2 consecutive sub-channels (200 kHz)
SU_SUBCHANNELS = 2

# ===== ML & System Thresholds =====
DISPLAY_INTERVAL = 3
MODEL_PATH = "./model.tflite"

# SU transmission timing (seconds)
SU_SEND_DURATION = 10
SU_BREAK_DURATION = 4