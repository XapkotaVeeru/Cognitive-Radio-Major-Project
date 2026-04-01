import numpy as np
import tensorflow as tf
import config
from rtlsdr import RtlSdr

def calculate_signal_power(samples):
    try:
        power = 10 * np.log10(np.mean(np.abs(samples)**2) + 1e-10)
        return power
    except:
        return -100

class SDRSensor:
    def __init__(self):
        self.active = config.USE_SDR
        self.sdr = None
        self.interpreter = None
        self.input_details = None
        self.output_details = None
        
        if self.active:
            try:
                self.sdr = RtlSdr()
                self.sdr.sample_rate = 2.048e6
                self.sdr.gain = 20
                print("✅ SDR initialized.")
            except Exception as e:
                print(f"❌ SDR init failed: {e}")
                self.active = False
                
            try:
                self.interpreter = tf.lite.Interpreter(model_path=config.MODEL_PATH)
                self.interpreter.allocate_tensors()
                self.input_details = self.interpreter.get_input_details()
                self.output_details = self.interpreter.get_output_details()
                self.interpreter.resize_tensor_input(self.input_details[0]['index'], (1, 1024, 2, 1))
                self.interpreter.allocate_tensors()
                print("✅ ML model loaded successfully.")
            except Exception as e:
                print(f"❌ Model load failed: {e}")
                self.active = False

    def get_occupied_subchannels(self):
        if not self.active:
            return[]
        
        state = self.get_occupancy_state()
        occupied = []
        
        if state[0]:   # PU1 active
            occupied.extend(range(config.PU1_START, config.PU1_END + 1))
        if state[1]:   # PU2 active
            occupied.extend(range(config.PU2_START, config.PU2_END + 1))
            
        return occupied

    def get_occupancy_state(self):
        if not self.active:
            return (False, False)
            
        pu1_active = False
        pu2_active = False

        try:
            # 1. Hop to PU1 (865.3 MHz)
            self.sdr.center_freq = config.PU1_FREQ_MHZ * 1e6
            samples1 = self.sdr.read_samples(1024)
            power1 = calculate_signal_power(samples1)
            
            iq1 = np.stack((np.real(samples1), np.imag(samples1)), axis=1).reshape(1, 1024, 2, 1).astype(np.float32)
            self.interpreter.set_tensor(self.input_details[0]['index'], iq1)
            self.interpreter.invoke()
            pred1 = self.interpreter.get_tensor(self.output_details[0]['index'])
            
            # Filter False Positives: Must be Class 1 AND have strong signal AND high confidence
            if np.argmax(pred1[0]) == 1 and power1 > config.SIGNAL_POWER_THRESHOLD and np.max(pred1[0]) > config.ML_CONFIDENCE_THRESHOLD:
                pu1_active = True

            # 2. Hop to PU2 (866.3 MHz)
            self.sdr.center_freq = config.PU2_FREQ_MHZ * 1e6
            samples2 = self.sdr.read_samples(1024)
            power2 = calculate_signal_power(samples2)
            
            iq2 = np.stack((np.real(samples2), np.imag(samples2)), axis=1).reshape(1, 1024, 2, 1).astype(np.float32)
            self.interpreter.set_tensor(self.input_details[0]['index'], iq2)
            self.interpreter.invoke()
            pred2 = self.interpreter.get_tensor(self.output_details[0]['index'])
            
            # Filter False Positives
            if np.argmax(pred2[0]) == 1 and power2 > config.SIGNAL_POWER_THRESHOLD and np.max(pred2[0]) > config.ML_CONFIDENCE_THRESHOLD:
                pu2_active = True

        except Exception as e:
            pass # Ignore random SDR dropouts while hopping

        return (pu1_active, pu2_active)