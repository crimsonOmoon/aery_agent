# AERY

A lightweight local AI assistant that connects directly to physical hardware sensors (Arduino) and searches the web when needed. 

Designed to run completely offline on everyday, low-end laptops without requiring expensive GPUs, cloud infrastructure, or paid API keys.

---

### Minimum System Requirements
Runs smoothly on entry-level hardware:
- **CPU:** Any dual-core processor (Intel Core i3 or equivalent, 2.0 GHz base clock)
- **RAM:** 4 GB
- **Storage:** ~4 GB free disk space (to store the model weights)

---

### Why Qwen 2.5 (3B)?
- **Date Awareness & Strict Formatting:** Handles temporal context (like dynamic dates) reliably and strictly outputs JSON schemas without breaking the execution loop.
- **Balanced Performance:** At 3 billion parameters, it occupies only ~2 GB of memory while retaining the reasoning power needed for accurate tool calling.

---

## System Architecture

             [ Web Browser ]
          (Tailwind CSS / HTML)
                    │
                    ▼
             [ Flask Server ]
                (aery.py)
                    │
                    ▼
             [ AERY Agent ]
               (agent.py)
             ┌──────┴──────┐
             ▼             ▼
   [ Local Ollama ]   [ Tools & Telemetry ]
    (qwen2.5:3b)       ├── Arduino (DHT11 temp/humidity)
                       ├── DuckDuckGo (Live web search)
                       └── Calculator (Math evaluator)

1. The user enters a prompt through the minimal web interface.
2. The agent interprets the query and determines whether external tools or sensors are required.
3. For indoor climate inquiries, it queries the Arduino over serial. For external news or weather, it runs a live search.
4. The observations are synthesized into a direct, concise response.


## Hardware Telemetry Protocol

Communication between the host machine and microcontroller runs over USB serial at `115200` baud:

- Host requests: `GET_SENSORS\n`
- Microcontroller responds: `{"temperature": 26, "humidity": 60}`
- Error handling: Returns `SENSOR_ERROR` on read failures so the host application stays stable.


## Quick Setup

1. Install Ollama & Pull Model
Ensure [Ollama](https://ollama.ai) is installed and available in the system PATH:

ollama pull qwen2.5:3b

2. Install Dependencies

git clone [https://github.com/YOUR_USERNAME/aery.git](https://github.com/YOUR_USERNAME/aery.git)
cd aery
pip install -r requirements.txt

3. Flash Microcontroller
Connect the DHT11 sensor data pin to digital pin D2 on the Arduino board, then upload the sketch located in firmware/ using the Arduino IDE.

4. Run Application

python aery.py

5.Open http://localhost:5000 in any web browser.



Switching AI Models
AERY can run any model supported by Ollama. To switch models:

1.Pull the desired model via terminal:

ollama pull llama3.2:3b
# or any other model, e.g., phi3.5:3.8b, llama3.2:1b

2.Update the model name in agent.py:
Locate the configuration variable near the top of agent.py and set it to the newly downloaded model tag:

MODEL = "llama3.2:3b"