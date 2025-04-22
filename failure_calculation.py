import pandas as pd
import pymysql
import numpy as np
import time
from email_alert import send_email_alert
from config import DB_CONFIG

def detect_and_alert_failures():
    try:
        print("🔄 Pulling data for failure detection...")
        conn = pymysql.connect(**DB_CONFIG)
        query = """
        SELECT sensorid, timestamp, Value, rolling_mean, slope, upper_limit, lower_limit 
        FROM current_sensor1 
        ORDER BY sensorid, timestamp
        """
        df = pd.read_sql(query, conn)
        conn.close()

        df['Value'] = pd.to_numeric(df['Value'], errors='coerce')
        df = df.dropna(subset=['Value'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Detect failure 
        def detect_failure(row):
            value = row['Value']
            upper = row['upper_limit']
            lower = row['lower_limit']
            if pd.notna(upper) and value > upper:
                return 'Failure_Upper_Breach'
            elif pd.notna(lower) and value < lower:
                return 'Failure_Lower_Breach'
            else:
                return None

        df['failure_type'] = df.apply(detect_failure, axis=1)

        failures = df[df['failure_type'].notnull()]
        print(f"📊 Total Data Points: {len(df)}")
        print(f"🔥 Total Failures Detected: {len(failures)}")

        if failures.empty:
            return {
                "status": "success",
                "total_failures": len(df),
                "failure_summary": df.to_dict(orient='records'),
                "failures_df": df.to_dict(orient='records')
            }

        # Group summary
        summary = (
            failures
            .groupby(['sensorid', 'failure_type'])
            .agg(
                total_failures=('failure_type', 'count'),
                first_failure=('timestamp', 'min'),
                last_failure=('timestamp', 'max'),
            )
            .reset_index()
        )

        # HTML Table for Email
        table_html = summary.to_html(index=False, border=1, justify="center")

        email_body = f"""
        <h2>🚨 Predictive Maintenance Alert!</h2>
        <p>The following sensor failures were detected:</p>
        {table_html}
        <p>Please inspect the equipment immediately.</p>
        """
        send_email_alert("⚠️ Sensor Failure Alert", email_body)

        return {
            "status": "success",
            "total_failures": len(failures),
            "failure_summary": summary.to_dict(orient='records'),
            "failures_df": df 
        }

    except Exception as e:
        print(f"❌ Error in failure detection: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == '__main__':
    detect_and_alert_failures()