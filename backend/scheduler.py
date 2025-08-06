from crud import store_carbon_intensity, store_power_breakdown
from carbon_intensity import fetch_carbon_intensity
from electricitymaps import fetch_power_breakdown
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


def scheduled_electricitymix_update():
    try:
        zone = 'FR'
        db = SessionLocal()
        data = fetch_power_breakdown(zone)
        store_power_breakdown(db, zone, data)
        db.close()
        print(f"✅ Power breakdown updated at {data.get('updatedAt')}")
    except Exception as e:
        print(f"❌ Error updating power breakdown: {e}")

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(scheduled_carbon_update, 'interval', minutes=5)
    scheduler.add_job(scheduled_electricitymix_update, 'interval', minutes=5)
    scheduler.start()
    print("🔄 Scheduler started: carbon intensity will update every 5 minutes.")
    return scheduler