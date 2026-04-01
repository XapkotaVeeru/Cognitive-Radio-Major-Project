import time
import config

class QueueManager:
    def __init__(self, radio):
        self.radio = radio
        self.queue =[]
        self.user_status = {
            2: {'name': 'PU1', 'active': False, 'last_seen': 0},
            3: {'name': 'PU2', 'active': False, 'last_seen': 0},
            4: {'name': 'SU1', 'active': False, 'last_seen': 0, 'allocated_subchannels':[], 'requested': False},
            5: {'name': 'SU2', 'active': False, 'last_seen': 0, 'allocated_subchannels': [], 'requested': False}
        }
        self.subchannel_occupancy =[{'occupied': False, 'occupied_by': None} for _ in range(config.NUM_SUBCHANNELS)]
        self.stats = {'packets_received': 0, 'su_requests': 0, 'allocations': 0}
        self.message_history =[]
        self.sensor_data = {
            4: {'temp': None, 'hum': None, 'mq135': None, 'last_update': 0},
            5: {'temp': None, 'hum': None, 'mq135': None, 'last_update': 0}
        }

    def update_sensor_data(self, su_id, temp, hum, mq135):
        if su_id in self.sensor_data:
            self.sensor_data[su_id]['temp'] = temp
            self.sensor_data[su_id]['hum'] = hum
            self.sensor_data[su_id]['mq135'] = mq135
            self.sensor_data[su_id]['last_update'] = time.time()
            self.add_message(f"📊 SU{su_id-3} sensor: {temp:.1f}°C, {hum:.1f}%, MQ={mq135}")

    def update_user_active(self, user_id):
        if user_id in self.user_status:
            self.user_status[user_id]['active'] = True
            self.user_status[user_id]['last_seen'] = time.time()

    def handle_pu_packet(self, pu_id):
        self.update_user_active(pu_id)
        if pu_id == 2:
            occupied_range = range(config.PU1_START, config.PU1_END + 1)
        else:
            occupied_range = range(config.PU2_START, config.PU2_END + 1)

        for su_id in config.SU_IDS:
            su = self.user_status[su_id]
            if any(ch in occupied_range for ch in su['allocated_subchannels']):
                self.vacate_su(su_id)

        for ch in occupied_range:
            self.subchannel_occupancy[ch]['occupied'] = True
            self.subchannel_occupancy[ch]['occupied_by'] = f'PU{pu_id-1}'
        self.add_message(f"🔴 PU{pu_id-1} active, occupying sub-channels {list(occupied_range)}")

    def handle_pu_timeout(self, pu_id):
        self.user_status[pu_id]['active'] = False
        if pu_id == 2:
            occupied_range = range(config.PU1_START, config.PU1_END + 1)
        else:
            occupied_range = range(config.PU2_START, config.PU2_END + 1)

        for ch in occupied_range:
            if self.subchannel_occupancy[ch]['occupied_by'] == f'PU{pu_id-1}':
                self.subchannel_occupancy[ch]['occupied'] = False
                self.subchannel_occupancy[ch]['occupied_by'] = None
        self.add_message(f"⏱️ PU{pu_id-1} timed out, freed sub-channels {list(occupied_range)}")

    def handle_su_request(self, su_id):
        if self.user_status[su_id]['allocated_subchannels']:
            # 🚀 FIX: The SU missed the packet! Re-send the allocation instead of ignoring!
            block = self.user_status[su_id]['allocated_subchannels']
            freq_start = config.BAND_START + block[0] * config.SUBCHANNEL_WIDTH
            freq_end = config.BAND_START + (block[-1] + 1) * config.SUBCHANNEL_WIDTH
            freq_center = (freq_start + freq_end) / 2
            
            self.radio.send(f"{su_id},{freq_center:.2f},{config.OWN_ADDRESS}")
            self.add_message(f"🔄 Resent allocation to SU{su_id-3} ({freq_center:.2f} MHz)")
            return
            
        if su_id not in self.queue:
            self.queue.append(su_id)
            self.user_status[su_id]['requested'] = True
            self.stats['su_requests'] += 1
            self.add_message(f"➕ SU{su_id-3} added to queue")

    def handle_su_end(self, su_id):
        subchannels = self.user_status[su_id]['allocated_subchannels']
        for ch in subchannels:
            self.subchannel_occupancy[ch]['occupied'] = False
            self.subchannel_occupancy[ch]['occupied_by'] = None
        self.user_status[su_id]['allocated_subchannels'] =[]
        self.user_status[su_id]['requested'] = False
        self.add_message(f"📢 SU{su_id-3} ended, freed sub-channels {subchannels}")
        if su_id in self.queue:
            self.queue.remove(su_id)

    def vacate_su(self, su_id):
        subchannels = self.user_status[su_id]['allocated_subchannels']
        if subchannels:
            self.radio.send(f"{su_id},-1,{config.OWN_ADDRESS}")
            for ch in subchannels:
                self.subchannel_occupancy[ch]['occupied'] = False
                self.subchannel_occupancy[ch]['occupied_by'] = None
            self.user_status[su_id]['allocated_subchannels'] =[]
            self.user_status[su_id]['requested'] = False
            self.add_message(f"⚠️ SU{su_id-3} vacated from sub-channels {subchannels}")
        if su_id not in self.queue:
            self.queue.insert(0, su_id)
            self.user_status[su_id]['requested'] = True

    def allocate_channels(self, occupied_subchannels):
        # Build list of free sub-channels
        free =[ch for ch in range(config.NUM_SUBCHANNELS) 
                if not self.subchannel_occupancy[ch]['occupied'] and ch not in occupied_subchannels]

        while self.queue and len(free) >= config.SU_SUBCHANNELS:
            block = None
            for i in range(len(free) - config.SU_SUBCHANNELS + 1):
                if free[i:i+config.SU_SUBCHANNELS] == list(range(free[i], free[i]+config.SU_SUBCHANNELS)):
                    block = free[i:i+config.SU_SUBCHANNELS]
                    break
            if not block:
                break

            su_id = self.queue.pop(0)
            for ch in block:
                self.subchannel_occupancy[ch]['occupied'] = True
                self.subchannel_occupancy[ch]['occupied_by'] = f'SU{su_id-3}'
            self.user_status[su_id]['allocated_subchannels'] = block
            self.user_status[su_id]['requested'] = False
            self.stats['allocations'] += 1

            freq_start = config.BAND_START + block[0] * config.SUBCHANNEL_WIDTH
            freq_end = config.BAND_START + (block[-1] + 1) * config.SUBCHANNEL_WIDTH
            freq_center = (freq_start + freq_end) / 2
            
            self.radio.send(f"{su_id},{freq_center:.2f},{config.OWN_ADDRESS}")
            self.add_message(f"✅ SU{su_id-3} allocated sub-channels {block} ({freq_center:.2f} MHz)")
            
            free =[ch for ch in free if ch not in block]

    def add_message(self, msg):
        self.message_history.append(f"[{time.strftime('%H:%M:%S')}] {msg}")
        if len(self.message_history) > 10:
            self.message_history.pop(0)