"""
EE 288 Laboratory Report 1, Lab Session 4
Flask + paho-mqtt subscriber.

Subscribes to the ESP32's JSON data topic on the local Mosquitto broker,
stores the most recent reading, and serves it at http://localhost:5000.

Before running:
  - Replace 12345678 in the subscribe topic with your student ID.
  - Make sure Mosquitto is running locally on port 1883.

Install dependencies:
  pip install flask paho-mqtt

Run:
  python mqtt_server.py
"""

from flask import Flask, render_template, request
import paho.mqtt.client as mqtt
import json

app = Flask(__name__)

sensor_data = {}

def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT Broker with code: " + str(rc))
    client.subscribe("esp32/GROUP30/data")  # Replace with your student ID

def on_message(client, userdata, msg):
    global sensor_data
    payload = msg.payload.decode()
    print(f"Message received: {payload}")
    try:
        sensor_data = json.loads(payload)
    except json.JSONDecodeError:
        print("Invalid JSON received")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
client.on_connect = on_connect
client.on_message = on_message

client.connect("localhost", 1883, 60)
client.loop_start()

@app.route('/')
def index():
    return sensor_data  # Can be enhanced to display HTML later

if __name__ == '__main__':
    app.run(debug=True, port=5000)
