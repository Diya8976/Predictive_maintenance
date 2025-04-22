import threading
import time
from flask import Flask, render_template, jsonify
import pandas as pd
import pymysql
import schedule
from config import DB_CONFIG
from degradation import update_data
from failure_calculation import detect_and_alert_failures
from visualization import plot_anomaly_graph

app = Flask(__name__)

# Fetch latest sensor value
def get_latest_sensor_data():
    try:
        connection = pymysql.connect(**DB_CONFIG)
        query = "SELECT current FROM current_sensor1 ORDER BY timestamp DESC LIMIT 1"
        df = pd.read_sql(query, con=connection)
        connection.close()
        return float(df['current'].iloc[0]) if not df.empty else "No data"
    except Exception as e:
        print(f"❌ Sensor Fetch Error: {e}")
        return "Error"

# Route to Home Dashboard
@app.route('/')
def dashboard():
    return render_template("dashboard.html")

# Route to Live Sensor Data API
@app.route('/live_sensor_data')
def sensor_data():
    return jsonify({"current": get_latest_sensor_data()})

# Route to Trigger Failures and Return Failure Summary (JSON)
@app.route('/detect_failures', methods=['POST'])
def trigger_failure_alerts():
    result = detect_and_alert_failures()

    failure_summary = result.get("failure_summary")
    failures_df = result.get("failures_df")

    # Convert DataFrames to JSON-safe format
    if isinstance(failure_summary, pd.DataFrame):
        failure_summary_json = failure_summary.to_dict(orient="records")
    else:
        failure_summary_json = failure_summary

    if isinstance(failures_df, pd.DataFrame):
        failures_df_json = failures_df.to_dict(orient="records")
    else:
        failures_df_json = failures_df

    if result.get("status") == "success" and result.get("total_failures", 0) > 0:
        return jsonify({
            "status": "alerts_sent",
            "alerts": failure_summary_json,
            "failures": failures_df_json
        })

    return jsonify({"status": "no_failures", "message": "No failures detected"})

# Route to Show Failures Table 
@app.route('/failures_table')
def failures_table():
    result = detect_and_alert_failures()
    if "failures_df" in result:
        df = result["failures_df"]
        df_html = df.to_html(classes='table table-bordered table-striped', index=False)
        return render_template("failures_table.html", table_html=df_html)
    return "<p>No failures detected</p>"

# Route to Anomaly and Failure Graph
@app.route('/anomaly_graph')
def sensor_graph():
    return plot_anomaly_graph()

# Function to handle failure data and convert it to JSON
def failure_to_json():
    result = detect_and_alert_failures()
    if "failures_df" in result:
        df = result["failures_df"]
        # Convert the DataFrame to JSON
        return jsonify(df.to_dict(orient="records"))
    return jsonify({"message": "No failure data available"})

# Background Scheduler for periodic tasks
def job():
    try:
        print("⏳ Hourly update: Updating degradation metrics...")
        update_data()
        print("✅ Degradation metrics updated by scheduler.")
    except Exception as e:
        print(f"❌ Scheduler Error: {e}")

def run_scheduler():
    schedule.every().hour.do(job)
    while True:
        schedule.run_pending()
        time.sleep(30)

def start_scheduler():
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print("🕒 Scheduler started (runs every hour in background)")

# Start Flask App
if __name__ == "__main__":
    start_scheduler()
    app.run(debug=True)
