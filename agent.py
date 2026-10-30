import json
import os
import shutil
import subprocess
import time
import requests
import serial

try:
    from duckduckgo_search import DDGS
except ImportError:
    try:
        from ddgs import DDGS
    except ImportError:
        DDGS = None

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_URL = f"{OLLAMA_BASE_URL}/api/chat"
MODEL = "qwen2.5:3b"

ARDUINO_PORT = "COM5"
ARDUINO_BAUD = 115200

OLLAMA_TIMEOUT = 60
MAX_STEPS = 4
KEEP_ALIVE = "10m"

ENABLE_INTERNET = True
http = requests.Session()


def is_ollama_running():
    try:
        res = requests.get(OLLAMA_BASE_URL, timeout=1)
        return res.status_code == 200
    except requests.exceptions.RequestException:
        return False


def ensure_ollama_running():
    if is_ollama_running():
        return

    binary = shutil.which("ollama")
    if not binary:
        print("[!] ollama binary not found in PATH")
        return

    print("[*] Starting local Ollama...")
    try:
        subprocess.Popen(
            [binary, "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )

        for _ in range(20):
            time.sleep(0.5)
            if is_ollama_running():
                print("[*] Ollama is live.")
                return

        print("[!] Timed out waiting for Ollama to start.")
    except Exception as e:
        print(f"[!] Failed to launch Ollama: {e}")


ensure_ollama_running()


# Hardware link
arduino = None
try:
    arduino = serial.Serial(ARDUINO_PORT, ARDUINO_BAUD, timeout=2)
    time.sleep(2)
    arduino.reset_input_buffer()
    print(f"[*] Attached to Arduino on {ARDUINO_PORT}")
except Exception as e:
    print(f"[!] Serial connection skipped: {e}")
    arduino = None


# Tool functions & toggles
def set_internet_toggle(state):
    global ENABLE_INTERNET
    ENABLE_INTERNET = state
    print(f"[*] Internet access set to {ENABLE_INTERNET}")


def room_sensor():
    if arduino is None:
        return {"error": "Room sensor (Arduino) is offline or not connected."}
    try:
        arduino.reset_input_buffer()
        arduino.write(b"GET_SENSORS\n")
        response = arduino.readline().decode("utf-8", errors="ignore").strip()
        if not response:
            return {"error": "Arduino did not respond."}
        if response == "SENSOR_ERROR":
            return {"error": "DHT sensor read error."}
        data = json.loads(response)
        return {"temperature": f"{data.get('temperature')}°C", "humidity": f"{data.get('humidity')}%"}
    except Exception as e:
        return {"error": f"Sensor communication failed: {str(e)}"}


def internet_search(query):
    global ENABLE_INTERNET
    if not ENABLE_INTERNET:
        return {"error": "Internet access is disabled by user switch."}

    try:
        query_lower = query.lower()
        if any(w in query_lower for w in ["temperature", "weather", "temp"]):
            city = query_lower.replace("temperature", "").replace("weather", "").replace("in", "").replace("of", "").replace("current", "").replace("today", "").strip()
            if city:
                try:
                    res = http.get(f"https://wttr.in/{city}?format=%C+%t+Humidity:+%h", timeout=4)
                    if res.status_code == 200 and "Unknown location" not in res.text:
                        return {"results": f"Weather in {city}: {res.text.strip()}"}
                except Exception:
                    pass

        if DDGS is None:
            return {"error": "duckduckgo_search library not installed."}

        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=2):
                results.append(f"{r.get('title')}: {r.get('body')[:180]}")
        return {"results": results if results else "No direct results found."}
    except Exception as e:
        return {"error": f"Search failed: {str(e)}"}


def safe_calculate(expression):
    try:
        allowed_chars = set("0123456789+-*/(). %")
        if not all(c in allowed_chars for c in expression):
            return "Invalid characters in mathematical expression."
        return str(eval(expression, {"__builtins__": None}, {}))
    except Exception as e:
        return f"Calculation error: {e}"


def execute_single_tool(name, args):
    if name == "room_sensor":
        return room_sensor()
    if name == "calculator":
        return safe_calculate(args.get("expression", ""))
    if name == "internet_search":
        return internet_search(args.get("query", ""))
    return {"error": "Unknown tool"}


# ReAct schema definition
REACT_SCHEMA = {
    "type": "object",
    "properties": {
        "thought": {"type": "string"},
        "action": {"type": "string", "enum": ["use_tool", "answer"]},
        "tool_name": {"type": "string", "enum": ["room_sensor", "calculator", "internet_search", "none"]},
        "tool_arguments": {
            "type": "object",
            "properties": {
                "expression": {"type": "string"},
                "query": {"type": "string"}
            },
            "additionalProperties": False
        },
        "final_answer": {"type": "string"}
    },
    "required": ["thought", "action", "tool_name", "tool_arguments", "final_answer"],
    "additionalProperties": False
}

SYSTEM_PROMPT = """Your name is AERY. You are an efficient, concise, and helpful AI assistant equipped with real-world sensor integration and live search tools.

AVAILABLE TOOLS:
- room_sensor: Reads local physical telemetry (temperature, humidity) from the attached hardware microcontroller.
- internet_search: Searches current web info, public weather, and real-time facts.
- calculator: Performs precise arithmetic expressions.

OPERATING GUIDELINES:
1. BREVITY: Keep final_answer concise, direct, and helpful (1-3 sentences).
2. HARDWARE DISTINCTION: Use 'room_sensor' strictly for indoor/local room ambient queries. For outside cities or global locations, use 'internet_search'.
3. REASONING: Place internal planning inside 'thought'. If you need information, choose 'use_tool'. Once the observation is received, synthesize the result and switch action to 'answer'.
4. RESILIENCE: If an external tool or internet access reports an error, explain the situation calmly and answer to the best of your general knowledge.
"""

chat_history = [{"role": "system", "content": SYSTEM_PROMPT}]


def ollama_chat(messages):
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "keep_alive": KEEP_ALIVE,
        "format": REACT_SCHEMA,
        "options": {"temperature": 0.2, "num_predict": 250}
    }
    try:
        response = http.post(OLLAMA_URL, json=payload, timeout=OLLAMA_TIMEOUT)
        response.raise_for_status()
        return response.json()["message"]
    except requests.exceptions.ConnectionError:
        return {"content": json.dumps({
            "thought": "Ollama service unavailable.",
            "action": "answer",
            "tool_name": "none",
            "tool_arguments": {},
            "final_answer": "Error: Ollama is not running. Please start Ollama via terminal ('ollama serve')."
        })}
    except Exception as e:
        return {"content": json.dumps({
            "thought": "Execution error.",
            "action": "answer",
            "tool_name": "none",
            "tool_arguments": {},
            "final_answer": f"Backend communication error: {str(e)}"
        })}


def solve_request(conversation_context):
    loop_messages = list(conversation_context)

    for step in range(MAX_STEPS):
        message = ollama_chat(loop_messages)
        content_str = message.get("content", "")

        try:
            state = json.loads(content_str)
        except Exception:
            return "Error: Model returned an unparseable response structure."

        if state.get("action") == "answer":
            return state.get("final_answer", "")

        if state.get("action") == "use_tool":
            tool_name = state.get("tool_name")
            args = state.get("tool_arguments", {})
            tool_result = execute_single_tool(tool_name, args)

            loop_messages.append({"role": "assistant", "content": content_str})
            loop_messages.append({
                "role": "user",
                "content": f"OBSERVATION: {json.dumps(tool_result)}\nProvide your final answer now if sufficient."
            })

    return "I reached the maximum step limit before determining an answer."


def chat_with_aery(user_input):
    global chat_history
    chat_history.append({"role": "user", "content": user_input})
    final_answer = solve_request(chat_history)
    chat_history.append({"role": "assistant", "content": final_answer})

    if len(chat_history) > 7:
        chat_history = [chat_history[0]] + chat_history[-6:]

    return final_answer


chat_with_alicia = chat_with_aery
