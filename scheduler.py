import time
import schedule
import threading
from app import update_data

def job():
    try:
        print("⏳ Updating data...")
        update_data()
        print("✅ Data updated successfully!")
    except Exception as e:
        print(f"❌ Error in update_data: {e}")

# Schedule the job every hour
schedule.every().hour.do(job)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(30)

# Start the scheduler thread
def start_scheduler():
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print("🕒 Scheduler started! Running every hour...")

# ✅ Auto-start if this file is run directly
if __name__ == "__main__":
    start_scheduler()
    while True:
        time.sleep(1)  # Keep main thread alive
