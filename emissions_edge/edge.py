import pandas as pd
import numpy as np
import sqlite3
import json
from ingest import receive_data  # Keep for real-data option
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend to avoid threading issues
import matplotlib.pyplot as plt
from flask import Flask, render_template, jsonify
import paho.mqtt.client as mqtt
import threading
from collections import deque
import time

# GWP factors
GWP = {"CO2": 1, "CH4": 25, "N2O": 298}

# Local database (optional historical data)
conn = sqlite3.connect("emissions.db")
try:
    pd.read_csv("historical_ghgp.csv").to_sql("historical", conn, if_exists="replace")
except FileNotFoundError:
    print("Warning: historical_ghgp.csv not found, skipping historical data.")

# Flask app setup
app = Flask(__name__)

# MQTT client with updated callback API version
mqtt_client = mqtt.Client(client_id="", userdata=None, protocol=mqtt.MQTTv311, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
latest_recommendation = "No recommendations yet"
history = deque(maxlen=5)  # Store last 5 readings

# Simulated sensor data with Tier 1, 2, 3 sources (in kg)
SIMULATED_DATA = [
    {"Tier1": {"CO2": 390.0, "CH4": 1.5, "N2O": 0.28}, "Tier2": {"CO2": 50.0}, "Tier3": {"CO2": 20.0}},  # CO2e: 510.94 + 50 + 20
    {"Tier1": {"CO2": 800.0, "CH4": 5.0, "N2O": 0.70}, "Tier2": {"CO2": 80.0}, "Tier3": {"CO2": 30.0}},  # CO2e: 1133.6 + 80 + 30
    {"Tier1": {"CO2": 600.0, "CH4": 3.0, "N2O": 0.50}, "Tier2": {"CO2": 60.0}, "Tier3": {"CO2": 25.0}},  # CO2e: 824.0 + 60 + 25
    {"Tier1": {"CO2": 420.0, "CH4": 2.0, "N2O": 0.35}, "Tier2": {"CO2": 55.0}, "Tier3": {"CO2": 22.0}},  # CO2e: 574.3 + 55 + 22
    {"Tier1": {"CO2": 405.2, "CH4": 1.7, "N2O": 0.30}, "Tier2": {"CO2": 52.0}, "Tier3": {"CO2": 21.0}},  # CO2e: 537.1 + 52 + 21
    {"Tier1": {"CO2": 410.5, "CH4": 1.8, "N2O": 0.32}, "Tier2": {"CO2": 53.0}, "Tier3": {"CO2": 23.0}}   # CO2e: 550.86 + 53 + 23
]

def on_cloud_message(client, userdata, msg):
    """Callback for receiving cloud recommendations."""
    global latest_recommendation
    latest_recommendation = msg.payload.decode()
    print(f"Cloud recommendation: {latest_recommendation}")

def setup_mqtt():
    """Initialize and start MQTT client."""
    mqtt_client.on_message = on_cloud_message
    mqtt_client.connect("broker.hivemq.com", 1883)
    mqtt_client.subscribe("emissions/recommend")
    mqtt_client.loop_start()

def parse_and_filter(data):
    """Parse and filter incoming sensor data."""
    if all(k in data["Tier1"] for k in ["CO2", "CH4", "N2O"]):
        if data["Tier1"]["CO2"] > 5000:  # Example anomaly
            return None, "CO2 spike"
        return data, None
    return None, "Incomplete data"

def calculate_carbon(data):
    """Calculate CO2-equivalent emissions across tiers."""
    tier1_co2e = sum(data["Tier1"][gas] * GWP[gas] for gas in data["Tier1"])
    tier2_co2e = data["Tier2"].get("CO2", 0) * GWP["CO2"]
    tier3_co2e = data["Tier3"].get("CO2", 0) * GWP["CO2"]
    total_co2e = tier1_co2e + tier2_co2e + tier3_co2e
    return total_co2e

def aggregate_with_history(data):
    """Compare current data with historical averages (if available)."""
    try:
        df = pd.read_sql("SELECT * FROM historical", conn)
        avg = df[["CO2", "CH4", "N2O"]].mean().to_dict()
        deviation = {k: data["Tier1"][k] - avg[k] for k in data["Tier1"]}
    except:
        deviation = data["Tier1"]  # Fallback if no historical data
    return deviation

def visualize(data, co2e):
    """Generate multiple plots for emissions data."""
    # Combined bar chart (default)
    plt.figure(figsize=(8, 4))
    tier1_data = data["Tier1"]
    plt.bar(tier1_data.keys(), tier1_data.values(), color=['#4CAF50', '#FF9800', '#F44336'])
    plt.axhline(y=1000, color='r', linestyle='--', label='Threshold (1000 kg)')
    plt.title(f"Current Tier 1 Emissions (CO2e: {co2e:.2f} kg)")
    plt.ylabel("kg")
    plt.legend()
    plt.savefig("static/emissions.png", bbox_inches='tight')
    plt.close()

    # Historical line plots
    times = [entry["time"] for entry in history]
    co2_vals = [entry["data"]["Tier1"]["CO2"] + entry["data"]["Tier2"]["CO2"] + entry["data"]["Tier3"]["CO2"] for entry in history]
    ch4_vals = [entry["data"]["Tier1"]["CH4"] for entry in history]
    n2o_vals = [entry["data"]["Tier1"]["N2O"] for entry in history]
    co2e_vals = [entry["co2e"] for entry in history]

    # CO2 plot
    plt.figure(figsize=(8, 4))
    plt.plot(times, co2_vals, marker='o', color='#4CAF50', label='CO2 (All Tiers)')
    plt.title("CO2 Trend (Tier 1+2+3)")
    plt.ylabel("kg")
    plt.xticks(rotation=45)
    plt.legend()
    plt.savefig("static/co2.png", bbox_inches='tight')
    plt.close()

    # CH4 plot
    plt.figure(figsize=(8, 4))
    plt.plot(times, ch4_vals, marker='o', color='#FF9800', label='CH4 (Tier 1)')
    plt.title("CH4 Trend (Tier 1)")
    plt.ylabel("kg")
    plt.xticks(rotation=45)
    plt.legend()
    plt.savefig("static/ch4.png", bbox_inches='tight')
    plt.close()

    # N2O plot
    plt.figure(figsize=(8, 4))
    plt.plot(times, n2o_vals, marker='o', color='#F44336', label='N2O (Tier 1)')
    plt.title("N2O Trend (Tier 1)")
    plt.ylabel("kg")
    plt.xticks(rotation=45)
    plt.legend()
    plt.savefig("static/n2o.png", bbox_inches='tight')
    plt.close()

    # CO2e plot
    plt.figure(figsize=(8, 4))
    plt.plot(times, co2e_vals, marker='o', color='#0288d1', label='CO2e (All Tiers)')
    plt.axhline(y=1000, color='r', linestyle='--', label='Threshold (1000 kg)')
    plt.title("CO2e Trend (Tier 1+2+3)")
    plt.ylabel("kg")
    plt.xticks(rotation=45)
    plt.legend()
    plt.savefig("static/co2e.png", bbox_inches='tight')
    plt.close()

@app.route('/')
def dashboard():
    """Serve the emissions dashboard."""
    return render_template("dashboard.html")

@app.route('/data')
def get_data():
    """Return current and historical data as JSON."""
    current = history[-1] if history else {"data": {"Tier1": {"CO2": 0, "CH4": 0, "N2O": 0}, "Tier2": {"CO2": 0}, "Tier3": {"CO2": 0}}, "co2e": 0, "time": "N/A", "alert": False}
    return jsonify({
        "current": current,
        "history": list(history),
        "recommendation": latest_recommendation
    })

def send_to_cloud(data, co2e):
    """Send processed data to the cloud via MQTT."""
    payload = {"time": pd.Timestamp.now().isoformat(), "CO2e": co2e, "raw": data}
    mqtt_client.publish("emissions/data", json.dumps(payload))

# Original real-data processing (commented out)
"""
def process_sensor_data():
    #Main loop to process sensor data.
    while True:
        raw_data = receive_data()
        data, flag = parse_and_filter(raw_data)
        if data:
            co2e = calculate_carbon(data)
            deviation = aggregate_with_history(data)
            visualize(data, co2e)
            history.append({"data": data, "co2e": co2e, "time": pd.Timestamp.now().isoformat(), "alert": co2e > 1000})
            send_to_cloud(data, co2e)
            if co2e > 1000:
                print("Alert: CO2e exceeds 1 ton!")
        elif flag:
            print(f"Data issue: {flag}")
"""

# Simulated sensor data processing
def process_sensor_data():
    """Main loop to process simulated sensor data."""
    data_index = 0
    while True:
        raw_data = SIMULATED_DATA[data_index % len(SIMULATED_DATA)]
        data, flag = parse_and_filter(raw_data)
        if data:
            co2e = calculate_carbon(data)
            deviation = aggregate_with_history(data)
            visualize(data, co2e)
            history.append({"data": data, "co2e": co2e, "time": pd.Timestamp.now().isoformat(), "alert": co2e > 1000})
            send_to_cloud(data, co2e)
            if co2e > 1000:
                print("Alert: CO2e exceeds 1 ton!")
        elif flag:
            print(f"Data issue: {flag}")
        
        data_index += 1
        time.sleep(5)  # Simulate real-time data every 5 seconds

if __name__ == "__main__":
    setup_mqtt()
    sensor_thread = threading.Thread(target=process_sensor_data, daemon=True)
    sensor_thread.start()
    app.run(host="0.0.0.0", port=5001)