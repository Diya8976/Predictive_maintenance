# Predictive_maintenance
# 📡 Real-Time Predictive Maintenance Dashboard

A powerful real-time predictive maintenance dashboard using **Flask**, **Plotly**, **Isolation Forest**, and **live sensor data from MySQL**. This system monitors sensor values, detects anomalies, visualizes thresholds, and sends email alerts — making it perfect for predictive maintenance applications.

---

## 🚀 Features

- 📈 **Live Sensor Plot** with anomaly detection (Isolation Forest)
- 🧠 **Smart Failure Detection** using ML + rules
- 📊 **Threshold Visualization** (Upper/Lower Limits)
- 📬 **HTML Email Alerts** for anomalies
- ⚡ **Interactive Dashboard** built with Flask + Bootstrap
- 📡 Connects to live MySQL sensor data feed

---

## 📂 Project Structure

├── app.py # Flask app with live routes ├── dashboard.html # Bootstrap-based dashboard UI ├── failure_calculation.py # Core failure detection logic ├── visualization.py # Plot generation & anomaly graph ├── email.py # Email alert system (HTML/Plain) ├── config.py # Database config ├── isolation_forest_model.pkl # Trained ML model ├── combo_scaler.pkl # Scaler for feature normalization └── requirements.txt # Python dependencies

---
