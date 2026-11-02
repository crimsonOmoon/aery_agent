<div align="center">

# ⚡ AERY
### Hardware-Integrated Local ReAct Agent & Telemetry Node

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-Qwen_2.5_(3B)-000000?style=for-the-badge)
![Arduino](https://img.shields.io/badge/Hardware-Arduino_/_DHT11-00979D?style=for-the-badge&logo=arduino&logoColor=white)
![Flask](https://img.shields.io/badge/Backend-Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**A lightweight, local-first AI assistant that bridges physical microcontroller sensors and live web search.**  
*Developed to run completely offline on entry-level laptops without expensive GPUs, cloud infrastructure, or paid API keys.*

</div>

---

## ✨ Key Highlights

* **🖥️ Built for Low-End Hardware:** Runs smoothly on dual-core CPUs and 4 GB of RAM with automatic background lifecycle management for Ollama.
* **🌡️ Real-Time Hardware Telemetry:** Queries physical ambient sensors (DHT11/DHT22) over USB serial (`115200` baud) on demand.
* **🌐 Live Web Aggregation:** Connects to DuckDuckGo and weather endpoints when real-time external information is needed, with a one-click **NET** killswitch for 100% offline use.
* **🛡️ Defensive Fallbacks:** Continues operating cleanly even if the microcontroller is unplugged or the internet disconnects.

---

## 💻 Minimum System Requirements

AERY is designed to run on everyday budget laptops rather than high-end workstations:

| Component | Minimum Specification |
| :--- | :--- |
| **CPU** | Any dual-core processor (Intel Core i3 or equivalent, ≥ 2.0 GHz base clock) |
| **RAM** | 4 GB system memory |
| **Storage** | ~4 GB free disk space (for local model weights) |
| **Microcontroller** | Arduino Uno, Nano, ESP32, or compatible serial board *(optional)* |
| **Sensor** | DHT11 or DHT22 temperature & humidity module *(optional)* |

---

## 🧠 Why Qwen 2.5 (3B)?

* **Date Awareness & Strict Formatting:** Reliably tracks dynamic dates and strictly obeys JSON output schemas without breaking the ReAct execution loop.
* **The Sweet Spot for Edge AI:** At 3 billion parameters, it consumes only **~2 GB of memory** while retaining the reasoning capability required for accurate tool selection.

---

## 🏗️ System Architecture

```text
                       ┌─────────────────────────┐
                       │       Web Browser          │
                       │  (Tailwind CSS / HTML)     │
                       └────────────┬────────────┘
                                    │ HTTP POST (JSON)
                                    ▼
                       ┌─────────────────────────┐
                       │      Flask Server       │
                       │        (arey.py)        │
                       └────────────┬────────────┘
                                    │ Internal Dispatch
                                    ▼
                       ┌─────────────────────────┐
                       │       AERY Agent        │
                       │       (agent.py)        │
                       └─────┬─────────────┬─────┘
           Structured Schema │             │ Observation Loop
                             ▼             ▼
          ┌────────────────────┐         ┌────────────────────────────┐
          │    Local Ollama    │         │   Tools & Telemetry Node   │
          │   (qwen2.5:3b)     │         │  ├─ Arduino Serial Driver  │
          └────────────────────┘         │  ├─ DuckDuckGo Web Search  │
                                         │  └─ Safe Math Evaluator    │
                                         └─────────────┬──────────────┘
                                                       │ USB Serial (115200 baud)
                                                       ▼
                                         ┌────────────────────────────┐
                                         │   Arduino + DHT11 Sensor   │
                                         └────────────────────────────┘
```

### Execution Flow
1. **Prompt Intake:** The user submits a query through the minimal web interface.
2. **Reasoning Step:** The agent evaluates the request and outputs a strict JSON decision determining whether a tool is required.
3. **Tool Dispatch:**
   * **Indoor climate queries** trigger a serial request to the Arduino.
   * **External news or global weather queries** trigger a live web search.
   * **Calculations** run through a sandboxed math evaluator.
4. **Synthesis:** Sensor data or search results are fed back into the agent and summarized into a concise 1–2 sentence response.

---

## 🔌 Arduino Hardware Setup

### 1. Wiring Pinout
Connect your DHT11 or DHT22 sensor to the microcontroller:

| DHT Sensor Pin | Arduino Pin | Notes |
| :--- | :--- | :--- |
| **VCC (+)** | `5V` or `3.3V` | Power supply |
| **DATA (Out)** | Digital Pin `D2` | Telemetry data line |
| **GND (-)** | `GND` | Common ground |

> **Note:** If using a bare 4-pin DHT sensor without a breakout board, place a `10kΩ` pull-up resistor between **VCC** and **DATA**.

### 2. Serial Communication Protocol
The Python backend communicates with the microcontroller over USB Serial at **`115200` baud**:

| Event | Direction | Payload |
| :--- | :--- | :--- |
| **Request Reading** | Host ➔ Arduino | `GET_SENSORS\n` |
| **Valid Telemetry** | Arduino ➔ Host | `{"temperature": 26.5, "humidity": 60}` |
| **Read Timeout / Fault** | Arduino ➔ Host | `SENSOR_ERROR` |

---

## 🚀 Quick Setup

### 1. Install Ollama & Pull the Default Model
Download and install [Ollama](https://ollama.ai), ensure it is added to your system PATH, and pull the model:
```bash
ollama pull qwen2.5:3b
```

### 2. Clone the Repository & Install Dependencies
```bash
git clone [https://github.com/crimsonOmoon/arey_agent.git](https://github.com/crimsonOmoon/arey_agent.git)
cd arey_agent
pip install -r requirements.txt
```

### 3. Flash the Microcontroller
1. Open the Arduino IDE and install the **DHT sensor library** by Adafruit.
2. Open the `.ino` sketch inside the `firmware/` folder and upload it to your board.
3. Check which port your Arduino is using (e.g., `COM5` on Windows or `/dev/ttyUSB0` on Linux) and ensure `ARDUINO_PORT` in `agent.py` matches.

### 4. Launch AERY
```bash
python arey.py
```
Open **`http://localhost:5000`** in any browser.

---

## 🔄 Switching AI Models

AERY supports any tool-capable model available on Ollama. To swap models:

1. **Download the desired model in your terminal:**
   ```bash
   ollama pull llama3.2:3b
   # Or try lighter/heavier models:
   # ollama pull llama3.2:1b
   # ollama pull phi3.5:3.8b
   ```

2. **Update `MODEL` in `agent.py`:**
   ```python
   MODEL = "llama3.2:3b"
   ```

3. **Restart the server:**
   Run `python arey.py` to load the new model weights.

---

## 📂 Repository Structure

```text
arey_agent/
├── firmware/
│   └── aery_sensor.ino    # Microcontroller C++ firmware for DHT11 telemetry
├── arey.py                # Flask web server and Tailwind CSS frontend UI
├── agent.py               # ReAct agent loop, serial driver, and tool orchestration
├── requirements.txt       # Python package dependencies
├── .gitignore             # Git exclusion rules
├── LICENSE                # MIT License
└── README.md              # Project documentation
```

---

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for full details.
