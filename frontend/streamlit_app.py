import math
import streamlit as st
import requests
import time
import pandas as pd
import plotly.express as px
from dbgpu import GPUDatabase
from streamlit_autorefresh import st_autorefresh
from datetime import datetime


tab1, tab2 , tab3 , tab4= st.tabs(["🏠 System Overview", "📈 Live Monitoring","🚗💨 Carbon Emissions", "📊 System Summary Overview"])
st.set_page_config(page_title="System Info Dashboard", layout="wide") 


FASTAPI_BASE_URL = "http://localhost:8000"

def wait_for_backend():
    for i in range(10):
        try:
            requests.get(FASTAPI_BASE_URL)
            return True
        except requests.exceptions.ConnectionError:
            time.sleep(1)
    return False


with tab1: 


    st.title("💻 System Information Dashboard")

    # Fetch data
    try:
        response = requests.get(f"{FASTAPI_BASE_URL}/system-info")
        data = response.json()
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        st.stop()

    # ---- CARDS ----
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("CPU", data.get("cpu", "Unknown"))
    col2.metric("RAM (GB)", round(data.get("ram_gb", 0), 2))
    col3.metric("GPU", ", ".join(data.get("gpus", [])))
    col4.metric("OS", data.get("os", "Unknown"))

    st.markdown("---")

    # ---- DISK INFORMATION ----
    st.subheader("Disk Information")
    real_disks = [d for d in data.get("disks", []) if not d["name"].startswith("loop")]

    if real_disks:
        df = pd.DataFrame(real_disks)
        st.dataframe(df)

        # Try to convert sizes to GB/TB for visualization
        def size_to_gb(size_str):
            try:
                size_str = size_str.upper()
                if size_str.endswith("T"):
                    return float(size_str[:-1]) * 1024
                elif size_str.endswith("G"):
                    return float(size_str[:-1])
                elif size_str.endswith("M"):
                    return float(size_str[:-1]) / 1024
                elif size_str.endswith("K"):
                    return float(size_str[:-1]) / (1024 * 1024)
            except:
                return 0
            return 0

        df["size_gb"] = df["size"].apply(size_to_gb)
        fig = px.pie(df, values="size_gb", names="name", title="Disk Size Distribution (GB)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No physical disks found.")

    st.title("Boavizta CPU Calculation")
    st.subheader("CPU Scope3 Calculations", divider=True)

    cpu_name = st.text_input(" CPU :", value=data.get("cpu"))
    if "cpu_data" not in st.session_state or st.session_state.get("cached_cpu_name") != cpu_name:
        try:
            payload = {"name": cpu_name}
            response = requests.post(f"{FASTAPI_BASE_URL}/CPU_Calc", json=payload)
            response.raise_for_status()
            cpu_data = response.json()

            # Store result and CPU name in session_state
            st.session_state.cpu_data = cpu_data
            st.session_state.cached_cpu_name = cpu_name

        except requests.RequestException as e:
            st.error(f"Failed to retrieve CPU data: {str(e)}")
            cpu_data = {}
    else:
        cpu_data = st.session_state.cpu_data

    st.subheader("Impact Information:")

    impacts = cpu_data.get("impacts", {})
    for key, impact_info in impacts.items():
        st.text(f"{key.upper()}")
        st.text(f"Unit: {impact_info['unit']}")
        st.text(f"Manufacture Impact: {impact_info['manufacture']} {impact_info['unit']}")
        st.text(f"Use Impact: {impact_info['use']} {impact_info['unit']}")
        st.text("")


    st.subheader("RAM Scope3 Calculations", divider=True)

    # --- Input Fields ---
    ram_capacity = st.number_input(
        "Enter RAM Capacity (GB):",
        min_value=1,
        value= int(math.ceil(round(data.get("ram_gb", 0), 2))) #int(math.ceil(float(parsed_info["RAM"].split()[0]) if parsed_info.get("RAM") != "Unknown" else 32))
    )
    ram_manufacturer = st.text_input("Enter RAM Manufacturer:", value="Samsung")
    ram_process = st.number_input("Enter Process (nm):", min_value=1, max_value=100, value=30)

    left, middle, right = st.columns(3)
    # --- Create a cache key for the current RAM config ---
    ram_cache_key = f"{ram_capacity}_{ram_manufacturer}_{ram_process}"

    # --- Fetch RAM Data ---
    if "ram_data" not in st.session_state or st.session_state.get("cached_ram_key") != ram_cache_key:
        try:
            payload = {
                "capacity": ram_capacity,
                "manufacturer": ram_manufacturer,
                "process": ram_process
            }
            response = requests.post(f"{FASTAPI_BASE_URL}/RAM-Calc", json=payload)
            response.raise_for_status()
            ram_data = response.json()

            # Cache the data
            st.session_state.ram_data = ram_data
            st.session_state.cached_ram_key = ram_cache_key
        except requests.RequestException as e:
            st.error(f"Failed to retrieve RAM data: {str(e)}")
            ram_data = {}
    else:
        ram_data = st.session_state.ram_data

    # --- Display Results ---
    st.subheader("Impact Information:")

    impacts = ram_data.get("impacts", {})
    for key, impact_info in impacts.items():
        st.text(f"{key.upper()}")
        st.text(f"Unit: {impact_info['unit']}")
        st.text(f"Manufacture Impact: {impact_info['manufacture']} {impact_info['unit']}")
        st.text(f"Use Impact: {impact_info['use']} {impact_info['unit']}")
        st.text("")


    # Separate disks into SSD and HDD
    ssds = [d for d in real_disks if d["type"] == "SSD"]
    hdds = [d for d in real_disks if d["type"] == "HDD"]

    def parse_disk_size(size_str):
        """Convert disk size string (e.g., '1.9T', '500G', '320M') into GB."""
        size_str = size_str.upper().strip().replace(",",".")
        if size_str.endswith("T"):
            return float(size_str.replace("T", "")) * 1000  # or 1024 for TB -> GB
        elif size_str.endswith("G"):
            return float(size_str.replace("G", ""))
        elif size_str.endswith("M"):
            return float(size_str.replace("M", "")) / 1000  # MB -> GB
        elif size_str.endswith("K"):
            return float(size_str.replace("K", "")) / 1000000  # KB -> GB
        else:
            return float(size_str)  # Already in GB

    st.subheader("Boavizta Disk Calculations", divider=True)


    if ssds:
        st.subheader("SSD Information")
        selected_ssd_index = st.selectbox(
                "Select SSD:", options=range(len(ssds)), format_func=lambda x: f"{ssds[x]['model']} ({ssds[x]['size']})"
            )
        selected_ssd = ssds[selected_ssd_index]

        ssd_capacity = st.number_input("Enter SSD Capacity (GB):", min_value=1, value=int(math.ceil(parse_disk_size(selected_ssd["size"]))))
        ssd_manufacturer = st.text_input("Enter SSD Manufacturer:", value=selected_ssd["model"] or "Unknown")
    # Create cache key for this SSD config
        ssd_cache_key = f"{ssd_capacity}_{ssd_manufacturer}"

        # Fetch SSD data only if needed
        if "ssd_data" not in st.session_state or st.session_state.get("cached_ssd_key") != ssd_cache_key:
            try:
                ssd_payload = {"capacity": ssd_capacity, "manufacturer": ssd_manufacturer}
                response = requests.post(f"{FASTAPI_BASE_URL}/SSD-Calc", json=ssd_payload)
                response.raise_for_status()
                ssd_data = response.json()

                # Cache it
                st.session_state.ssd_data = ssd_data
                st.session_state.cached_ssd_key = ssd_cache_key
            except requests.RequestException as e:
                st.error(f"Failed to retrieve SSD data: {str(e)}")
                ssd_data = {}
        else:
            ssd_data = st.session_state.ssd_data

        # --- Display Results ---
        st.subheader("Impact Information:")

        impacts = ssd_data.get("impacts", {})
        for key, impact_info in impacts.items():
            st.text(f"{key.upper()}")
            st.text(f"Unit: {impact_info['unit']}")
            st.text(f"Manufacture Impact: {impact_info['manufacture']} {impact_info['unit']}")
            st.text(f"Use Impact: {impact_info['use']} {impact_info['unit']}")
            st.text("")

    # HDD Section
    if hdds:
        st.subheader("HDD Information")
        selected_hdd_index = st.selectbox(
                "Select HDD:", options=range(len(hdds)), format_func=lambda x: f"{hdds[x]['model']} ({hdds[x]['size']})"
            )
        selected_hdd = hdds[selected_hdd_index]

        hdd_capacity = st.number_input("Enter HDD Capacity (GB):", min_value=1, value=int(math.ceil(parse_disk_size(selected_hdd["size"]))))
        hdd_units = st.number_input("Enter HDD Units:", min_value=1, value=1)
        #Create cache key for this SSD config
        hdd_cache_key = f"{hdd_capacity}_{hdd_units}"
        if "cached_hdd_key" not in st.session_state or st.session_state.get("cached_hdd_key") != hdd_cache_key:
            try:
                hdd_payload = {"capacity": hdd_capacity, "units": hdd_units}
                response = requests.post(f"{FASTAPI_BASE_URL}/HDD-Calc", json=hdd_payload)
                response.raise_for_status()
                hdd_data = response.json()

                # Cache it
                st.session_state.hdd_data = hdd_data
                st.session_state.cached_hdd_key = hdd_cache_key
            except requests.RequestException as e:
                st.error(f"Failed to retrieve HDD data: {str(e)}")
                hdd_data = {}
        else:
            hdd_data = st.session_state.hdd_data

        st.subheader("HDD Impact Information:")

        impacts = hdd_data.get("impacts", {})
        for key, impact_info in impacts.items():
            st.text(f"{key.upper()}")
            st.text(f"Unit: {impact_info['unit']}")
            st.text(f"Manufacture Impact: {impact_info['manufacture']} {impact_info['unit']}")
            st.text(f"Use Impact: {impact_info['use']} {impact_info['unit']}")
            st.text("")
    else:
        st.info("No HDDs detected.")

    st.title("Server Case Scope3 Calculation")

    st.subheader("Boavizta Case Calculations", divider = True)

    # Create input fields for SSD specifications
    case_type = st.selectbox("Case Type :", ("blade", "rack"),)
    left, middle, right = st.columns(3)

        # --- Input ---
    case_type = st.selectbox("Case Type :", ("blade", "rack"), key="case_type_selectbox")

    # --- Unique Cache Key ---
    case_cache_key = f"case_{case_type}"

    # HTTP POST request with inputs to FastAPI endpoint
    if "case_data" not in st.session_state or st.session_state.get("cached_case_key") != case_cache_key:
        try:
            payload = {"case_type": case_type}
            response = requests.post(f"{FASTAPI_BASE_URL}/Case-Calc", json=payload)
            response.raise_for_status()
            case_data = response.json()

            # Store result in session_state
            st.session_state.case_data = case_data
            st.session_state.cached_case_key = case_cache_key
        except requests.RequestException as e:
            st.error(f"Failed to retrieve Case data: {str(e)}")
            case_data = {}
    else:
        case_data = st.session_state.case_data

    # Display the first 6 impact entries
    st.subheader("Impact Information:")

    impacts = case_data.get("impacts", {})
    for key, impact_info in impacts.items():
        st.text(f"{key.upper()}")
        st.text(f"Unit: {impact_info['unit']}")
        st.text(f"Manufacture Impact: {impact_info['manufacture']} {impact_info['unit']}")
        st.text(f"Use Impact: {impact_info['use']} {impact_info['unit']}")
        st.text("")


        
    st.title("Motherboard Scope3 Calculation (API non functional)")

    st.subheader("Boavizta Motherboard Calculations", divider = True)


    def post_motherboard_impact(data):
        url = f"{FASTAPI_BASE_URL}/motherboard/"  # Adjust if your backend runs elsewhere
        response = requests.post(url, json=data)
        if response.status_code == 200:
            st.info("Motherboard impact saved!")
        else:
            st.error(f"Failed to save motherboard impact: {response.text}")

        # --- Constants ---
    MOTHERBOARD_GWP = 66.10   # kgCO2eq per unit
    MOTHERBOARD_ADP = 3.69E-03  # kgSbeq per unit
    MOTHERBOARD_PE  = 836.00   # MJ per unit

    # --- Initialize session state ---
    if "motherboard_units" not in st.session_state:
        st.session_state["motherboard_units"] = 1

    # --- Input ---
    motherboard_units = st.number_input(
        "Enter Motherboard Units:",
        min_value=1,
        value=st.session_state["motherboard_units"],
        key="motherboard_units"
    )

    # --- Calculations ---
    total_gwp = motherboard_units * MOTHERBOARD_GWP
    total_adp = motherboard_units * MOTHERBOARD_ADP
    total_pe  = motherboard_units * MOTHERBOARD_PE

    # --- Store in session_state (optional if used elsewhere) ---
    motherboard_data = {
    "gwp": total_gwp,
    "adp": total_adp,
    "pe": total_pe
}
    if "motherboard_saved" not in st.session_state:
        post_motherboard_impact(motherboard_data)
        st.session_state["motherboard_saved"] = True

    # Convert to impacts structure
    motherboard_impacts = {
        "GWP": {"manufacture": float(motherboard_data.get("gwp", 0)), "use": 0.0, "unit": "kgCO2eq"},
        "ADP": {"manufacture": float(motherboard_data.get("adp", 0)), "use": 0.0, "unit": "kgSbeq"},
        "PE":  {"manufacture": float(motherboard_data.get("pe", 0)),  "use": 0.0, "unit": "MJ"},
    }

    
    # --- Display in Columns ---
    left, middle, right = st.columns(3)
    with left:
        st.metric("GWP", f"{total_gwp:.2f} kgCO₂eq")
    with middle:
        st.metric("ADP", f"{total_adp:.5f} kgSbeq")
    with right:
        st.metric("PE", f"{total_pe:.2f} MJ")



    st.subheader("Boavizta GPU Calculations", divider=True)
    detected_GPU = data.get("gpus")

    gpus = [gpu for gpu in detected_GPU]  # Ensure this is populated correctly

    @st.cache_data(show_spinner=False, max_entries=1)
    def fetch_gpu_impacts(gpus: list):
        if not gpus:
            return None, []

        database = GPUDatabase.default()

        api_payloads = []
        for gpu_brand in gpus:
            try:
                spec = database.search(gpu_brand)
                die_size = spec.die_size_mm2
                ram_size = spec.memory_size_gb
            except KeyError:
                die_size = 100.0
                ram_size = 8

            api_payloads.append({
                "model": gpu_brand,
                "die_size_mm2": die_size,
                "ram_size_gb": ram_size
            })

        try:
            response = requests.post(f"{FASTAPI_BASE_URL}/GPU-Calc", json=api_payloads)  # send list here
            response.raise_for_status()
            data = response.json()  # This will be a list of results

            # Initialize totals
            gwp_total = {"manufacture": 0, "use": 0, "unit": "kgCO₂eq"}
            adp_total = {"manufacture": 0, "use": 0, "unit": "kgSbeq"}
            pe_total  = {"manufacture": 0, "use": 0, "unit": "MJ"}

            per_gpu_results = []
            for result in data:
                gwp_total["manufacture"] += result.get("gwp", 0)
                adp_total["manufacture"] += result.get("adp", 0)
                pe_total["manufacture"]  += result.get("pe", 0)

                per_gpu_results.append({
                    "gpu": result.get("model", "Unknown"),
                    "gwp": result.get("gwp", 0),
                    "adp": result.get("adp", 0),
                    "pe":  result.get("pe", 0),
                    "saved": result.get("saved", False),
                    "message": result.get("message", "")
                })

            return {
                "gwp": gwp_total,
                "adp": adp_total,
                "pe": pe_total
            }, per_gpu_results

        except requests.RequestException as e:
            st.error(f"Failed to calculate GPU impact: {str(e)}")
            return None, []





    # --- UI Part (widgets outside cache) ---
    if gpus:
        database = GPUDatabase.default()
        api_payloads = []

        for gpu_index, detected_gpu in enumerate(gpus):
            st.markdown(f"### GPU {gpu_index + 1} ({detected_gpu})")

            gpu_brand = st.text_input(
                f"GPU Model for GPU {gpu_index + 1}",
                value=detected_gpu,
                key=f"gpu_brand_{gpu_index}"
            )

            try:
                spec = database.search(gpu_brand)
                die_size = spec.die_size_mm2
                ram_size = spec.memory_size_gb
            except KeyError:
                st.warning(f"Specs for {gpu_brand} not found. Please enter manually.")
                die_size = 100.0
                ram_size = 8

            die_size_input = st.number_input(
                f"Die Size (mm²) for GPU {gpu_index + 1}",
                value=die_size,
                format="%.2f",
                key=f"die_size_{gpu_index}"
            )
            ram_size_input = st.number_input(
                f"RAM Size (GB) for GPU {gpu_index + 1}",
                value=ram_size,
                key=f"ram_size_{gpu_index}"
            )

            api_payloads.append({
                "model": gpu_brand,
                "die_size_mm2": die_size_input,
                "ram_size_gb": ram_size_input
            })

        # --- Call cached API fetch ---
        gpu_data, per_gpu_results = fetch_gpu_impacts(detected_GPU)

        # Show per GPU
        for result in per_gpu_results:
            st.markdown(f"**{result['gpu']}**")
            st.markdown(f"- **GWP:** {result['gwp']} kgCO₂eq")
            st.markdown(f"- **ADP:** {result['adp']} kgSbeq")
            st.markdown(f"- **PE:** {result['pe']} MJ")



        # --- Display results ---
        st.subheader("GPU Impact Results (Per GPU)")
        # for result in per_gpu_results:
        #     st.markdown(f"**{result['gpu']}**")
        #     st.markdown(f"- **GWP:** {result['gwp']} kgCO₂eq")
        #     st.markdown(f"- **ADP:** {result['adp']} kgSbeq")
        #     st.markdown(f"- **PE:** {result['pe']} MJ")

        st.markdown("**Total Environmental Impact (GPUs only):**")
        for impact_type, vals in gpu_data.items():
            st.markdown(f"- **{impact_type.upper()}**: {vals['manufacture']} {vals['unit']}")

    else:
        st.info("No GPUs detected in the system information.")



    # st.subheader("Boavizta GPU Calculations", divider=True, help="Based on formula found in the following article: https://hal.science/hal-04643414v1/document")

    # gpus = [gpu for gpu in detected_GPU]  # Populate from /system-info

    # if gpus:
    #     selected_gpu_index = st.selectbox("Select GPU:", range(len(gpus)), format_func=lambda x: f"GPU {x + 1}",  key="gpu_selectbox")
    #     selected_gpu = gpus[selected_gpu_index]
    #     gpu_brand = st.text_input("GPU Model", value=selected_gpu)

    #     # Try to auto-detect specs
    #     database = GPUDatabase.default()
    #     try:
    #         spec = database.search(gpu_brand)
    #         die_size = spec.die_size_mm2
    #         ram_size = spec.memory_size_gb
    #     except KeyError:
    #         st.warning(f"Specs for {gpu_brand} not found. Please enter manually.")
    #         die_size = 100.0
    #         ram_size = 8

    #     die_size_input = st.number_input("Die Size (mm²)", value=die_size, format="%.2f")
    #     ram_size_input = st.number_input("RAM Size (GB)", value=ram_size)

        
    #     payload = {
    #         "model" : selected_gpu,
    #         "die_size_mm2": die_size_input,
    #         "ram_size_gb": ram_size_input
    #     }
    #     try:
    #         response = requests.post(f"{FASTAPI_BASE_URL}/GPU-Calc", json=payload)
    #         response.raise_for_status()
    #         data = response.json()

        
    #         st.markdown(f"**GWP:** {data['gwp']} kgCO₂eq")
    #         st.markdown(f"**ADP:** {data['adp']} kgSbeq")
    #         st.markdown(f"**PE:** {data['pe']} MJ")

    #     except requests.RequestException as e:
    #         st.error(f"Failed to calculate GPU impact: {str(e)}")
    # else:
    #     st.info("No GPUs detected in the system information.")

    # st.title("System Info & Electricity Data")

    # if wait_for_backend():
    #     st.subheader("System Information")
    #     sys_info = requests.get(f"{FASTAPI_BASE_URL}/system-info").json()
    #     st.json(sys_info)

    st.title("Power and Carbon")

    ### Display Power Breakdown

    try:
        # Fetch data from FastAPI backend
        response = requests.get(f"{FASTAPI_BASE_URL}/power-breakdown?zone=FR")
        response.raise_for_status()
        data = response.json()

        st.subheader('Electricity Maps Live Power Breakdown')
        st.subheader(f"Zone: {data.get('zone', 'N/A')}")

        # Extract breakdown data
        breakdown = data.get('powerProductionBreakdown', {})
        df_elec = pd.DataFrame(breakdown.items(), columns=["Source", "Power (MW)"])

        # Display JSON breakdown
        #st.json(breakdown)

        # Create pie chart
        fig = px.pie(df_elec, values='Power (MW)', names='Source', title="Energy Production Breakdown")
        st.plotly_chart(fig)
    except Exception as e:
        st.error(f"Failed to fetch power breakdown data: {e}")


    if wait_for_backend():
        response = requests.get(f"{FASTAPI_BASE_URL}/")
        st.write("Message from backend:", response.json().get("message"))
    else:
        st.error("Backend not available!")


    ### Display Carbon Intensity

    try:
        # Fetch data from FastAPI backend
        response_carbon = requests.get(f"{FASTAPI_BASE_URL}/carbon-intensity?zone=FR")
        response_carbon.raise_for_status()
        data_carbon = response_carbon.json()

        st.subheader('ElectricityMaps Live Carbon Intensity')
        st.subheader(f"Zone: {data_carbon.get('zone', 'N/A')}")

        # Display JSON data
        #st.json(data_carbon)

        # Optional: Visualize carbon intensity data if applicable
        df_carbon = pd.DataFrame(data_carbon.items(), columns=['Metric', 'Value'])
        st.write(df_carbon)
    except Exception as e:
        st.error(f"Failed to fetch carbon intensity data: {e}")


with tab2 : 


        # Auto-refresh every 10 seconds
    st_autorefresh(interval=10000, key="auto_refresh")

    resource_types = ["cpu", "ram", "gpu", "sd", "nic"]

    for resource_type in resource_types:
        st.markdown(f"## 🔍 Resource: {resource_type.upper()}")

        # Fetch data
        try:
            response = requests.get(f"{FASTAPI_BASE_URL}/ecofloc/{resource_type}")
            response.raise_for_status()
            data = response.json()
            df = pd.DataFrame(data)
        except Exception as e:
            st.error(f"Error fetching data for {resource_type}: {e}")
            continue  # Skip to next resource_type

        # Validate and clean data
        required = ['timestamp', 'metric_value', 'metric_name', 'process_name']
        missing = [col for col in required if col not in df.columns]
        if missing:
            st.error(f"Missing expected columns in {resource_type}: {missing}")
            st.write("Available columns:", df.columns.tolist())
            continue

        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df['metric_value'] = pd.to_numeric(df['metric_value'], errors='coerce')
        df.dropna(subset=['timestamp', 'metric_value'], inplace=True)

        for col in df.select_dtypes(include="object").columns:
            df[col] = df[col].astype(str)

        # Filter to total energy only
        energy_df = df[df['metric_name'].str.lower().str.contains("total energy")]

        if energy_df.empty:
            st.info(f"No energy data available for {resource_type}.")
            continue
        

        # Total energy consumed today
        total_energy = (
            energy_df.groupby("process_name")["metric_value"]
            .sum()
            .reset_index()
            .sort_values(by="metric_value", ascending=False)
        )

          # Calculate total energy in kWh
        total_energy['metric_value_kwh'] = total_energy['metric_value'] / (3.6 / 10**6)  # Convert J to kWh

        try:
            response = requests.get(f"{FASTAPI_BASE_URL}/carbon-intensity/last?zone=FR")
            response.raise_for_status()
            carbon_data = response.json()
            carbon_intensity = carbon_data.get("carbonIntensity")  # in gCO2/kWh

            # Multiply for each process
            total_energy['co2_emission_g'] = total_energy['metric_value_kwh'] * carbon_intensity

              # Optionally: store into DB
            for _, row in total_energy.iterrows():
                payload = {
                    "pid": row.get("process_name", None),  # if available in your dataframe
                    "resource_type": resource_type,
                    "energy_kwh": row['metric_value_kwh'],
                    "co2_g": row['co2_g']
                }
                try:
                    post_resp = requests.post(f"{FASTAPI_BASE_URL}/eco-scope2-co2/", json=payload)
                    post_resp.raise_for_status()
                except requests.RequestException as e:
                    st.error(f"Failed to post energy data: {e}")

        except Exception as e:
            st.error(f"Error fetching carbon intensity: {e}")


        # Layout: bar + line plots
        col1, col2 = st.columns(2)

        with col1:
            st.subheader(f"⚡ Total Energy per Process ({resource_type.upper()})")
            fig_bar = px.bar(
                total_energy,
                x="process_name",
                y="metric_value",
                labels={"process_name": "Process", "metric_value": "Energy (J)"},
                title=f"{resource_type.upper()} - Energy by Process"
            )
            st.plotly_chart(fig_bar, use_container_width=True, key=f"{resource_type}_bar")

        with col2:
            st.subheader("📈 Energy Over Time")
            fig_line = px.line(
                energy_df,
                x="timestamp",
                y="metric_value",
                color="process_name",
                labels={"timestamp": "Time", "metric_value": "Energy (J)", "process_name": "Process"},
                title=f"{resource_type.upper()} - Energy Over Time"
            )
            fig_line.update_layout(height=500)
            st.plotly_chart(fig_line, use_container_width=True, key=f"{resource_type}_line")

        # # Metrics summary
        # st.metric(f"🔋 Total Energy Today ({resource_type.upper()})", f"{total_energy['metric_value'].sum():.2f} J")

        # top5 = total_energy.head(5)
        # st.subheader(f"🏭 Top 5 Energy Consumers ({resource_type.upper()})")
        # st.table(top5)

          # Metrics summary
        total_energy_sum_j = total_energy['metric_value'].sum()
        total_energy_sum_kwh = total_energy_sum_j / 3_600_000
        st.metric(f"🔋 Total Energy Today ({resource_type.upper()})", f"{total_energy_sum_j:.2f} J / {total_energy_sum_kwh:.8f} kWh")

        top5 = total_energy.head(5).copy()
        top5['metric_value_kwh'] = top5['metric_value'] / 3_600_000
        st.subheader(f"🏭 Top 5 Energy Consumers ({resource_type.upper()})")
        st.table(top5[['process_name', 'metric_value', 'metric_value_kwh']])


        st.markdown("---")

with tab3:
    st.title("Carbon Footprint Dashboard")

    # try:
    #     # Fetch latest carbon intensity
    #     response = requests.get(f"{FASTAPI_BASE_URL}/carbon-intensity/last?zone=FR")
    #     response.raise_for_status()
    #     carbon_data = response.json()

    #     carbon_intensity = carbon_data.get("carbonIntensity")
    #     updated_at = carbon_data.get("updatedAt", "N/A")

    #     if carbon_intensity is None:
    #         st.error("Carbon intensity data is not available.")
    #     else:
    #         # st.subheader("Latest Stored Carbon Intensity")
    #         # st.metric("Carbon Intensity", f"{carbon_intensity} gCO₂eq/kWh")
    #         # st.caption(f"Updated at: {updated_at}")

    #         # Fetch carbon intensity history for line plot
    #         try:
    #             response_history = requests.get(f"{FASTAPI_BASE_URL}/carbon-intensity/history?zone=FR")
    #             response_history.raise_for_status()
    #             history_data = response_history.json()

    #             # Build DataFrame
    #             df_history = pd.DataFrame(history_data)
    #             df_history['updatedAt'] = pd.to_datetime(df_history['updatedAt'], errors='coerce')
    #             df_history['carbonIntensity'] = pd.to_numeric(df_history['carbonIntensity'], errors='coerce')
    #             df_history.dropna(subset=['updatedAt', 'carbonIntensity'], inplace=True)
    #             df_history = df_history.sort_values('updatedAt')

    #             # Create line plot
    #             fig_line = px.line(
    #                 df_history,
    #                 x='updatedAt',
    #                 y='carbonIntensity',
    #                 labels={'updatedAt': 'Updated Time', 'carbonIntensity': 'gCO₂/kWh'},
    #                 title='🧭 Carbon Intensity Over Time',
    #                 height=350
    #             )

    #             # Display metric + line plot side-by-side
    #             col1, col2 = st.columns([1, 3])

    #             with col1:
    #                 st.subheader("Live Carbon Intensity")
    #                 st.metric("Carbon Intensity", f"{carbon_intensity} gCO₂eq/kWh")
    #                 st.caption(f"Updated at: {updated_at}")

    #             with col2:
    #                 st.plotly_chart(fig_line, use_container_width=True)

    #         except Exception as e:
    #             st.warning(f"Could not load carbon intensity history: {e}")


    #         st.title("Carbon Intensity Viewer")

    #         try:
    #             # Fetch latest carbon intensity
    #             response = requests.get(f"{FASTAPI_BASE_URL}/carbon-intensity/last?zone=FR")
    #             response.raise_for_status()
    #             carbon_data = response.json()
    #             carbon_intensity = carbon_data.get("carbonIntensity")
    #             updated_at = carbon_data.get("updatedAt", "N/A")

    #         except requests.RequestException as e:
    #             st.error(f"❌ Failed to fetch latest carbon intensity: {e}")
    #             st.stop()

    #             try:
    #                 # Fetch carbon intensity history
    #                 response_history = requests.get(f"{FASTAPI_BASE_URL}/carbon-intensity-history?zone=FR")
    #                 response_history.raise_for_status()
    #                 history_response = response_history.json()

    #                 history_list = history_response.get("history", [])

    #                 if not history_list:
    #                     st.warning("⚠️ No carbon intensity history data available.")
    #                     st.stop()

    #                 # Convert to DataFrame
    #                 df_history = pd.DataFrame(history_list)
    #                 df_history['datetime'] = pd.to_datetime(df_history['datetime'], errors='coerce')
    #                 df_history['datetime_rounded'] = df_history['datetime'].dt.floor("15min")

    #                 latest_datetime_str = carbon_data.get("datetime") or carbon_data.get("updatedAt")

    #                 if latest_datetime_str is None:
    #                     st.warning("Latest carbon intensity datetime is missing, cannot add latest data point.")
    #                 else:
    #                     latest_time = pd.to_datetime(latest_datetime_str).floor("15min")

    #                     if latest_time not in df_history['datetime_rounded'].values:
    #                         latest_row = {
    #                             "zone": carbon_data.get("zone"),
    #                             "carbonIntensity": carbon_data.get("carbonIntensity"),
    #                             "datetime": pd.to_datetime(latest_datetime_str),
    #                             "updatedAt": pd.to_datetime(carbon_data.get("updatedAt")),
    #                             "createdAt": pd.to_datetime(carbon_data.get("createdAt")),
    #                             "emissionFactorType": carbon_data.get("emissionFactorType"),
    #                             "isEstimated": carbon_data.get("isEstimated"),
    #                             "estimationMethod": carbon_data.get("estimationMethod")
    #                         }
    #                         df_history = pd.concat([df_history, pd.DataFrame([latest_row])], ignore_index=True)
    #                 # After appending latest row
    #                 df_history = df_history.sort_values("datetime")
    #                 df_history = df_history.drop(columns=["datetime_rounded"], errors="ignore")

    #                 # Plot with Plotly
    #                 fig = px.line(
    #                     df_history,
    #                     x='datetime',
    #                     y='carbonIntensity',
    #                     title="15-Minute Carbon Intensity (FR)",
    #                     labels={"datetime": "Time", "carbonIntensity": "gCO₂eq/kWh"},
    #                     markers=True
    #                 )

    #                 fig.update_layout(
    #                     xaxis_title="Time",
    #                     yaxis_title="Carbon Intensity (gCO₂eq/kWh)",
    #                     template="plotly_white",
    #                     xaxis=dict(
    #                         tickformat="%H:%M",
    #                         tickangle=45
    #                     )
    #                 )

    #                 # Optional: highlight the latest point
    #                 fig.add_scatter(
    #                     x=[latest_row["datetime"]],
    #                     y=[latest_row["carbonIntensity"]],
    #                     mode="markers+text",
    #                     marker=dict(color="red", size=10),
    #                     text=["Latest"],
    #                     textposition="top center",
    #                     name="Latest"
    #                 )

    #                 st.plotly_chart(fig, use_container_width=True)
    #             except requests.RequestException as e:
    #                 st.error(f"❌ Failed to fetch carbon intensity history: {e}")
        
    #         global_total_co2_kg = 0  # Accumulator for all resources

    #         for resource_type in resource_types:
    #             st.markdown(f"### 🔎 Resource: {resource_type.upper()}")

    #             # Fetch energy data
    #             try:
    #                 response = requests.get(f"{FASTAPI_BASE_URL}/ecofloc/{resource_type}")
    #                 response.raise_for_status()
    #                 df = pd.DataFrame(response.json())
    #             except Exception as e:
    #                 st.error(f"Error fetching data for {resource_type}: {e}")
    #                 continue

    #             # Ensure required columns
    #             required = ['timestamp', 'metric_value', 'metric_name', 'process_name']
    #             if not all(col in df.columns for col in required):
    #                 st.warning(f"Skipping {resource_type} due to missing columns.")
    #                 continue

    #             df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    #             df['metric_value'] = pd.to_numeric(df['metric_value'], errors='coerce')
    #             df.dropna(subset=['timestamp', 'metric_value'], inplace=True)
    #             df['process_name'] = df['process_name'].astype(str)

    #             # Filter for total energy metrics
    #             energy_df = df[df['metric_name'].str.lower().str.contains("total energy")]
    #             if energy_df.empty:
    #                 st.info(f"No total energy data for {resource_type}.")
    #                 continue

    #             # Convert to kWh and compute CO₂
    #             energy_df['energy_kwh'] = energy_df['metric_value'] / 3_600_000
    #             energy_df['co2_g'] = energy_df['energy_kwh'] * carbon_intensity
    #             energy_df['co2_kg'] = energy_df['co2_g'] / 1000

    #             # Total CO₂ per process
    #             carbon_summary = (
    #                 energy_df.groupby("process_name")[["co2_kg", "energy_kwh"]]
    #                 .sum()
    #                 .reset_index()
    #                 .sort_values(by="co2_kg", ascending=False)
    #             )

                

    #             # Total CO₂ today
    #             total_co2_kg = carbon_summary['co2_kg'].sum()
    #             global_total_co2_kg += total_co2_kg

                          
    #             energy_kwh_total = pd.to_numeric(energy_df["energy_kwh"], errors="coerce").sum()
    #             energy_kwh_total = float(energy_kwh_total) if not pd.isna(energy_kwh_total) else 0.0

    #             # Get last stored value for this resource
    #             resp = requests.get(f"{FASTAPI_BASE_URL}/scope2/last/{resource_type}")
    #             last_value = resp.json().get("co2_kg", 0.0)

    #             increment = float(total_co2_kg) - float(last_value)
    #             for _, row in carbon_summary.iterrows():
    #                 if increment > 0:

    #                     # Save only today's total for this resource type
    #                     payload = {
    #                         "process_name": row["process_name"],
    #                         "resource_type": resource_type,
    #                         "energy_kwh": float(energy_kwh_total),
    #                         "co2_kg": float(total_co2_kg),
    #                         "carbon_intensity": float(carbon_intensity)
    #                     }

    #                     requests.post(f"{FASTAPI_BASE_URL}/scope2", json=payload).raise_for_status()
                   

    #             st.metric(f"🌫️ Total CO₂ Emissions Today ({resource_type.upper()})", f"{total_co2_kg:.8f} kg")

    #             # 📊 Bar Plot: CO₂ by process
    #             fig_bar = px.bar(
    #                 carbon_summary,
    #                 x="process_name",
    #                 y="co2_kg",
    #                 labels={"process_name": "Process", "co2_kg": "CO₂ (kg)"},
    #                 title=f"{resource_type.upper()} - CO₂ Emissions by Process",
    #             )

    #             # 📈 Line Plot: CO₂ over time
    #             fig_line = px.line(
    #                 energy_df,
    #                 x="timestamp",
    #                 y="co2_kg",
    #                 color="process_name",
    #                 labels={"timestamp": "Time", "co2_kg": "CO₂ (kg)", "process_name": "Process"},
    #                 title=f"{resource_type.upper()} - CO₂ Over Time"
    #             )
    #             fig_line.update_layout(height=500)

    #             col1, col2 = st.columns(2)

    #             with col1:
    #                 st.subheader(f"📊 CO₂ by Process ({resource_type.upper()})")
    #                 st.plotly_chart(fig_bar, use_container_width=True, key=f"{resource_type}_co2_bar")

    #             with col2:
    #                 st.subheader("📈 CO₂ Over Time")
    #                 st.plotly_chart(fig_line, use_container_width=True, key=f"{resource_type}_co2_line")

    #             # 🏭 Table: Top 5 emitters
    #             top5 = carbon_summary.head(5).copy()
    #             st.subheader(f"🏭 Top 5 CO₂ Emitters ({resource_type.upper()})")
    #             st.table(top5[['process_name', 'co2_kg', 'energy_kwh']])

    # except Exception as e:
    #     st.error(f"Failed to load carbon footprint: {e}")

   
    st.title("⚡ Live Carbon Footprint per Resource")

    # Fetch latest carbon intensity
    try:
        response = requests.get(f"{FASTAPI_BASE_URL}/carbon-intensity/last?zone=FR")
        response.raise_for_status()
        carbon_data = response.json()
        carbon_intensity = carbon_data.get("carbonIntensity")
        updated_at = carbon_data.get("updatedAt", "N/A")

        if carbon_intensity is None:
            st.error("Carbon intensity data is not available.")
            st.stop()

        st.subheader("Live Carbon Intensity")
        st.metric("Carbon Intensity", f"{carbon_intensity} gCO₂eq/kWh", delta=None)
        st.caption(f"Updated at: {updated_at}")

    except Exception as e:
        st.error(f"Failed to fetch carbon intensity: {e}")
        st.stop()

    # Global CO₂ accumulator
    global_total_co2_kg = 0

    # Loop over all resources
    for resource_type in resource_types:
        st.markdown(f"### 🔎 Resource: {resource_type.upper()}")

        try:
            # Fetch Ecofloc data
            response = requests.get(f"{FASTAPI_BASE_URL}/ecofloc/{resource_type}")
            response.raise_for_status()
            df = pd.DataFrame(response.json())
        except Exception as e:
            st.error(f"Error fetching data for {resource_type}: {e}")
            continue

        required_cols = ['timestamp', 'metric_value', 'metric_name', 'process_name', 'pid']
        if not all(col in df.columns for col in required_cols):
            st.warning(f"Skipping {resource_type} due to missing columns")
            continue

        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df['metric_value'] = pd.to_numeric(df['metric_value'], errors='coerce')
        df.dropna(subset=['timestamp', 'metric_value'], inplace=True)
        df['process_name'] = df['process_name'].astype(str)

        # Filter total energy metrics
        energy_df = df[df['metric_name'].str.lower().str.contains("total energy")]
        if energy_df.empty:
            st.info(f"No total energy data for {resource_type}.")
            continue

        # Energy → kWh and CO₂ conversion
        energy_df['energy_kwh'] = energy_df['metric_value'] / 3_600_000
        energy_df['co2_g'] = energy_df['energy_kwh'] * carbon_intensity
        energy_df['co2_kg'] = energy_df['co2_g'] / 1000

        # Group by process & PID
        carbon_summary = (
            energy_df.groupby(["process_name", "pid"])[["co2_kg", "energy_kwh"]]
            .sum()
            .reset_index()
            .sort_values(by="co2_kg", ascending=False)
        )

        total_co2_kg = carbon_summary['co2_kg'].sum()
        global_total_co2_kg += total_co2_kg

        st.metric(f"🌫️ Total CO₂ Emissions Today ({resource_type.upper()})", f"{total_co2_kg:.8f} kg")

        # Bar chart: CO₂ by process
        fig_bar = px.bar(
            carbon_summary,
            x="process_name",
            y="co2_kg",
            color="process_name",
            labels={"process_name": "Process", "co2_kg": "CO₂ (kg)"},
            title=f"{resource_type.upper()} - CO₂ by Process",
        )

        # Line chart: CO₂ over time per process
        fig_line = px.line(
            energy_df,
            x="timestamp",
            y="co2_kg",
            color="process_name",
            labels={"timestamp": "Time", "co2_kg": "CO₂ (kg)", "process_name": "Process"},
            title=f"{resource_type.upper()} - CO₂ Over Time"
        )
        fig_line.update_layout(height=500)

        # Display charts with unique keys
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(fig_bar, use_container_width=True, key=f"{resource_type}_bar_{datetime.now().timestamp()}")
        with col2:
            st.plotly_chart(fig_line, use_container_width=True, key=f"{resource_type}_line_{datetime.now().timestamp()}")

        # Top 5 emitters
        top5 = carbon_summary.head(5).copy()
        st.subheader(f"🏭 Top 5 CO₂ Emitters ({resource_type.upper()})")
        st.table(top5[['process_name', 'pid', 'co2_kg', 'energy_kwh']])

    st.markdown(f"## 🌍 Total CO₂ Today Across All Resources: {global_total_co2_kg:.8f} kg")
    #render_tab3()
with tab4:

    st.title("Carbon Footprint Summary")
    cols1 , col2 , cols3 = st.columns(3)
    with cols1:
        st.subheader("Scope 3 Value")

        def sum_impacts(*args):

            def safe_float(val):
                try:
                    return float(val)
                except (TypeError, ValueError):
                    return 0.0

            total_impacts = {}

            for data in args:
                if not data:
                    continue

                # Get impacts dict
                impacts = data.get("impacts")
                
                # If no "impacts" key, try to get root-level impact keys (like "gwp" or "GWP")
                if not impacts:
                    impacts = {}
                    for key in ["gwp", "GWP", "pe", "PE", "adp", "ADP"]:
                        if key in data:
                            impacts[key.lower()] = data[key]

                for impact_type, impact_vals in impacts.items():
                    impact_type = impact_type.lower()
                    if impact_type not in total_impacts:
                        total_impacts[impact_type] = {"manufacture": 0.0, "use": 0.0, "unit": impact_vals.get("unit", "") if isinstance(impact_vals, dict) else ""}

                    # If impact_vals is dict with manufacture/use
                    if isinstance(impact_vals, dict):
                        manufacture_val = safe_float(impact_vals.get("manufacture", 0))
                        use_val = safe_float(impact_vals.get("use", 0))
                    else:
                        # If it's a direct number or string, assume manufacture only
                        manufacture_val = safe_float(impact_vals)
                        use_val = 0.0

                    total_impacts[impact_type]["manufacture"] += manufacture_val
                    total_impacts[impact_type]["use"] += use_val

            return total_impacts

            # --- Sum all impacts ---
        def safe_get(var_name):
            return globals().get(var_name) or locals().get(var_name) or None

        components = [cpu_data, ram_data, case_data, ssd_data, motherboard_impacts]

        for optional_var in ['hdd_data', 'gpu_data']:
            val = safe_get(optional_var)
            if val is not None:
                components.append(val)


        total_impacts = sum_impacts(*components)
        
        def get_total_scope3():
            url = f"{FASTAPI_BASE_URL}/scope3/total"
            try:
                response = requests.get(url)
                response.raise_for_status()
                result = response.json()
                return result.get("total_scope3_gwp", 0.0)
            except Exception as e:
                st.error(f"Error fetching total Scope 3: {e}")
                return 0.0

        # Display in Streamlit
        total_scope3 = get_total_scope3()

        


        st.subheader("Summary of Total Impacts")
        for impact_type, vals in total_impacts.items():
            manufacture = vals["manufacture"]
            use = vals["use"]
            unit = vals["unit"]
            st.write(f"**{impact_type.upper()}**: Manufacture = {manufacture} {unit}")


    with col2:
        st.subheader("Scope 2 Value")
        st.subheader("🌍 Total CO₂ (Live Sum)")
        st.metric("All Resources", f"{global_total_co2_kg:.8f} kg")


    with cols3:
        st.subheader("Carbon Emissions Total")
        total_manufacture_emissions = sum(vals["manufacture"] for vals in total_impacts.values() if "kgCO2eq" in vals["unit"])
        combined_total_co2 = total_manufacture_emissions + global_total_co2_kg
        st.subheader("🌍 Combined Carbon Footprint Summary")
        st.metric(f"💯 **Total Estimated CO₂ Footprint:**",f"{combined_total_co2:.8f} kg CO₂eq")



    