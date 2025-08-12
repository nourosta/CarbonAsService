import json
from database import SessionLocal
from sqlalchemy.orm import Session
from models import CarbonIntensity, CaseImpact, EcoflocResult, GPUImpact, MotherboardImpact, PowerBreakdown, RAMImpact, SSDImpact, HDDImpact, CPUImpact, Scope2Result


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


def save_case(type, gwp, adp, pe):
    db = SessionLocal()
    try:
        entry = CaseImpact(type=type, gwp=gwp, adp=adp, pe=pe)
        db.add(entry)
        db.commit()
    finally:
        db.close()

def save_motherboard(gwp, adp, pe):
    db = SessionLocal()
    try:
        entry = MotherboardImpact(gwp=gwp, adp=adp, pe=pe)
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
def store_power_breakdown(db, zone: str, data: dict):
    db = SessionLocal()
    try:
        power_data = PowerBreakdown(zone=zone, data=json.dumps(data))  #
        db.add(power_data)
        db.commit()
        db.refresh(power_data)
        return power_data
    finally:
        db.close()

# Store carbon intensity
def store_carbon_intensity(db, zone: str, data: dict):
    db = SessionLocal()
    try:
        intensity_data = CarbonIntensity(zone=zone, data=json.dumps(data)) 
        db.add(intensity_data)
        db.commit()
        db.refresh(intensity_data)
        return intensity_data
    finally:
        db.close()

def save_ecofloc_results(pid, pname, resource, metrics, cpu_usage=None, ram_usage=None):
    db = SessionLocal()
    try:
        for metric_name, value, unit in metrics:
            record = EcoflocResult(
                pid=pid,
                process_name=pname,
                resource_type=resource,
                metric_name=metric_name,
                metric_value=value,
                unit=unit,
                cpu_usage=cpu_usage,
                ram_usage=ram_usage
            )
            db.add(record)
        db.commit()
    except Exception as e:
        print(f"[ERROR] DB insert failed: {e}")
    finally:
        db.close()


def Ecofloc_results():
    db = SessionLocal()
    try:
        results = db.query(EcoflocResult).all()
        return results
    finally:
        db.close()

def get_all_ecofloc_results(db: Session):
    return db.query(EcoflocResult).all()

def get_latest_carbon_intensity_by_zone(db: Session, zone: str):
    record = (
        db.query(CarbonIntensity)
        .filter(CarbonIntensity.zone == zone)
        .order_by(CarbonIntensity.id.desc())
        .first()
    )
    if record:
        data = json.loads(record.data)
        return {
            "carbonIntensity": data.get("carbonIntensity"),
            "updatedAt": data.get("updatedAt")
        }
    return None


def get_all_carbon_intensity_by_zone(db: Session, zone: str):
    records = (
        db.query(CarbonIntensity)
        .filter(CarbonIntensity.zone == zone)
        .order_by(CarbonIntensity.id.asc())  # oldest to newest
        .all()
    )
    results = []
    for record in records:
        try:
            data = json.loads(record.data)
            results.append({
                "carbonIntensity": data.get("carbonIntensity"),
                "updatedAt": data.get("updatedAt")
            })
        except:
            continue  # skip malformed data
    return results


def get_total_scope3_emissions():
    db = SessionLocal()
    try:
        cpu_total = sum(float(c.gwp or 0) for c in db.query(CPUImpact).all())
        gpu_total = sum(float(g.gwp or 0) for g in db.query(GPUImpact).all())
        ram_total = sum(float(r.gwp or 0) for r in db.query(RAMImpact).all())
        ssd_total = sum(float(s.gwp or 0) for s in db.query(SSDImpact).all())
        hdd_total = sum(float(h.gwp or 0) for h in db.query(HDDImpact).all())
        case_total = sum(float(c.gwp or 0 )for c in db.query(CaseImpact).all())
        motherboard_total = sum(float(m.gwp or 0)for m in db.query(MotherboardImpact).all())
        

        print("[DEBUG] GPU records:", [(g.model, g.gwp) for g in db.query(GPUImpact).all()])
        print("[DEBUG] Totals -> CPU:", cpu_total, "GPU:", gpu_total, "RAM:", ram_total, "SSD:", ssd_total, "HDD:", hdd_total, "Case:", case_total, "Motherboard:", motherboard_total)

        total_scope3 = cpu_total + gpu_total + ram_total + ssd_total + hdd_total + case_total + motherboard_total
        return total_scope3
    finally:
        db.close()

def store_scope2_result(db: Session, process_name: str, resource_type: str,co2_kg: float, energy_kwh: float, carbon_intensity: float):
    
    db_result = Scope2Result(
        process_name=process_name,
        resource_type=resource_type,
        co2_kg=co2_kg,
        energy_kwh=energy_kwh,
        carbon_intensity=carbon_intensity
    )
    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    return db_result