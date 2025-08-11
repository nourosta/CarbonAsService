from datetime import datetime, timedelta
from typing import List
from scheduler import start_scheduler
from models import EcoflocResult
from fastapi import FastAPI,HTTPException , APIRouter, Query, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from electricitymaps import fetch_power_breakdown
from carbon_intensity import fetch_carbon_intensity, fetch_history_carbon_intensity
from system_info import collect_system_info, get_top_processes_ps
import json 
import requests
from pydantic import BaseModel
from crud import get_all_carbon_intensity_by_zone, get_latest_carbon_intensity_by_zone, store_power_breakdown, store_carbon_intensity, save_ram,save_gpu,save_hdd,save_ssd, save_cpu
from database import get_db, init_db
from fastapi.middleware.cors import CORSMiddleware
from system_info import get_top_processes_ps
from ecofloc_runner import  monitor_top_processes

 

app = FastAPI()
router = APIRouter()

# Start the scheduler
scheduler = start_scheduler()

# Define a Pydantic model for input validation
class RAMSpec(BaseModel):
    capacity: int
    manufacturer: str
    process: int

class CPURequest(BaseModel):
    name: str

class SSDSpec(BaseModel):
    capacity : int
    manufacturer : str

class HDDSpec(BaseModel):
    units : int
    type : str
    capacity : int

class CaseSpec(BaseModel):
    case_type : str

class GPUInput(BaseModel):
    model : str
    die_size_mm2: float
    ram_size_gb: float

# Pydantic schema for API output
class EcoflocResultOut(BaseModel):
    id: int
    pid: int
    process_name: str
    resource_type: str
    metric_name: str
    metric_value: float
    unit: str
    timestamp: datetime

    class Config:
        orm_mode = True

def ram_impacts(ram_spec: RAMSpec):
    
    payload = ram_spec.dict()
    try:
        response = requests.post(
            "http://localhost:5000/v1/component/ram",
            headers={"accept": "application/json"},
            json=payload
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Boavizta RAM API error: {str(e)}")


@app.on_event("startup")
def on_startup():
    init_db()

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()


@app.get("/system-info")
async def system_info():
    return collect_system_info()

@app.post("/CPU_Calc/")
async def cpu_calc(cpu_spec: CPURequest):
    try:
        response = requests.post(
                    "http://localhost:5000/v1/component/cpu",
                    json={"name": cpu_spec.name},
                    headers={
                        "accept": "application/json",
                        "Content-Type": "application/json"
                    }
                )    
        response.raise_for_status()  # Handle HTTP errors
        data = response.json()
         # Extract required fields
        impacts = data.get("impacts", {})
        gwp = impacts.get("gwp", {}).get("manufacture", 0)
        adp = impacts.get("adp", {}).get("manufacture", 0)
        pe  = impacts.get("pe", {}).get("manufacture", 0)

        # Save to DB
        save_cpu(
            model=cpu_spec.name,
            gwp=gwp,
            adp=adp,
            pe=pe
        )
        return data
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect to Boavizta API: {str(e)}")
    




@app.post("/RAM-Calc")
async def ram_calc(ram_spec: RAMSpec):

    data = ram_impacts(ram_spec)
    # try:
    #     # Use the inputs provided by the user
    #     payload = ram_spec.dict()  # Assuming direct usage, adjust as necessary for API
    #     #print(payload)
    #     # Modify this request based on how you need to use these inputs in Boavizta API
    #     response = requests.post("http://localhost:5000/v1/component/ram", headers={"accept": "application/json"}, json=payload)
    #     #print(response.json())
    #     response.raise_for_status()  # Handle HTTP errors
    #     data = response.json()
         # Extract required fields
    impacts = data.get("impacts", {})
    gwp = impacts.get("gwp", {}).get("manufacture", 0)
    adp = impacts.get("adp", {}).get("manufacture", 0)
    pe  = impacts.get("pe", {}).get("manufacture", 0)

    # Save to DB
    save_ram(
        manufacturer=ram_spec.manufacturer,
        capacity=ram_spec.capacity,
        process=ram_spec.process,
        gwp=gwp,
        adp=adp,
        pe=pe
    )
    return data
    # except requests.RequestException as e:
    #     raise HTTPException(status_code=500, detail=f"Failed to connect to Boavizta API: {str(e)}")


@app.post("/SSD-Calc")
async def ssd_calc(ssd_spec: SSDSpec):
    try:
        # Use the inputs provided by the user
        payload = ssd_spec.dict()  # Assuming direct usage, adjust as necessary for API
        print(payload)
        # Modify this request based on how you need to use these inputs in Boavizta API
        response = requests.post("http://localhost:5000/v1/component/ssd", headers={"accept": "application/json"}, json=payload)
        print(response.json())
        response.raise_for_status()  # Handle HTTP errors
        data = response.json()
         # Extract required fields
        impacts = data.get("impacts", {})
        gwp = impacts.get("gwp", {}).get("manufacture", 0)
        adp = impacts.get("adp", {}).get("manufacture", 0)
        pe  = impacts.get("pe", {}).get("manufacture", 0)

        # Save to DB
        save_ssd(
            manufacturer=ssd_spec.manufacturer,
            capacity=ssd_spec.capacity,
            gwp=gwp,
            adp=adp,
            pe=pe
        )
        return data
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect to Boavizta API: {str(e)}")
    


@app.post("/HDD-Calc")
async def hdd_calc(hdd_spec: HDDSpec):
    try:
        # Use the inputs provided by the user
        payload = hdd_spec.dict()  # Assuming direct usage, adjust as necessary for API
        print(payload)
        # Modify this request based on how you need to use these inputs in Boavizta API
        response = requests.post("http://boaviztapi:5000/v1/component/hdd", headers={"accept": "application/json"}, json=payload)
        print(response.json())
        response.raise_for_status()  # Handle HTTP errors
        data = response.json()
         # Extract required fields
        impacts = data.get("impacts", {})
        gwp = impacts.get("gwp", {}).get("manufacture", 0)
        adp = impacts.get("adp", {}).get("manufacture", 0)
        pe  = impacts.get("pe", {}).get("manufacture", 0)

        # Save to DB
        save_hdd(
            units=hdd_spec.units,
            capacity=hdd_spec.capacity,
            gwp=gwp,
            adp=adp,
            pe=pe
        )
        return data
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect to Boavizta API: {str(e)}")
    


@app.post("/Case-Calc")
async def case_calc(case_spec: CaseSpec):
    try:
        # Use the inputs provided by the user
        payload = case_spec.dict()  # Assuming direct usage, adjust as necessary for API
        print(payload)
        # Modify this request based on how you need to use these inputs in Boavizta API
        response = requests.post("http://localhost:5000/v1/component/case", headers={"accept": "application/json"}, json=payload)
        print(response.json())
        response.raise_for_status()  # Handle HTTP errors
        return response.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect to Boavizta API: {str(e)}")

@app.post("/GPU-Calc")
def calculate_gpu(gpu: GPUInput):
    model = gpu.model
    die_mm2 = gpu.die_size_mm2
    ram_gb = gpu.ram_size_gb

    # Constants
    die_gwp = 1.97
    die_adp = 5.80E-07
    die_pe = 26.50
    ram_density = 1.25
    gpu_base = 23.71

    # Calculate RAM impacts via internal function (no saving to DB)
    ram_spec = RAMSpec(
        capacity=int(ram_gb),
        manufacturer="Samsung",  # Or get from frontend
        process=30
    )
    ram_data = ram_impacts(ram_spec)

    # Extract impact values
    impacts = ram_data.get("impacts", {})
    ram_gwp = impacts.get("gwp", {}).get("manufacture", 0)
    ram_adp = impacts.get("adp", {}).get("manufacture", 0)
    ram_pe  = impacts.get("pe", {}).get("manufacture", 0)

    # Calculate GPU impacts
    gpu_gwp = (die_mm2 * die_gwp) + ram_gwp + gpu_base
    gpu_adp = (die_mm2 * die_adp) + ram_adp + gpu_base
    gpu_pe  = (die_mm2 * die_pe) + (ram_gb / ram_density) * ram_pe + gpu_base

    print("Saving GPU to database:", model, die_mm2, ram_gb, gpu_gwp, gpu_adp, gpu_pe)

    # Save GPU to DB
    save_gpu(
        model=model,
        die_size=die_mm2,
        ram_size=ram_gb,
        gwp=gpu_gwp,
        adp=gpu_adp,
        pe=gpu_pe
    )

    return {
        "gwp": round(gpu_gwp, 2),
        "adp": round(gpu_adp, 8),
        "pe": round(gpu_pe, 2)
    }


@app.get("/power-breakdown")
async def get_power_breakdown(zone: str = 'FR',db: Session = Depends(get_db)):
    try:
        #fetch data from elecricitymaps
        data = fetch_power_breakdown(zone)

        #Store data in database
        store_power_breakdown(db,zone,data)
        #store_power_breakdown(zone,data)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    # New endpoint for carbon intensity
@app.get("/carbon-intensity")
async def get_carbon_intensity(zone: str = 'FR',db: Session = Depends(get_db)):
    try:
        data = fetch_carbon_intensity(zone)
        #store_carbon_intensity(zone, data)
        store_carbon_intensity(db,zone,data)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    


# CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/top-processes")
def top_processes():
    return get_top_processes_ps()

# @app.get("/energy")
# def energy_measurement(
#     pid: int = Query(..., description="PID of the process to measure"),
#     metric: str = Query("cpu", description="Component to measure (cpu, ram, gpu, nic, sd)"),
#     interval_ms: int = Query(1000, ge=100, le=10000, description="Sampling interval in milliseconds"),
#     duration_s: int = Query(1, ge=1, le=30, description="Total measurement duration in seconds")
# ):
#     """
#     Measure energy usage of a process using EcoFloc for one metric.
#     """
#     result = measure_energy(pid, metric, interval_ms, duration_s)
#     return result

@app.get("/ecofloc/monitor")
def monitor_endpoint(
    limit: int = Query(5, ge=1, le=20),
    interval: int = Query(1000, description="Sampling interval (ms)"),
    duration: int = Query(5, description="Duration in seconds"),
    resources: str = Query("cpu,ram", description="Comma-separated: cpu,ram,gpu,sd,nic")
):
    try:
        resource_list = [r.strip() for r in resources.split(",")]
        results = monitor_top_processes(
            resources=resource_list,
            limit=limit,
            interval=interval,
            duration=duration
        )
        return {"results": results}
    except Exception as e:
        return {"error": str(e)}
    

def fetch_ecofloc_results(db: Session):
    time_24h_ago = datetime.utcnow() - timedelta(hours=24)
    return (
        db.query(EcoflocResult)
        .filter(EcoflocResult.timestamp >= time_24h_ago)
        .order_by(EcoflocResult.timestamp.asc())  # oldest first for evolution plots
        .all()
    )
@app.get("/ecofloc_results/", response_model=List[EcoflocResultOut])
def get_ecofloc_results_endpoint(db: Session = Depends(get_db)):
    # results = fetch_ecofloc_results(db, skip, limit)
    results = fetch_ecofloc_results(db)
    return results

# @app.get("/ecofloc/cpu", response_model=List[EcoflocResultOut])
# def get_all_cpu_data(db: Session = Depends(get_db)):
#     results = (
#         db.query(EcoflocResult)
#         .filter(EcoflocResult.resource_type == "cpu")
#         .filter(EcoflocResult.timestamp.isnot(None))  # just to be safe
#         .all()
#     )
#     return results

@app.get("/ecofloc/cpu", response_model=List[EcoflocResultOut])
def get_cpu_data(db: Session = Depends(get_db)):

    start_of_day = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    return (
        db.query(EcoflocResult)
        .filter(EcoflocResult.resource_type == "cpu")
        .filter(EcoflocResult.timestamp >= start_of_day)
        .all()
    )

@app.get("/ecofloc/ram", response_model=List[EcoflocResultOut])
def get_cpu_data(db: Session = Depends(get_db)):

    start_of_day = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    return (
        db.query(EcoflocResult)
        .filter(EcoflocResult.resource_type == "ram")
        .filter(EcoflocResult.timestamp >= start_of_day)
        .all()
    )

@app.get("/ecofloc/sd", response_model=List[EcoflocResultOut])
def get_cpu_data(db: Session = Depends(get_db)):

    start_of_day = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    return (
        db.query(EcoflocResult)
        .filter(EcoflocResult.resource_type == "sd")
        .filter(EcoflocResult.timestamp >= start_of_day)
        .all()
    )

@app.get("/ecofloc/nic", response_model=List[EcoflocResultOut])
def get_cpu_data(db: Session = Depends(get_db)):

    start_of_day = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    return (
        db.query(EcoflocResult)
        .filter(EcoflocResult.resource_type == "nic")
        .filter(EcoflocResult.timestamp >= start_of_day)
        .all()
    )

@app.get("/ecofloc/gpu", response_model=List[EcoflocResultOut])
def get_cpu_data(db: Session = Depends(get_db)):

    start_of_day = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    return (
        db.query(EcoflocResult)
        .filter(EcoflocResult.resource_type == "gpu")
        .filter(EcoflocResult.timestamp >= start_of_day)
        .all()
    )

# @app.get("/ecofloc/{resource}", response_model=List[EcoflocResultOut])
# def get_resource_data(resource: str, db: Session = Depends(get_db)):
#     valid_resources = {"cpu", "ram", "gpu", "sd", "nic"}
#     if resource not in valid_resources:
#         raise HTTPException(status_code=400, detail="Invalid resource type")

#     start_of_day = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
#     return (
#         db.query(EcoflocResult)
#         .filter(EcoflocResult.resource_type == resource)
#         .filter(EcoflocResult.timestamp >= start_of_day)
#         .all()
#     )


# @app.get("/ecofloc/cpu", response_model=List[EcoflocResultOut])
# def get_today_cpu_data(db: Session = Depends(get_db)):
#     now = datetime.utcnow()
#     start_of_day = datetime(now.year, now.month, now.day)  # 00:00 UTC
#     results = (
#         db.query(EcoflocResult)
#         .filter(EcoflocResult.resource_type == "cpu")
#         .filter(EcoflocResult.timestamp.isnot(None))  # ✅ safeguard
#         .filter(EcoflocResult.timestamp >= start_of_day)
#         .all()
#     )
#     return results


# @app.get("/ecofloc/cpu", response_model=List[EcoflocResultOut])
# def get_today_cpu_data(db: Session = Depends(get_db)):
#     now = datetime.utcnow()
#     start_of_day = datetime(now.year, now.month, now.day)  # Midnight UTC
#     results = (
#         db.query(EcoflocResult)
#         .filter(EcoflocResult.resource_type == "cpu")
#         .filter(EcoflocResult.timestamp >= start_of_day)
#         .all()
#     )
#     return results



# @app.get("/ecofloc/cpu", response_model=List[EcoflocResultOut])
# def get_ecofloc_cpu(db: Session = Depends(get_db)):
#     results = fetch_ecofloc_results(db)
#     cpu_data = [r for r in results if r.resource_type == "cpu"]
#     return cpu_data

# @app.get("/ecofloc/cpu", response_model=List[EcoflocResultOut])
# def get_recent_cpu_data(hours: int = 24, db: Session = Depends(get_db)):
#     time_cutoff = datetime.utcnow() - timedelta(hours=hours)
#     results = (
#         db.query(EcoflocResult)
#         .filter(EcoflocResult.resource_type == "cpu")
#         .filter(EcoflocResult.timestamp >= time_cutoff)
#         .order_by(EcoflocResult.timestamp.asc())
#         .all()
#     )
#     return results

# @app.get("/ecofloc/cpu", response_model=List[EcoflocResultOut])
# def get_recent_cpu_data(hours: int = 24, db: Session = Depends(get_db)):
#     time_cutoff = datetime.utcnow() - timedelta(hours=hours)
#     results = (
#         db.query(EcoflocResult)
#         .filter(EcoflocResult.resource_type == "cpu")
#         .filter(EcoflocResult.timestamp >= time_cutoff)
#         .order_by(EcoflocResult.timestamp.asc())
#         .all()
#     )
#     return results
    
# # @app.get("/ecofloc/cpu", response_model=List[EcoflocResultOut])
# # def get_ecofloc_cpu(db: Session = Depends(get_db)):
# #     results = fetch_ecofloc_results(db)
# #     cpu_data = [r for r in results if r.resource_type == "cpu"]
# #     return cpu_data


# @app.get("/ecofloc/cpu", response_model=List[EcoflocResultOut])
# def get_today_cpu_data(db: Session = Depends(get_db)):
#     now = datetime.utcnow()
#     start_of_day = datetime.combine(now.date(), time.min)  # 00:00 UTC
#     end_of_day = datetime.combine(now.date(), time.max)    # 23:59:59.999999 UTC

#     results = (
#         db.query(EcoflocResult)
#         .filter(EcoflocResult.resource_type == "cpu")
#         .filter(EcoflocResult.timestamp >= start_of_day)
#         .filter(EcoflocResult.timestamp <= end_of_day)
#         .order_by(EcoflocResult.timestamp.asc())
#         .all()
#     )
#     return results


# @app.get("/ecofloc/ram", response_model=List[EcoflocResultOut])
# def get_today_cpu_data(db: Session = Depends(get_db)):
#     now = datetime.utcnow()
#     start_of_day = datetime.combine(now.date(), time.min)  # 00:00 UTC
#     end_of_day = datetime.combine(now.date(), time.max)    # 23:59:59.999999 UTC

#     results = (
#         db.query(EcoflocResult)
#         .filter(EcoflocResult.resource_type == "ram")
#         .filter(EcoflocResult.timestamp >= start_of_day)
#         .filter(EcoflocResult.timestamp <= end_of_day)
#         .order_by(EcoflocResult.timestamp.asc())
#         .all()
#     )
#     return results
    
# @app.get("/api/ecofloc")
# async def get_ecofloc_data():
#     try:
#         raw_results = run_ecofloc_simulated()
#         grouped = group_results_by_pid(raw_results)
#         return {"results": grouped}
#     except Exception as e:
#         return {"error": str(e)}


@app.get("/carbon-intensity/last")
def get_last_carbon_intensity(zone: str = "FR", db: Session = Depends(get_db)):
    result = get_latest_carbon_intensity_by_zone(db, zone)
    if not result:
        raise HTTPException(status_code=404, detail="No data found")
    return result


@app.get("/carbon-intensity/history")
def get_carbon_intensity_history(zone: str = "FR", db: Session = Depends(get_db)):
    data = get_all_carbon_intensity_by_zone(db, zone)
    if not data:
        raise HTTPException(status_code=404, detail="No historical data found.")
    return data


class CarbonRequest(BaseModel):
    zone: str = 'FR'
    token: str
    temporal_granularity: str = '15_minutes'
    
# @app.get("/carbon-intensity-history")
# async def get_carbon_intensity_evolution(
#     zone: str = Query('FR', description="Zone code, e.g. 'FR'")
# ):
#     try:
#         # Assuming fetch_history_carbon_intensity is defined and token + temporal granularity are hardcoded or managed internally
#         # If you still need token and temporal_granularity as parameters, you can add them as query params as well
#         data = fetch_history_carbon_intensity(zone=zone)
#         return data
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


@app.get("/carbon-intensity-history")
async def get_carbon_intensity_evolution(
    zone: str = 'FR',
    db: Session = Depends(get_db)
):
    data = get_all_carbon_intensity_by_zone(db, zone)
    return {"history": data}