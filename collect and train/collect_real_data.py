from rtlsdr import RtlSdr
import numpy as np
import time

sdr = RtlSdr()
sdr.sample_rate = 2.0e6
sdr.center_freq = 865.8e6
sdr.gain = 40

def record_class(class_name, class_label, duration_sec=15):
    print(f"\n--- Recording {class_name} ---")
    print(f"Make sure the correct Arduinos are ON/OFF as requested!")
    for i in range(3, 0, -1):
        print(f"Starting in {i}...")
        time.sleep(1)
        
    print("🔴 RECORDING NOW! Leave the Arduinos running...")
    X_list = []
    y_list =[]
    
    start_time = time.time()
    while time.time() - start_time < duration_sec:
        # Read exactly 1024 samples for the CNN
        samples = sdr.read_samples(1024)
        
        # Normalize the real data (remove DC spike and scale)
        samples = samples - np.mean(samples)
        samples = samples / (np.std(samples) + 1e-8)
        
        iq_matrix = np.column_stack((np.real(samples), np.imag(samples)))
        X_list.append(iq_matrix)
        y_list.append(class_label)
        
    print(f"✅ Captured {len(X_list)} samples for {class_name}.")
    return np.array(X_list, dtype=np.float32), np.array(y_list, dtype=np.int32)

try:
    print("=== LORA AI DATASET GENERATOR ===")
    
    # Class 0
    input("\n1. Turn OFF BOTH Arduinos (PU1 and PU2). \nPress ENTER to record Background Noise (00)...")
    X0, y0 = record_class("Both Free (00)", 0)
    
    # Class 1
    input("\n2. Turn ON PU1 (865.3) and keep PU2 OFF. \nPress ENTER to record (10)...")
    X1, y1 = record_class("865.3 Occupied (10)", 1)
    
    # Class 2
    input("\n3. Turn OFF PU1 and turn ON PU2 (866.3). \nPress ENTER to record (01)...")
    X2, y2 = record_class("866.3 Occupied (01)", 2)
    
    # Class 3
    input("\n4. Turn ON BOTH PU1 and PU2. \nPress ENTER to record (11)...")
    X3, y3 = record_class("Both Occupied (11)", 3)

    print("\n💾 Saving Real-World Dataset...")
    X_real = np.concatenate((X0, X1, X2, X3))
    y_real = np.concatenate((y0, y1, y2, y3))
    np.savez_compressed("real_lora_dataset.npz", X=X_real, y=y_real)
    print(f"🎉 Done! Successfully saved {X_real.shape[0]} real-world samples to 'real_lora_dataset.npz'.")

finally:
    sdr.close()