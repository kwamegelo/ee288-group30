# EE 288 — Group 30: Real-Time IoT Sensor Monitoring
A real-time system that streams four sensor readings from an ESP32 to a live
web dashboard, built for the EE 288 (Electrical Measurement and Instrumentation)
laboratory at KNUST.
## Architecture
ESP32 (sensors) → MQTT broker (Mosquitto) → Python subscriber (paho-mqtt) → Plotly/Dash dashboard
The ESP32 reads a DHT11 (temperature, humidity), an LDR (light) and an HC-SR04
(distance), packs them into one JSON message, and publishes to the topic
`esp32/GROUP30/data` every 5 seconds. A local Mosquitto broker routes the
messages; a Python program subscribes and either serves the latest reading
(Flask) or plots all four sensors live (Dash).
## Files
- `lab2_mqtt_publish.ino` — ESP32 sketch: publishes temperature and humidity (Lab 2).
- `lab3_json_publish.ino` — ESP32 sketch: all four sensors as one JSON message (Lab 3).
- `mqtt_server.py` — Flask + paho-mqtt subscriber; serves the latest reading as JSON (Lab 4).
- `realtime_dashboard.py` — Dash + Plotly dashboard: four live graphs, a CSV log and smoothing (Labs 5–6).
## Running it
1. Start the Mosquitto broker (`localhost:1883`).
2. Flash an ESP32 sketch (set your Wi-Fi SSID/password and the PC's LAN IPv4 in the sketch).
3. Install the Python side: `pip install flask dash plotly paho-mqtt`.
4. Run `python mqtt_server.py` (browser at `localhost:5000`) or `python realtime_dashboard.py` (browser at `127.0.0.1:8050`).
## Team
Group 30 — Department of Computer Engineering, KNUST.
