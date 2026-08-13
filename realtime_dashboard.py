import csv
import json
import threading
from collections import deque
from datetime import datetime

import paho.mqtt.client as mqtt
import plotly.graph_objs as go
from dash import Dash, dcc, html, Input, Output

# ---------------- configuration ----------------
BROKER = "localhost"
PORT = 1883
TOPIC = "esp32/GROUP30/data"
HISTORY = 30          # number of recent points kept per graph
UPDATE_MS = 5000      # graph refresh interval, milliseconds
SMOOTH_WINDOW = 5     # moving-average window (set to 1 to turn smoothing off)
LOG_FILE = "sensor_log.csv"

# one colour per metric, reused for the graph line and its heading
COLORS = {
    "temperature": "#E4572E",
    "humidity":    "#2E86DE",
    "light":       "#F2A104",
    "distance":    "#17A398",
}

# ---------------- shared data (written by MQTT thread, read by Dash) ----------------
lock = threading.Lock()
timestamps = deque(maxlen=HISTORY)
series = {key: deque(maxlen=HISTORY) for key in COLORS}
last_update = {"time": "waiting for data..."}

# start a fresh CSV log with a header row
with open(LOG_FILE, "w", newline="") as f:
    csv.writer(f).writerow(["timestamp", "temperature", "humidity", "light", "distance"])

# ---------------- MQTT ----------------
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT Broker with code:", rc)
    client.subscribe(TOPIC)

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
    except json.JSONDecodeError:
        print("Invalid JSON received")
        return

    now = datetime.now()
    with lock:
        timestamps.append(now.strftime("%H:%M:%S"))
        for key in series:
            series[key].append(data.get(key))
        last_update["time"] = now.strftime("%H:%M:%S")

    # append this reading to the timestamp log
    with open(LOG_FILE, "a", newline="") as f:
        csv.writer(f).writerow([
            now.strftime("%Y-%m-%d %H:%M:%S"),
            data.get("temperature"), data.get("humidity"),
            data.get("light"), data.get("distance"),
        ])

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)  # paho-mqtt 2.x compatibility
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT, 60)
client.loop_start()

# ---------------- helpers ----------------
def moving_average(values, window):
    """Trailing moving average; returns a list the same length as values."""
    out = []
    for i in range(len(values)):
        lo = max(0, i - window + 1)
        chunk = values[lo:i + 1]
        out.append(sum(chunk) / len(chunk))
    return out

def make_figure(key, title, y_label):
    with lock:
        x_all = list(timestamps)
        y_all = list(series[key])

    # keep only points where this sensor actually reported a value
    x = [t for t, v in zip(x_all, y_all) if v is not None]
    y = [v for v in y_all if v is not None]

    traces = [go.Scatter(
        x=x, y=y, mode="lines+markers", name="reading",
        line=dict(color=COLORS[key], width=2),
    )]

    if SMOOTH_WINDOW > 1 and len(y) >= SMOOTH_WINDOW:
        traces.append(go.Scatter(
            x=x, y=moving_average(y, SMOOTH_WINDOW), mode="lines",
            name=f"{SMOOTH_WINDOW}-point average",
            line=dict(color=COLORS[key], width=1, dash="dot"),
        ))

    return {
        "data": traces,
        "layout": go.Layout(
            title=dict(text=title, font=dict(color=COLORS[key])),
            xaxis=dict(title="time"),
            yaxis=dict(title=y_label),
            margin=dict(l=50, r=20, t=45, b=40),
            template="plotly_white",
            height=320,
            legend=dict(orientation="h", y=-0.25),
        ),
    }

# ---------------- Dash app ----------------
app = Dash(__name__)
app.title = "GROUP30 Sensor Dashboard"

CARD = {
    "flex": "1 1 45%", "minWidth": "320px", "margin": "10px", "padding": "6px",
    "border": "1px solid #E2E2E2", "borderRadius": "8px", "background": "white",
}

app.layout = html.Div(
    style={"fontFamily": "Segoe UI, Arial, sans-serif", "background": "#F4F6F8",
           "minHeight": "100vh", "padding": "16px"},
    children=[
        html.Div(style={"textAlign": "center", "marginBottom": "8px"}, children=[
            html.H1("EE 288  -  Real-Time Sensor Dashboard",
                    style={"color": "#1F3A34", "marginBottom": "2px"}),
            html.P("Group 30   -   live data from esp32/GROUP30/data",
                   style={"color": "#555", "marginTop": "0"}),
            html.P(id="last-update",
                   style={"color": "#2E5A52", "fontWeight": "bold", "marginTop": "2px"}),
        ]),
        html.Div(
            style={"display": "flex", "flexWrap": "wrap", "justifyContent": "center"},
            children=[
                html.Div(dcc.Graph(id="temp-graph"), style=CARD),
                html.Div(dcc.Graph(id="hum-graph"), style=CARD),
                html.Div(dcc.Graph(id="light-graph"), style=CARD),
                html.Div(dcc.Graph(id="dist-graph"), style=CARD),
            ],
        ),
        dcc.Interval(id="tick", interval=UPDATE_MS, n_intervals=0),
    ],
)

@app.callback(
    [Output("temp-graph", "figure"), Output("hum-graph", "figure"),
     Output("light-graph", "figure"), Output("dist-graph", "figure"),
     Output("last-update", "children")],
    [Input("tick", "n_intervals")],
)
def refresh(_):
    temp = make_figure("temperature", "Temperature", "\u00b0C")
    hum = make_figure("humidity", "Humidity", "%")
    light = make_figure("light", "Light (LDR)", "raw ADC (0-4095)")
    dist = make_figure("distance", "Distance", "cm")
    return temp, hum, light, dist, f"Last reading at {last_update['time']}"

if __name__ == "__main__":
    # use_reloader=False keeps debug pages but avoids a second MQTT connection
    app.run(debug=True, use_reloader=False, port=8050)
