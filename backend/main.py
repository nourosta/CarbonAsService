from fastapi import FastAPI,HTTPException , APIRouter
from electricitymaps import fetch_power_breakdown
from carbon_intensity import fetch_carbon_intensity
from system_info import collect_system_info
import json 
import requests
from pydantic import BaseModel
 

app = FastAPI()
router = APIRouter()

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
    die_size_mm2: float
    ram_size_gb: float

@app.get("/")
async def root():
    return {"message": "Hello from FastAPI backend!"}

@app.get("/system-info")
async def system_info():
    return collect_system_info()

@app.post("/CPU_Calc/")
async def cpu_calc(request: CPURequest):
    try:
        response = requests.post(
                    "http://localhost:5000/v1/component/cpu",
                    json={"name": request.name},
                    headers={
                        "accept": "application/json",
                        "Content-Type": "application/json"
                    }
                )    
        response.raise_for_status()  # Handle HTTP errors
        return response.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect to Boavizta API: {str(e)}")
    




@app.post("/RAM-Calc")
async def ram_calc(ram_spec: RAMSpec):
    try:
        # Use the inputs provided by the user
        payload = ram_spec.dict()  # Assuming direct usage, adjust as necessary for API
        #print(payload)
        # Modify this request based on how you need to use these inputs in Boavizta API
        response = requests.post("http://localhost:5000/v1/component/ram", headers={"accept": "application/json"}, json=payload)
        #print(response.json())
        response.raise_for_status()  # Handle HTTP errors
        return response.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect to Boavizta API: {str(e)}")


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
        return response.json()
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
        return response.json()
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
    die_mm2 = gpu.die_size_mm2
    ram_gb = gpu.ram_size_gb

    # Constants
    die_gwp = 1.97
    die_adp = 5.80E-07
    die_pe = 26.50
    ram_density = 1.25
    gpu_base = 23.71

     # Call internal RAM-Calc API
    try:
        ram_payload = {
            "capacity": ram_gb,
            "manufacturer": "Samsung",
            "process": 30
        }
        response = requests.post("http://localhost:8000/RAM-Calc", json=ram_payload)
        response.raise_for_status()
        ram_data = response.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"RAM impact fetch failed: {str(e)}")


    # Get RAM impact values
    impacts = ram_data.get("impacts", {})
    ram_gwp = impacts.get("gwp", {}).get("embedded", {}).get("value", 0)
    ram_adp = impacts.get("adp", {}).get("embedded", {}).get("value", 0)
    ram_pe = impacts.get("pe", {}).get("embedded", {}).get("value", 0)

    # Calculate GPU impacts
    gpu_gwp = (die_mm2 * die_gwp) + ram_gwp + gpu_base
    gpu_adp = (die_mm2 * die_adp) + ram_adp + gpu_base
    gpu_pe = (die_mm2 * die_pe) + (ram_gb / ram_density) * ram_pe + gpu_base

    return {
        "gwp": round(gpu_gwp, 2),
        "adp": round(gpu_adp, 8),
        "pe": round(gpu_pe, 2)
    }


@app.get("/power-breakdown")
async def get_power_breakdown(zone: str = 'FR'):
    try:
        #fetch data from elecricitymaps
        data = fetch_power_breakdown(zone)

        #Store data in database
        #store_power_breakdown(zone,data)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    # New endpoint for carbon intensity
@app.get("/carbon-intensity")
async def get_carbon_intensity(zone: str = 'FR'):
    try:
        data = fetch_carbon_intensity(zone)
        #store_carbon_intensity(zone, data)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))