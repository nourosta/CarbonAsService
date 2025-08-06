from crud import store_carbon_intensity
from carbon_intensity import fetch_carbon_intensity
from database import SessionLocal
from apscheduler.schedulers.background import BackgroundScheduler



def scheduled_carbon_update():
    try:
        zone = 'FR'
        db = SessionLocal()
        data = fetch_carbon_intensity(zone)
        store_carbon_intensity(db, zone, data)
        db.close()
        print(f"✅ Carbon intensity updated at {data.get('updatedAt')}")
    except Exception as e:
        print(f"❌ Error updating carbon intensity: {e}")

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(scheduled_carbon_update, 'interval', minutes=15)
    scheduler.start()
    print("🔄 Scheduler started: carbon intensity will update every 15 minutes.")
    return scheduler