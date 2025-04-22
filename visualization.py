import pandas as pd
import pymysql
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
from flask import Response, request
from config import DB_CONFIG

def plot_anomaly_graph():
    try:
        # Load models
        iso_model = joblib.load("isolation_forest_model.pkl")
        scaler = joblib.load("combo_scaler.pkl")

        selected_features = [
            "value", "rolling_mean", "slope", 
            "upper_limit", "lower_limit", "degradation_score"
        ]

        # Fetch full data
        conn = pymysql.connect(**DB_CONFIG)
        df = pd.read_sql("SELECT * FROM current_sensor1 ORDER BY timestamp", conn)
        conn.close()

        # Clean columns
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
        
        df.fillna(0, inplace=True)
        df = df.infer_objects(copy=False)

        # Parse types
        for col in selected_features:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df.dropna(subset=['timestamp'], inplace=True)

        # Handle hourly mode
        view_mode = request.args.get("mode", "raw")
        if view_mode == "hourly":
            df = df.set_index('timestamp').resample('1h').mean().dropna().reset_index()

        if df.empty:
            print("⚠️ No data available after filtering.")
            return Response("No data available to plot", status=200)

        # Anomaly Detection
        X_scaled = scaler.transform(df[selected_features])
        df["anomaly_label"] = (iso_model.predict(X_scaled) == -1).astype(int)

        # Failure Detection
        def detect_failure(row):
            if row['value'] > row['upper_limit']:
                return 'Upper'
            elif row['value'] < row['lower_limit']:
                return 'Lower'
            return None
        df['failure_type'] = df.apply(detect_failure, axis=1)

        # Plotting
        plt.switch_backend('Agg')
        plt.figure(figsize=(15, 6))

        sns.lineplot(x=df["timestamp"], y=df["value"], label="Sensor Value", linewidth=2)
        sns.lineplot(x=df["timestamp"], y=df["upper_limit"], label="Upper Limit", color="green", linestyle="--")
        sns.lineplot(x=df["timestamp"], y=df["lower_limit"], label="Lower Limit", color="orange", linestyle="--")

        # Anomalies
        anomaly_df = df[df["anomaly_label"] == 1]
        if not anomaly_df.empty:
            sns.scatterplot(x=anomaly_df["timestamp"], y=anomaly_df["value"],
                            color="red", label="Anomaly", s=70)

        # Failures
        upper_failures = df[df["failure_type"] == "Upper"]
        if not upper_failures.empty:
            sns.scatterplot(x=upper_failures["timestamp"], y=upper_failures["value"],
                            color="darkred", label="Failure (Upper)", marker="X", s=100)

        lower_failures = df[df["failure_type"] == "Lower"]
        if not lower_failures.empty:
            sns.scatterplot(x=lower_failures["timestamp"], y=lower_failures["value"],
                            color="blue", label="Failure (Lower)", marker="X", s=100)

        plt.title("Sensor Value with Anomalies & Failures (Live View)")
        plt.xlabel("Timestamp")
        plt.ylabel("Sensor Value (Amps)")
        plt.legend(loc="best")
        plt.grid(True)
        plt.tight_layout()

        # Save to image buffer
        img = BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plt.close()

        return Response(img.getvalue(), mimetype='image/png')

    except Exception as e:
        import traceback
        print(f"❌ Anomaly Graph Error: {e}")
        traceback.print_exc()
        return Response("Error generating anomaly graph", status=500)

if __name__ == '__main__':
    plot_anomaly_graph()
