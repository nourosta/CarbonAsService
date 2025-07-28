from database import SessionLocal
from models import CarbonIntensity, EcoflocResult, GPUImpact, PowerBreakdown, RAMImpact, SSDImpact, HDDImpact, CPUImpact


def save_cpu(model, gwp, adp, pe):
    db = SessionLocal()
    try:
        entry = CPUImpact(
            model=model,
            gwp=gwp,
            adp=adp,
            pe=pe
        )
        db.add(entry)
        db.commit()
    finally:
        db.close()

def save_gpu(model, die_size, ram_size, gwp, adp, pe):
    db = SessionLocal()
    try:
        entry = GPUImpact(model=model, die_size=die_size, ram_size=ram_size, gwp=gwp, adp=adp, pe=pe)
        db.add(entry)
        db.commit()
    finally:
        db.close()

def save_ram(manufacturer, capacity, process, gwp, adp, pe):
    db = SessionLocal()
    try:
        entry = RAMImpact(manufacturer=manufacturer, capacity=capacity, process=process, gwp=gwp, adp=adp, pe=pe)
        db.add(entry)
        db.commit()
    finally:
        db.close()

def save_ssd(manufacturer, capacity, gwp, adp, pe):
    db = SessionLocal()
    try:
        entry = SSDImpact(manufacturer=manufacturer, capacity=capacity, gwp=gwp, adp=adp, pe=pe)
        db.add(entry)
        db.commit()
    finally:
        db.close()

def save_hdd(capacity, units, gwp, adp, pe):
    db = SessionLocal()
    try:
        entry = HDDImpact(capacity=capacity, units=units, gwp=gwp, adp=adp, pe=pe)
        db.add(entry)
        db.commit()
    finally:
        db.close()

# Store power breakdown
def store_power_breakdown(zone: str, data: dict):
    db = SessionLocal()
    try:
        power_data = PowerBreakdown(zone=zone, data=str(data))
        db.add(power_data)
        db.commit()
        db.refresh(power_data)
        return power_data
    finally:
        db.close()

# Store carbon intensity
def store_carbon_intensity(zone: str, data: dict):
    db = SessionLocal()
    try:
        intensity_data = CarbonIntensity(zone=zone, data=str(data))
        db.add(intensity_data)
        db.commit()
        db.refresh(intensity_data)
        return intensity_data
    finally:
        db.close()

def save_ecofloc_results(pid, pname, resource, metrics):
    db = SessionLocal()
    try:
        for metric_name, value, unit in metrics:
            record = EcoflocResult(
                pid=pid,
                process_name=pname,
                resource_type=resource,
                metric_name=metric_name,
                metric_value=value,
                unit=unit
            )
            db.add(record)
        db.commit()
    except Exception as e:
        print(f"[ERROR] DB insert failed: {e}")
    finally:
        db.close()
