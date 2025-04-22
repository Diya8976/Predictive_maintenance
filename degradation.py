import pandas as pd
import pymysql
import numpy as np
import time
from config import DB_CONFIG 

def update_data():
    try:
        # Connect to DB
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()

        def column_exists(table, column):
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE table_schema = '{DB_CONFIG["database"]}' 
                AND table_name = '{table}' 
                AND column_name = '{column}'
            """)
            return cursor.fetchone()[0] > 0


        columns_to_add = {
            "rolling_mean": "FLOAT",
            "slope": "FLOAT",
            "upper_limit": "FLOAT",
            "lower_limit": "FLOAT",
            "degradation_score": "FLOAT"
        }

        for col, col_type in columns_to_add.items():
            if not column_exists("current_sensor1", col):
                alter_sql = f"ALTER TABLE current_sensor1 ADD COLUMN {col} {col_type}"
                cursor.execute(alter_sql)
                print(f"✅ Column added: {col}")
            else:
                print(f"ℹ️ Column already exists: {col}")

        # Read and clean data
        query = "SELECT sensorid, timestamp, Value FROM current_sensor1 ORDER BY timestamp"
        df = pd.read_sql(query, conn)

        df['Value'] = pd.to_numeric(df['Value'], errors='coerce')
        df = df.dropna(subset=['Value'])

        # Calculate metrics
        df['rolling_mean'] = df['Value'].rolling(window=60, min_periods=1).mean()
        df['slope'] = df['Value'].diff()

        mean_val = df['Value'].mean()
        std_val = df['Value'].std()
        df['upper_limit'] = mean_val + 3 * std_val
        df['lower_limit'] = mean_val - 3 * std_val

        df = df.where(pd.notnull(df), None)

        # Prepare SQL Update
        update_sql = """
        UPDATE current_sensor1 
        SET 
            rolling_mean = %s, 
            slope = %s, 
            upper_limit = %s,
            lower_limit = %s,
            degradation_score = NULL
        WHERE sensorid = %s
        """

        batch_size = 100
        count = 0

        for index, row in df.iterrows():
            for attempt in range(3):
                try:
                    cursor.execute(update_sql, (
                        None if pd.isna(row['rolling_mean']) else float(row['rolling_mean']),
                        None if pd.isna(row['slope']) else float(row['slope']),
                        None if pd.isna(row['upper_limit']) else float(row['upper_limit']),
                        None if pd.isna(row['lower_limit']) else float(row['lower_limit']),
                        row['sensorid']
                    ))
                    break
                except pymysql.err.OperationalError as e:
                    if "Lock wait timeout" in str(e):
                        print(f"⏳ Row {index} locked. Retrying... (Attempt {attempt+1}/3)")
                        time.sleep(1)
                    elif "Undo Log" in str(e):
                        print("❌ Undo log full. Please extend tablespace.")
                        conn.rollback()
                        return
                    else:
                        print(f"❌ Unexpected error: {e}")
                        conn.rollback()
                        return

            count += 1
            if count % batch_size == 0:
                conn.commit()
                print(f"✅ Committed {count} rows...")

        conn.commit()
        print("✅ All rows committed.")
        cursor.close()
        conn.close()
        print("✅ Degradation metrics updated successfully.")

    except Exception as e:
        print(f"❌ update_data() failed: {e}")
