import time
import config

def clear_screen():
    print("\033[2J\033[H", end="")

def draw_subchannel_circles(qm, sdr_occupied):
    circles = []
    for i in range(config.NUM_SUBCHANNELS):
        occupant = qm.subchannel_occupancy[i]['occupied_by']
        
        # Red if SDR physically detects PU, or if PU packet received
        if i in sdr_occupied or (occupant and occupant.startswith('PU')):
            circles.append("🔴")
        # Yellow if allocated to an SU
        elif occupant and occupant.startswith('SU'):
            circles.append("🟡")
        # Green if Free
        else:
            circles.append("🟢")
            
    return "   ".join(circles)

def display_system(qm, sdr_active, sdr_occupied):
    clear_screen()

    print("\n" + "="*60)
    print("COGNITIVE RADIO CENTRAL NODE")
    print("="*60)

    print("\nSub-channel occupancy (visual):")
    print("  " + draw_subchannel_circles(qm, sdr_occupied))
    print("   0    1    2    3    4    5    6    7    8    9\n")

    print("Scanning spectrum...")
    for i in range(config.NUM_SUBCHANNELS):
        freq_center = config.BAND_START + i * config.SUBCHANNEL_WIDTH + config.SUBCHANNEL_WIDTH/2
        occupant = qm.subchannel_occupancy[i]['occupied_by']
        
        if i in sdr_occupied:
            status = "🔴 PU Detected (SDR)"
        elif occupant and occupant.startswith('PU'):
            status = f"🔴 Occupied ({occupant})"
        elif occupant and occupant.startswith('SU'):
            status = f"🟡 Occupied ({occupant})"
        else:
            status = "🟢 Free"
            
        print(f"  {freq_center:.2f} MHz → {status}")

    free =[ch for ch in range(config.NUM_SUBCHANNELS) if not qm.subchannel_occupancy[ch]['occupied'] and ch not in sdr_occupied]
    free_freqs =[config.BAND_START + ch*config.SUBCHANNEL_WIDTH + config.SUBCHANNEL_WIDTH/2 for ch in free]
    print(f"\nAvailable channels: {[round(f,2) for f in free_freqs]}")

    print("\n" + "-"*40)
    print("📡 SECONDARY USER (SU) STATUS")
    print("-"*40)

    active_su_found = False
    for active_su in config.SU_IDS:
        ch_list = qm.user_status[active_su]['allocated_subchannels']
        if ch_list:
            active_su_found = True
            freq_start = config.BAND_START + ch_list[0] * config.SUBCHANNEL_WIDTH
            freq_end = config.BAND_START + (ch_list[-1] + 1) * config.SUBCHANNEL_WIDTH
            freq_center = (freq_start + freq_end) / 2
            print(f"Active SU: SU{active_su-3} on sub-channels {ch_list} ({freq_center:.2f} MHz)")

            sens = qm.sensor_data.get(active_su, {})
            if sens.get('temp') is not None:
                print(f"  🌡️  Temperature: {sens['temp']:.1f} °C")
                print(f"  💧 Humidity:    {sens['hum']:.1f} %")
                print(f"  🧪 MQ135 gas:   {sens['mq135']}")
                print(f"  ⏱️  Last update: {time.strftime('%H:%M:%S', time.localtime(sens['last_update']))}")
            else:
                print("  ⏳ Waiting for sensor data from SU...")
                
    if not active_su_found:
        print("No SU currently active (no channel allocated).")

    print(f"\nQueue length: {len(qm.queue)}")
    if qm.message_history:
        print("\nRecent activity:")
        for msg in qm.message_history[-6:]:
            print(f"  {msg}")

    print("="*60)