# AI-Powered LoRa Cognitive Radio Network (CRN)

**An Edge-AI Driven Dynamic Spectrum Access System using LoRa, SDR, and Deep Learning**

---

## Project Overview

The rapid expansion of wireless technologies, IoT devices, and emerging applications like 6G has created an unprecedented demand for radio frequency spectrum resources. Traditional static spectrum allocation policies have led to extreme inefficiencies—studies by the Spectrum Policy Task Force show that licensed spectrum bands remain unoccupied 15-85% of the time, while unlicensed bands become increasingly congested.

This project addresses the spectrum scarcity crisis by implementing an **Intelligent Cognitive Radio Network (CRN)** that dynamically senses, learns, and adapts to its radio environment in real-time. The system leverages a **Convolutional Neural Network (CNN)** for spectrum sensing and a centralized controller for dynamic spectrum allocation, ensuring optimal spectrum utilization while protecting licensed (Primary) users from interference.

Unlike conventional energy detection methods that struggle at low Signal-to-Noise Ratios (SNR), our deep learning approach automatically extracts discriminative features from raw In-phase and Quadrature (I/Q) samples, achieving superior detection accuracy even in challenging channel conditions.

---

## Project Objectives

### Primary Goals
- Develop an intelligent spectrum sensing engine using CNNs to classify channel occupancy from raw I/Q samples
- Implement dynamic spectrum allocation using First-Come-First-Serve (FCFS) queue management with RTS/CTS handshaking
- Protect Primary Users through instantaneous channel evacuation upon PU reappearance
- Validate system performance through both software-based and hardware-in-the-loop testing
- Optimize for edge deployment using TensorFlow Lite quantization

### Key Metrics Achieved

| Metric | Software Dataset | Real-World Hardware |
|--------|------------------|---------------------|
| Test Accuracy | 99.05% | 75.48% |
| F1-Score | 0.9904 | 0.76 (macro avg) |
| Model Size | 24.16 MB | Optimized for edge |
| Inference Time | 0.1205 ms/sample | Real-time capable |

---

## Key Features

### AI-Based Spectrum Sensing
The system uses a custom CNN architecture that processes 128-sample windows of raw I/Q data to classify spectrum occupancy into four states:
- **State 0 [0,0]**: Both channels free
- **State 1 [1,0]**: 865.3 MHz occupied, 866.3 MHz free  
- **State 2 [0,1]**: 865.3 MHz free, 866.3 MHz occupied
- **State 3 [1,1]**: Both channels occupied

This approach eliminates the need for manual feature engineering and performs reliably even at low SNR where traditional energy detectors fail.

### Edge Optimization with TensorFlow Lite
The trained CNN model is post-trained quantized using TensorFlow Lite, producing a lightweight `.tflite` file suitable for real-time inference on resource-constrained hardware like the Raspberry Pi 4B. This optimization enables:
- Reduced memory footprint
- Faster inference times
- Lower power consumption

### Real-Time Dynamic Spectrum Allocation
The centralized controller manages a First-Come-First-Serve (FCFS) queue for SU transmission requests. Channel allocation decisions are made based on CNN-predicted spectrum states:
- Available channels are immediately assigned to waiting SUs
- Multiple SUs can transmit simultaneously on different free channels
- System continuously monitors and reallocates as conditions change

### Instant Eviction Mechanism
When a Primary User begins transmitting on a channel currently used by a Secondary User:
1. The CNN model detects PU activity
2. Central Node immediately sends a Vacate Channel (VC) command
3. SU halts transmission and is re-queued
4. Channel is cleared for PU use

This ensures absolute priority for licensed users while maximizing spectrum utilization.

### Thread-Safe Communication Architecture
The LoRa communication stack implements SPI locking mechanisms, ensuring stable operation even with concurrent threads handling spectrum sensing and data transmission.

---

## Operating Frequencies

| Channel | Frequency | Purpose |
|---------|-----------|---------|
| PU1 | 865.3 MHz | Primary User Channel 1 |
| PU2 | 866.3 MHz | Primary User Channel 2 |
| Control | 867.3 MHz | LoRa Control Channel |

---

## Hardware Requirements

### Central Node (Cognitive Controller)

| Component | Quantity | Purpose |
|-----------|----------|---------|
| Raspberry Pi 4B (4GB RAM) | 1 | Central processing, ML inference, decision making |
| RTL-SDR Dongle (RTL2832U) | 2 | Spectrum sensing on PU channels |
| UHF Antenna (865-868 MHz) | 2 | Signal reception for SDRs |
| Adafruit RFM95 LoRa Module | 1 | Control channel communication |
| MicroSD Card (32GB Class 10) | 1 | OS and data storage |
| Micro HDMI Cable | 1 | Display interface |

### IoT Nodes (Secondary Users)

| Component | Quantity | Purpose |
|-----------|----------|---------|
| Arduino Uno R3 | 2 | SU node processing |
| Adafruit RFM95 LoRa Module | 2 | Control channel communication |
| Temperature & Humidity Sensor | 2 | Environmental monitoring |
| LoRa Antenna (868 MHz) | 2 | RF communication |

### Primary User Nodes

| Component | Quantity | Purpose |
|-----------|----------|---------|
| Arduino Uno R3 | 2 | PU behavior simulation |
| Adafruit RFM95 LoRa Module | 2 | Status reporting |

### Additional Components

| Component | Quantity |
|-----------|----------|
| 9V Batteries & Connectors | 5 sets |
| Jumper Wires & Breadboards | 1 set |
| Soldering Kit | 1 set |

---

## Software Requirements

### Operating Systems
- **Raspberry Pi OS** (64-bit) - for Central Node operation
- **Windows/Linux/macOS** - for development and model training

### Programming Environments
- **Python 3.9+** - Primary language for Central Node and ML development
- **Arduino IDE** - C++ code compilation and upload for Arduino nodes

### Machine Learning Stack

| Tool | Purpose |
|------|---------|
| TensorFlow 2.x | CNN model development and training |
| Keras | High-level neural network API |
| TensorFlow Lite | Model optimization for edge deployment |
| NumPy | Numerical operations and I/Q sample processing |
| Pandas | Data organization and feature extraction |

### Communication Libraries

| Library | Purpose |
|---------|---------|
| librtlsdr / pyrtlsdr | RTL-SDR control and I/Q sample capture |
| spidev | SPI interface for LoRa modules |
| pyserial | Serial communication with Arduino nodes |

---

## System Operation

### Spectrum Sensing Loop
The system continuously monitors both PU channels:
1. RTL-SDR dongles capture 128-sample windows of raw I/Q data at 865.3 MHz and 866.3 MHz
2. I/Q samples are formatted as (128, 2) tensors (I component + Q component)
3. TensorFlow Lite interpreter runs inference using the optimized CNN model
4. Model outputs probability distribution across 4 possible occupancy states

### Decision Engine and Allocation
Based on the CNN prediction:
- **State [0,0]**: Both channels free -> allocate to first two waiting SUs
- **State [1,0]**: Channel 1 occupied -> allocate Channel 2 to next SU
- **State [0,1]**: Channel 2 occupied -> allocate Channel 1 to next SU
- **State [1,1]**: Both occupied -> all SUs queued, no allocation

### Eviction Process
When PU reappearance is detected:
1. CNN prediction changes from free to occupied
2. Central Node identifies SU(s) using the affected channel
3. VC message sent via LoRa control channel
4. SU halts transmission immediately
5. Affected SU(s) added to front of FCFS queue
6. Channel cleared for PU use

---

## CNN Model Details

### Training Methodology
The system employs a **dual-dataset approach**:
1. **Pre-obtained software dataset** (SDR 802.11 a/g) for baseline benchmarking
2. **Hardware-collected dataset** from actual RTL-SDR captures for final model training

### Dataset Characteristics

| Parameter | Software Dataset | Hardware Dataset |
|-----------|------------------|------------------|
| Source | USRP N210 SDRs | RTL-SDR dongles |
| Bandwidth | 20 MHz | 2 channels @ 5 MHz each |
| SNR Range | Controlled | Variable (-10 dB to +20 dB) |
| Environment | Simulated | Real-world indoor |
| Sample Count | 359,970 | 50,000+ |

### Training Results (Software Dataset)

| Metric | Value |
|--------|-------|
| Test Accuracy | 99.05% |
| Test F1-Score | 0.9904 |
| Test Precision | 0.9905 |
| Test Recall | 0.9905 |
| Model Parameters | 2,106,000 |
| Model Size | 24.16 MB |
| Inference Time | 0.1205 ms/sample |
| FLOPs | 8.78e+06 |

### Real-World Performance (Hardware Dataset)

| Channel State | Precision | Recall | F1-Score |
|---------------|-----------|--------|----------|
| Both Free (00) | 0.65 | 0.83 | 0.73 |
| 865.3 MHz Occupied (10) | 0.82 | 0.74 | 0.78 |
| 866.3 MHz Occupied (01) | 0.74 | 0.71 | 0.73 |
| Both Occupied (11) | 0.85 | 0.74 | 0.79 |

**Overall Test Accuracy:** 75.48%

### Performance Gap Analysis
The significant difference between software (99.05%) and hardware (75.48%) accuracy highlights the domain gap between controlled simulations and real-world deployment:
- **Multipath fading** from signal reflections causes distortion
- **Ambient noise** from electronic devices introduces random fluctuations
- **Interference** from other transmitters creates unexpected patterns
- **Hardware imperfections** (oscillator drift, sampling errors) degrade signal quality

This demonstrates that while CNNs perform exceptionally well in controlled environments, practical deployment requires techniques like data augmentation, domain adaptation, and on-device fine-tuning.

---

## Test Cases and Validation

The system was validated across 8 test cases covering all possible scenarios:

| ID | Scenario | PU Activity | SU Activity | Expected Behavior | Result |
|----|----------|-------------|-------------|-------------------|--------|
| T-01 | Single SU, Unoccupied | [0,0] | SU1 requests | Allocate 865.3 MHz | Pass |
| T-02 | Multiple SUs, Unoccupied | [0,0] | SU1, SU2 in order | SU1->865.3, SU2->866.3 | Pass |
| T-03 | Both Channels Occupied | [1,1] | Any SU request | Queue all requests | Pass |
| T-04 | Single Channel Occupied | [1,0] | SU1 requests | Allocate 866.3 MHz | Pass |
| T-05 | PU Arrives During SU TX | [0,0]->[1,0] | SU1 transmitting | SU1 vacates, re-queues | Pass |
| T-06 | PU Departs | [1,0]->[0,0] | SU1 in queue | Allocate freed channel | Pass |
| T-07 | Both PUs Arrive | [0,0]->[1,1] | SU1, SU2 active | Both vacate, queue | Pass |
| T-08 | PU Arrives, Alternate Free | [1,0] | SU2 on 866.3 | SU2 unaffected | Pass |

All test cases completed successfully, confirming:
- Primary User protection through instant evacuation
- Fair spectrum allocation via FCFS queue
- Robust operation under dynamic conditions

---

## Why This Matters

### Technical Significance
- **Outperforms conventional methods**: CNN-based sensing achieves superior accuracy at low SNR where energy detection fails
- **Real-time edge AI**: TensorFlow Lite optimization enables complex deep learning on resource-constrained hardware
- **Practical implementation**: Bridges the gap between theoretical ML research and hardware-based deployment

### Practical Impact
- **Better spectrum utilization**: Dynamically allocates unused licensed spectrum to secondary users
- **Reduced interference**: Instant PU detection prevents harmful interference to licensed users
- **Energy efficiency**: Optimized for low-power IoT deployments
- **Scalability**: Centralized architecture can be extended to more channels and nodes

### Future-Ready
This project lays the foundation for intelligent wireless networks essential for:
- **5G/6G Networks** - Dynamic spectrum sharing
- **Massive IoT Deployments** - Efficient connectivity for billions of devices
- **Smart Cities** - Reliable communication infrastructure
- **URLLC Applications** - Ultra-reliable low-latency communications

---

## Limitations and Challenges

### Hardware Constraints
- **Processing Power**: Raspberry Pi 4B shows latency spikes during peak processing
- **SDR Limitations**: Consumer-grade RTL-SDRs have limited dynamic range and frequency stability
- **Memory Constraints**: Arduino Uno nodes insufficient RAM for local processing

### Dataset Limitations
- **Hardware Dataset Size**: Limited by manual collection time; larger datasets would improve generalization
- **Environmental Diversity**: Primarily indoor testing; outdoor/mobility scenarios not fully validated
- **Channel Variations**: Deep fading and high interference scenarios underrepresented

### System Limitations
- **Limited Channels**: Only 2 PU channels and 2 SU nodes tested
- **Single Point of Failure**: Centralized architecture fails if Raspberry Pi crashes
- **Control Channel Dependency**: LoRa overhead and potential frequency clashes
- **Sensing Latency**: CNN inference adds slight delay in sensing cycle

### Model Limitations
- **Generalization**: Performance degrades under significantly different environmental conditions
- **Noise Sensitivity**: Accuracy reduces at very low SNR (below -10 dB)
- **Training Dependency**: Quality and diversity of training data directly impacts performance

---

## Future Enhancements

### Hardware Improvements
- **Enhanced Processing**: Upgrade to NVIDIA Jetson Nano or Raspberry Pi 5 for lower latency
- **Higher Quality SDRs**: Implement USRP or BladeRF for better dynamic range and frequency stability
- **Distributed Processing**: Add edge computing capabilities to SU nodes for faster local decisions

### Dataset Expansion
- **Large-Scale Collection**: Gather data across diverse environments (indoor, outdoor, urban, rural)
- **Automated Annotation**: Develop tools for automated data collection and labeling
- **Public Dataset Release**: Share hardware-collected dataset to enable reproducible research

### Architectural Enhancements
- **Multi-Node Cooperative Sensing**: Leverage spatial diversity through cooperative sensing among multiple SUs
- **Decentralized Architecture**: Implement distributed/mesh design to eliminate single point of failure
- **Multi-Channel Support**: Scale to more PU channels and SU nodes

### Model Improvements
- **Advanced Architectures**: Explore ResNet, DenseNet, and Transformer-based models
- **Hybrid CNN-LSTM**: Capture temporal dependencies in PU activity patterns
- **Transfer Learning**: Reduce training data requirements by leveraging pre-trained models
- **Federated Learning**: Collaborative training across multiple CR nodes without sharing raw data

### Real-World Deployment
- **Field Trials**: Long-term outdoor testing to evaluate system robustness
- **Energy Optimization**: Implement adaptive duty cycling for battery-powered nodes
- **5G/6G Integration**: Explore integration with next-generation network architectures
- **Security Enhancements**: Implement defenses against spectrum sensing data falsification (SSDF) attacks

---

## Total Cost

| Component | Quantity | Unit Price (NPR) | Total (NPR) |
|-----------|----------|------------------|-------------|
| Raspberry Pi 4B (4GB RAM) | 1 | 21,500 | 21,500 |
| RTL-SDR Dongle (RTL2832U) | 2 | 15,000 | 30,000 |
| Arduino Uno R3 (Original/Compatible) | 5 | 1,200 | 6,000 |
| Adafruit RFM95 LoRa Transceiver Module | 5 | 1,000 | 5,000 |
| Antennas for SDR (UHF 865–868 MHz) | 2 | 1,000 | 2,000 |
| Micro HDMI Cable | 1 | 350 | 350 |
| MicroSD Card (32GB Class 10) | 1 | 550 | 550 |
| 9V Batteries and Connectors | 5 sets | 60 | 300 |
| Jumper Wires and Breadboards | 1 set | 600 | 600 |
| Temperature and Humidity Sensor | 5 | 500 | 2,500 |
| Miscellaneous (Connectors, Soldering Kit) | 1 set | 1,000 | 1,000 |
| **Total** | | | **69,800 NPR** |

---

## References

1. Upadhye, A., Saravanan, P., Chandra, S.S., & Gurugopinath, S. (2021). "A survey on machine learning algorithms for applications in cognitive radio networks." *IEEE International Conference on Electronics, Computing and Communication Technologies*.

2. Captain, K.M. & Joshi, M.V. (2021). *Spectrum Sensing for Cognitive Radio: Fundamentals and Applications*. CRC Press.

3. Chauhan, P., Deka, S.K., & Sarma, N. (2023). "LSTM-enabled prediction-based channel switching scheduling for multi-channel cognitive radio networks." *Physical Communication*, 60, 102136.

4. Haykin, S. (2005). "Cognitive radio: Brain-empowered wireless communications." *IEEE Journal on Selected Areas in Communications*, 23(2), 201-220.

5. Yucek, T. & Arslan, H. (2009). "A survey of spectrum sensing algorithms for cognitive radio applications." *IEEE Communications Surveys and Tutorials*, 11(1), 116-130.

6. Arjoune, Y. & Kaabouch, N. (2019). "A comprehensive survey on spectrum sensing in cognitive radio networks: Recent advances, new challenges, and future research directions." *Sensors*, 19(1), 126.

7. Uvaydov, D., D'Oro, S., Restuccia, F., & Melodia, T. (2021). "Deepsense: Fast wideband spectrum sensing through real-time in-the-loop deep learning." *IEEE INFOCOM 2021*, 1-10.

---

## Contributing

Contributions are welcome. Please:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

---

## License

This project is licensed under the MIT License.

---

## Authors

**Birat Sapkota**    
**Nageshwor Chaudhary**   
**Nishan Bastola**    
**Sonu Alam**  

**Supervisor:** Er. Krishna Kumar Jha

Department of Electronics and Computer Engineering  
Advanced College of Engineering and Management  
Kalanki, Kathmandu, Nepal

---

<p align="center">
Department of Electronics and Computer Engineering | Advanced College of Engineering and Management
</p>
