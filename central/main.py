import time
import threading
import config
from radio import Radio
from sdr_sensing import SDRSensor
from queue_manager import QueueManager
from display import display_system

def main_loop():
    radio = Radio()
    qm = QueueManager(radio)
    sdr = SDRSensor() if config.USE_SDR else None
    
    last_display = time.time()
    last_alloc = time.time()
    last_pu_timeout_check = time.time()

    # Packet listener thread
    def packet_listener():
        while True:
            try:
                packet = radio.receive(timeout=0.5)
                if packet:
                    qm.stats['packets_received'] += 1
                    parts = packet.split(',')
                    if len(parts) < 3:
                        continue
                    try:
                        src = int(parts[0])
                        msg = parts[1]
                        dst = int(parts[-1])
                        if dst != config.OWN_ADDRESS:
                            continue
                    except:
                        continue
                        
                    qm.update_user_active(src)

                    if src in config.PU_IDS:
                        qm.add_message(f"📥 RCVD PU MSG: {packet}")
                        if msg == "start" or msg == "PU":
                            qm.handle_pu_packet(src)
                            radio.send(f"{src},ACK,{config.OWN_ADDRESS}")
                        elif msg == "end":
                            qm.handle_pu_timeout(src)
                    elif src in config.SU_IDS:
                        if msg == "end":
                            qm.add_message(f"📥 RCVD SU MSG: {packet}")
                            qm.handle_su_end(src)
                        elif msg == "start":
                            qm.add_message(f"📥 RCVD SU MSG: {packet}")
                            qm.handle_su_request(src)
                        elif msg == "DATA":
                            # Format: src,DATA,temp,hum,mq135,dst
                            if len(parts) >= 6:
                                try:
                                    temp = float(parts[2])
                                    hum = float(parts[3])
                                    mq135 = int(parts[4])
                                    qm.update_sensor_data(src, temp, hum, mq135)
                                except ValueError:
                                    pass
            except Exception as e:
                qm.add_message(f"⚠️ Radio error: {e}")
                time.sleep(1)

    listener_thread = threading.Thread(target=packet_listener, daemon=True)
    listener_thread.start()

    # Main Loop
    while True:
        now = time.time()

        # ----- Get occupied sub-channels from SDR -----
        sdr_occupied =[]
        if sdr and sdr.active:
            sdr_occupied = sdr.get_occupied_subchannels()
            
            # INSTANT EVICTION: If SDR detects occupancy on a channel an SU is using, kick them off!
            vacated_this_loop = set()
            for ch in sdr_occupied:
                occupant = qm.subchannel_occupancy[ch]['occupied_by']
                if occupant and occupant.startswith('SU'):
                    try:
                        su_num = int(occupant.replace('SU', ''))
                        su_id = su_num + 3  # SU1 is ID 4, SU2 is ID 5
                        if su_id not in vacated_this_loop:
                            qm.add_message(f"⚠️ SDR detected Primary User! Vacating SU{su_num} instantly.")
                            qm.vacate_su(su_id)
                            vacated_this_loop.add(su_id)
                    except:
                        pass
        
        # ----- Allocate channels -----
        if now - last_alloc > 2:   # every 2 seconds
            qm.allocate_channels(sdr_occupied)
            last_alloc = now

        # ----- Check PU timeouts (packet-based) -----
        if now - last_pu_timeout_check > 2:
            for pu_id in config.PU_IDS:
                if qm.user_status[pu_id]['active'] and now - qm.user_status[pu_id]['last_seen'] > config.PU_TIMEOUT:
                    qm.handle_pu_timeout(pu_id)
            last_pu_timeout_check = now

        # ----- CLI Display -----
        if now - last_display > config.DISPLAY_INTERVAL:
            display_system(qm, sdr.active if sdr else False, sdr_occupied)
            last_display = now

        time.sleep(0.5)

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        print("\nShutting down Central Node...")