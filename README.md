# 📡 AI-Powered LoRa Cognitive Radio Network (CRN)

> 🚀 **Edge-AI Dynamic Spectrum Access System using LoRa + SDR + Deep Learning**

---

## 📖 **Project Overview**

This project implements a **Cognitive Radio Central Node** (running on a Raspberry Pi or Linux PC) that dynamically manages a **1 MHz radio band (865.3 – 866.3 MHz)**.

The band is divided into **10 sub-channels (100 kHz each)**.

The system performs **real-time spectrum sensing** using an **RTL-SDR** combined with a **Quantized TensorFlow Lite (TFLite) CNN model**.

👉 If a **Primary User (PU)** is detected:

* The system **instantly evicts Secondary Users (SUs)**
* Prevents interference
* Reallocates spectrum dynamically

👉 Secondary Users (IoT nodes) transmit:

* 🌡️ Temperature
* 💧 Humidity
* 🧪 Gas data

---

## ✨ **Features**

* 🤖 **Deep Learning Spectrum Sensing**
  Real-time IQ data classification using a custom CNN

* ⚡ **Float16 Quantization**
  Optimized TFLite model for low-power edge devices

* 🔄 **Instant Eviction**
  Automatic SU removal when PU is detected

* 📊 **Dynamic Terminal Dashboard**
  Real-time channel visualization with emojis

* 🧵 **Thread-Safe LoRa Architecture**
  SPI locks prevent crashes in multi-threaded systems

---

## 🏗️ **System Architecture**

```text
                +------------------------+
                |  Cognitive Controller  |
                | (Raspberry Pi / PC)    |
                +----------+-------------+
                           |
         +-----------------+------------------+
         |                                    |
   +-----v-----+                       +------v------+
   |  RTL-SDR  |                       |  LoRa Radio |
   | Spectrum  |                       | (RFM95x)    |
   | Sensing   |                       | Control Tx  |
   +-----------+                       +-------------+
         |
   IQ Samples → CNN → Decision Engine
                                   |
                    +--------------+--------------+
                    |                             |
             +------v------+               +------v------+
             |  Primary    |               | Secondary   |
             |  Users (PU) |               | Users (SU)  |
             +-------------+               +-------------+
```

---

## 📊 **Channel Visualization Example**

```text
Channel Status:
[🟢][🟢][🔴][🟡][🟢][🟢][🔴][🟢][🟢][🟢]

🟢 Free   🔴 PU Active   🟡 SU Active
```

---

## 🛠️ **Hardware Requirements**

### 🔹 Central Node (Controller)

* Raspberry Pi or Linux PC
* RTL-SDR (RTL2832U)
* RFM95x LoRa Module (SPI)

### 🔹 IoT Nodes

* Arduino / Microcontroller
* LoRa Module (SX127x / RFM95)
* Sensors:

  * Temperature
  * Humidity
  * Gas

---

## 💻 **Software Requirements**

* Python 3.9
* TensorFlow Lite
* NumPy
* RTL-SDR drivers (`librtlsdr`)
* SPI libraries (`spidev`)

---

## ⚙️ **How It Works**

1. 📡 **Spectrum Sensing**

   * RTL-SDR scans frequency band continuously

2. 🤖 **AI Classification**

   * CNN model detects PU activity

3. 🧠 **Decision Engine**

   * Allocates channels to SUs

4. ⚡ **Eviction Mechanism**

   * SU vacates immediately if PU appears

5. 📤 **Data Transmission**

   * IoT nodes send sensor data

---

## 🚀 **Getting Started**

### 1️⃣ Clone Repository

```bash
git clone https://github.com/Ncy7/cognitive_radio_major_project.git
cd cognitive_radio_major_project
```

### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 3️⃣ Run the System

```bash
python main.py
```

---

## 🧠 **AI Model Details**

| Feature      | Description          |
| ------------ | -------------------- |
| Model        | CNN                  |
| Input        | IQ Samples           |
| Output       | PU / No PU           |
| Optimization | Float16 Quantization |
| Runtime      | TensorFlow Lite      |

---

## 🔥 **Advantages**

* ⚡ Real-time spectrum decisions
* 📉 Interference reduction
* 🔋 Low power consumption
* 📡 Efficient spectrum usage

---

## 🛣️ **Future Improvements**

* 🌍 Multi-band support
* 🤖 Reinforcement learning-based allocation
* 📊 Web dashboard (GUI)
* ☁️ Cloud analytics integration

---

## 🤝 **Contributing**

Contributions are welcome!
Feel free to fork and submit a pull request.

---

## 📜 **License**

MIT License

---

## ⭐ **Support**

If you like this project:

👉 **Star the repository**
👉 **Share with others**

---

<p align="center">
  🚀 Built with AI + Wireless Communication 🚀
</p>
