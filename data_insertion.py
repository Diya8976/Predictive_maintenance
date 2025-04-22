import pandas as pd
import pymysql

# DB Config
db_config = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "root",
    "database": "predictive_maintenance",
    "port": 3306
}

# Read CSV with proper separator
df = pd.read_csv("sensor-fault-detection.csv", sep=';')

# Rename columns to match DB
df.rename(columns={
    'Timestamp': 'timestamp',
    'SensorId': 'sensor_id',
    'Value': 'value'
}, inplace=True)

# Convert timestamp
df['timestamp'] = pd.to_datetime(df['timestamp'])

# MySQL Insert
try:
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()

    # Create correct table
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS current_sensor1 (
        id INT AUTO_INCREMENT PRIMARY KEY,
        timestamp DATETIME,
        sensor_id VARCHAR(50),
        value FLOAT
    );
    """
    cursor.execute(create_table_sql)

    # Insert into table
    insert_sql = """
    INSERT INTO current_sensor1 (timestamp, sensor_id, value)
    VALUES (%s, %s, %s)
    """
    data_to_insert = df[['timestamp', 'sensor_id', 'value']].values.tolist()
    cursor.executemany(insert_sql, data_to_insert)
    conn.commit()

    print("✅ Data inserted successfully!")

except Exception as e:
    print(f"❌ Error inserting data: {e}")

finally:
    cursor.close()
    conn.close()
