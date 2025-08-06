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

    # Save in session state
    st.session_state["motherboard_data"] = motherboard_data

    # --- Display in Columns ---
    left, middle, right = st.columns(3)
    with left:
        st.metric("GWP", f"{total_gwp:.2f} kgCO₂eq")
    with middle:
        st.metric("ADP", f"{total_adp:.5f} kgSbeq")
    with right:
        st.metric("PE", f"{total_pe:.2f} MJ")

    detected_GPU = data.get("gpus")

    st.subheader("Boavizta GPU Calculations", divider=True, help="Based on formula found in the following article: https://hal.science/hal-04643414v1/document")

    gpus = [gpu for gpu in detected_GPU]  # Populate from /system-info

    if gpus:
        selected_gpu_index = st.selectbox("Select GPU:", range(len(gpus)), format_func=lambda x: f"GPU {x + 1}",  key="gpu_selectbox")
        selected_gpu = gpus[selected_gpu_index]
        gpu_brand = st.text_input("GPU Model", value=selected_gpu)

        # Try to auto-detect specs
        database = GPUDatabase.default()
        try:
            spec = database.search(gpu_brand)
            die_size = spec.die_size_mm2
            ram_size = spec.memory_size_gb
        except KeyError:
            st.warning(f"Specs for {gpu_brand} not found. Please enter manually.")
            die_size = 100.0
            ram_size = 8

        die_size_input = st.number_input("Die Size (mm²)", value=die_size, format="%.2f")
        ram_size_input = st.number_input("RAM Size (GB)", value=ram_size)

        
        payload = {
            "model" : selected_gpu,
            "die_size_mm2": die_size_input,
            "ram_size_gb": ram_size_input
        }
        try:
            response = requests.post(f"{FASTAPI_BASE_URL}/GPU-Calc", json=payload)
            response.raise_for_status()
            data = response.json()

        
            st.markdown(f"**GWP:** {data['gwp']} kgCO₂eq")
            st.markdown(f"**ADP:** {data['adp']} kgSbeq")
            st.markdown(f"**PE:** {data['pe']} MJ")

        except requests.RequestException as e:
            st.error(f"Failed to calculate GPU impact: {str(e)}")
    else:
        st.info("No GPUs detected in the system information.")

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
#     st.header("🔄 Real-Time System Monitoring")


#     st.title("Ecofloc CPU Energy Dashboard – Today")

#     # Get today's data
#     try:
#         response = requests.get(f"{FASTAPI_BASE_URL}/ecofloc/cpu")
#         response.raise_for_status()
#         data = response.json()
#         df = pd.DataFrame(data)
#     except Exception as e:
#         st.error(f"Error fetching Ecofloc CPU data: {e}")
#         st.stop()

#     # Clean + filter
#     if "timestamp" in df.columns:

#         df['timestamp'] = pd.to_datetime(df['timestamp'])
#         df['metric_value'] = pd.to_numeric(df['metric_value'], errors='coerce')
#         df.dropna(subset=['metric_value', 'timestamp'], inplace=True)
#     else:
#         st.error("Missing 'timestamp' in data")
#         st.stop()

#     # Filter for "Total Energy" rows only
#     energy_df = df[df["metric_name"].str.lower().str.contains("total energy")].copy()

#     # ✅ Total energy consumed today
#     total_energy_today = energy_df["metric_value"].sum()

#     # ✅ Top 5 producers by process name
#     top5 = (
#         energy_df.groupby("process_name")["metric_value"]
#         .sum()
#         .sort_values(ascending=False)
#         .head(5)
#         .reset_index()
#     )

#     # Display total energy and top 5
#     col1, col2 = st.columns(2)

#     with col1:
#         st.metric("🔋 Total Energy Consumed Today", f"{total_energy_today:.2f} J")
#         st.subheader("Top 5 Energy Producers Today")
#         fig_top5 = px.bar(
#             top5,
#             x="process_name",
#             y="metric_value",
#             labels={"process_name": "Process", "metric_value": "Total Energy (J)"},
#             title="Top 5 Energy Consumers"
#         )
#         st.plotly_chart(fig_top5, use_container_width=True)

#     # (Optional) Line plot of energy over time
#     st.subheader("Energy Consumption Over Time (Today)")
#     fig_line = px.line(
#         energy_df,
#         x="timestamp",
#         y="metric_value",
#         color="process_name",
#         labels={
#             "timestamp": "Timestamp",
#             "metric_value": "Energy (J)",
#             "process_name": "Process"
#         },
#         title="Process Energy Consumption Over Time"
#     )
#     fig_line.update_layout(height=500)
#     st.plotly_chart(fig_line, use_container_width=True)
#     st.markdown("---")



#     st.header("🧾 Top Running Processes")
#     st_autorefresh(interval=5000)
#     try:
       
#         response = requests.get(f"{FASTAPI_BASE_URL}/top-processes")
#         processes = response.json()
#         df = pd.DataFrame(processes)
#         df = df.rename(columns={
#             'pid': 'PID',
#             'name': 'Name',
#             'cpu_percent': 'CPU (%)',
#             'memory_percent': 'RAM (%)'
#         })
#         st.dataframe(df)
#     except Exception as e:
#         st.error(f"Error loading processes: {e}")

#     st.subheader("EcoFloc Monitoring for Top Processes")

#     # User inputs
#     limit = st.slider("Number of Top Processes", 1, 20, 5)
#     interval = st.number_input("Sampling Interval (ms)", min_value=100, value=1000, step=100)
#     duration = st.number_input("Duration (s)", min_value=1, value=5, step=1)
#     resources = st.multiselect("Resources to Monitor", ["cpu", "ram", "gpu", "sd", "nic"], default=["cpu", "ram"])

#     if st.button("Run EcoFloc Monitor"):
#         with st.spinner("Running EcoFloc..."):
#             try:
#                 query_params = {
#                     "limit": limit,
#                     "interval": interval,
#                     "duration": duration,
#                     "resources": ",".join(resources)
#                 }

#                 response = requests.get(f"{FASTAPI_BASE_URL}/ecofloc/monitor", params=query_params)
#                 data = response.json().get("results", [])

#                 if data:
#                     df = pd.DataFrame(data)
#                     st.success("Monitoring complete.")
#                     st.dataframe(df[["pid", "name", "cpu_percent", "memory_percent", "resource"]])

#                     with st.expander("Raw Output Logs"):
#                         for row in data:
#                             st.text(f"PID {row['pid']} ({row['name']}) - {row['resource']}")
#                             st.code(row.get("ecofloc_output", "No output"))

#                 else:
#                     st.warning("No results returned.")

#             except Exception as e:
#                 st.error(f"Failed to fetch data: {e}")


# st.title("EcoFloc Monitor")

# limit = st.slider("Top Processes", 1, 20, 5)
# interval = st.number_input("Interval (ms)", 100, 5000, 1000)
# duration = st.number_input("Duration (s)", 1, 30, 5)
# resources = st.multiselect("Resources", ["cpu", "ram", "gpu", "sd", "nic"], default=["cpu", "ram"])

# if st.button("Run Monitoring"):
#     with st.spinner("Running..."):
#         try:
#             response = requests.get(
#                 f"{FASTAPI_BASE_URL}/ecofloc/monitor",
#                 params={
#                     "limit": limit,
#                     "interval": interval,
#                     "duration": duration,
#                     "resources": ",".join(resources)
#                 }
#             )
#             result = response.json()

#             if "results" in result:
#                 df = pd.DataFrame(result["results"])
#                 st.success("Monitoring completed.")
#                 st.dataframe(df[["pid", "name", "resource"]])

#                 with st.expander("Raw Output"):
#                     for r in result["results"]:
#                         st.text(f"PID: {r['pid']} ({r['name']}) - {r['resource']}")
#                         st.code(r.get("output", r.get("error", "No data")))
#             else:
#                 st.error(result.get("error", "Unknown error."))

#         except Exception as e:
#             st.error(f"Failed to fetch: {e}")

# try:
#     response = requests.get(f"{FASTAPI_BASE_URL}/ecofloc_results")
#     response.raise_for_status()
#     db_data = response.json()

#     if db_data:
#         df_db = pd.DataFrame(db_data)
#         st.dataframe(df_db)

#         # Optional: plot some meaningful chart if you want
#         if 'value' in df_db.columns and 'resource' in df_db.columns:
#             fig = px.bar(df_db, x="resource", y="value", color="resource", title="Ecofloc Metrics by Resource")
#             st.plotly_chart(fig)
#     else:
#         st.info("No Ecofloc DB data found.")
# except Exception as e:
#     st.error(f"Error fetching Ecofloc DB data: {e}")

# # Display Ecofloc Cpu results :
# try: 
#     response = requests.get(f"{FASTAPI_BASE_URL}/ecofloc/cpu")
#     cpu_data = response.json()
#     df_cpu = pd.DataFrame(cpu_data)
#     st.dataframe(df_cpu)
# except Exception as e:
#     st.error(f"Error fetching Ecofloc CPU data: {e}")

#     # Fetch data
# try:
#     response = requests.get(f"{FASTAPI_BASE_URL}/ecofloc/cpu")
#     response.raise_for_status()
#     cpu_data = response.json()
#     df_cpu = pd.DataFrame(cpu_data)
# except Exception as e:
#     st.error(f"Error fetching Ecofloc CPU data: {e}")
#     st.stop()


# # --- DATA CLEANUP to avoid pyarrow serialization errors ---

# # # Ensure metric_value is numeric
# # if 'metric_value' in df_cpu.columns:
# #     df_cpu['metric_value'] = pd.to_numeric(df_cpu['metric_value'], errors='coerce')

# # # Ensure timestamp is datetime
# # if 'timestamp' in df_cpu.columns:
# #     df_cpu['timestamp'] = pd.to_datetime(df_cpu['timestamp'], errors='coerce')

# # # If any other columns are object but should be strings, cast them explicitly
# # for col in df_cpu.select_dtypes(include='object').columns:
# #     if col != 'timestamp':  # timestamp already handled
# #         df_cpu[col] = df_cpu[col].astype(str)

# # # Filter rows with missing critical data after conversion (optional)
# # df_cpu = df_cpu.dropna(subset=['metric_value', 'timestamp', 'pid'])

# # # Filter to energy consumption rows (assuming metric_name contains 'energy')
# # energy_df = df_cpu[df_cpu["metric_name"].str.lower().str.contains("energy")].copy()

# # # Accumulate energy consumption per PID
# # energy_sum_per_pid = energy_df.groupby("pid")["metric_value"].sum().reset_index()
# # energy_sum_per_pid = energy_sum_per_pid.sort_values(by="metric_value", ascending=False)

# # # Create 3 columns for display
# # col1, col2, col3 = st.columns(3)

# # with col1:
    
# #     st.subheader("Ecofloc CPU Data")
# #     st.dataframe(df_cpu)

# # with col2:
# #     st.subheader("Total Energy Consumption per PID")
# #     fig_bar = px.bar(
# #         energy_sum_per_pid,
# #         x="pid",
# #         y="metric_value",
# #         labels={"pid": "PID", "metric_value": "Total Energy Consumption"},
# #         title="Total Energy Consumption per PID"
# #     )
# #     st.plotly_chart(fig_bar, use_container_width=True)

# # with col3:
# #     st.subheader("Energy Consumption Evolution Over Time")
# #     fig_line = px.line(
# #         energy_df,
# #         x='timestamp',
# #         y='metric_value',
# #         color='pid',
# #         labels={"timestamp": "Timestamp", "metric_value": "Energy Consumption", "pid": "PID"},
# #         title="PID Energy Consumption Over Time"
# #     )
# #     st.plotly_chart(fig_line, use_container_width=True)

# # Ensure types
# df_cpu['timestamp'] = pd.to_datetime(df_cpu['timestamp'])
# df_cpu['metric_value'] = pd.to_numeric(df_cpu['metric_value'], errors='coerce')
# df_cpu.dropna(subset=['timestamp', 'metric_value'], inplace=True)

# # Filter for 'Total Energy' metric only
# energy_df = df_cpu[df_cpu["metric_name"].str.lower().str.contains("total energy")]

# # Group by process_name to sum total energy
# total_energy = energy_df.groupby("process_name")["metric_value"].sum().reset_index()
# total_energy = total_energy.sort_values(by="metric_value", ascending=False)

# # Layout
# col1, col2 = st.columns([1, 1])
# with col1:
#     st.subheader("Raw Ecofloc CPU Data")
#     st.dataframe(df_cpu)

# with col2:
#     st.subheader("Total Energy per Process")
#     fig_bar = px.bar(
#         total_energy,
#         x="process_name",
#         y="metric_value",
#         labels={"process_name": "Process", "metric_value": "Total Energy"},
#         title="Total Energy Consumption (Last 24h)"
#     )
#     st.plotly_chart(fig_bar, use_container_width=True)

# # Full-width time series
# st.subheader("Energy Consumption Evolution Over Time")
# fig_line = px.line(
#     energy_df,
#     x="timestamp",
#     y="metric_value",
#     color="process_name",
#     labels={
#         "timestamp": "Timestamp",
#         "metric_value": "Energy Consumption",
#         "process_name": "Process"
#     },
#     title="Process Energy Consumption Over Time"
# )
# fig_line.update_layout(height=500)
# st.plotly_chart(fig_line, use_container_width=True)



#     # Fetch data
# try:
#     response = requests.get(f"{FASTAPI_BASE_URL}/ecofloc/ram")
#     response.raise_for_status()
#     ram_data = response.json()
#     df_ram = pd.DataFrame(ram_data)
# except Exception as e:
#     st.error(f"Error fetching Ecofloc CPU data: {e}")
#     st.stop()

# # Ensure types
# df_ram['timestamp'] = pd.to_datetime(df_ram['timestamp'])
# df_ram['metric_value'] = pd.to_numeric(df_ram['metric_value'], errors='coerce')
# df_ram.dropna(subset=['timestamp', 'metric_value'], inplace=True)

# # Filter for 'Total Energy' metric only
# energy_ram_df = df_ram[df_ram["metric_name"].str.lower().str.contains("total energy")]

# # Group by process_name to sum total energy
# total_energy_ram = energy_ram_df.groupby("process_name")["metric_value"].sum().reset_index()
# total_energy_ram = total_energy_ram.sort_values(by="metric_value", ascending=False)

# # Layout
# col1, col2 = st.columns([1, 1])
# with col1:
#     st.subheader("Raw Ecofloc CPU Data")
#     st.dataframe(df_ram)

# with col2:
#     st.subheader("Total Energy per Process")
#     fig_bar_ram = px.bar(
#         total_energy_ram,
#         x="process_name",
#         y="metric_value",
#         labels={"process_name": "Process", "metric_value": "Total Energy"},
#         title="Total Energy Consumption (Last 24h)"
#     )
#     st.plotly_chart(fig_bar_ram, use_container_width=True)

# # Full-width time series
# st.subheader("Energy Consumption Evolution Over Time")
# fig_line_ram = px.line(
#     energy_ram_df,
#     x="timestamp",
#     y="metric_value",
#     color="process_name",
#     labels={
#         "timestamp": "Timestamp",
#         "metric_value": "Energy Consumption",
#         "process_name": "Process"
#     },
#     title="Process Energy Consumption Over Time"
# )
# fig_line.update_layout(height=500)
# st.plotly_chart(fig_line_ram, use_container_width=True)

    # st_autorefresh(interval=10000, key="refresh")



    # try:
    #     response = requests.get(f"{FASTAPI_BASE_URL}/ecofloc/cpu")
    #     response.raise_for_status()
    #     data = response.json()
    #     df_cpu = pd.DataFrame(data)
    # except Exception as e:
    #     st.error(f"Error fetching CPU data: {e}")
    #     st.stop()

    # # Check if necessary columns exist
    # required = ['timestamp', 'metric_value', 'metric_name', 'process_name']
    # missing = [col for col in required if col not in df_cpu.columns]
    # if missing:
    #     st.error(f"Missing expected columns: {missing}")
    #     st.write("Available columns:", df_cpu.columns.tolist())
    #     st.stop()

    # # Type conversion
    # df_cpu['timestamp'] = pd.to_datetime(df_cpu['timestamp'], errors='coerce')
    # df_cpu['metric_value'] = pd.to_numeric(df_cpu['metric_value'], errors='coerce')
    # df_cpu.dropna(subset=["timestamp", "metric_value"], inplace=True)

    # # Fix Arrow error (optional)
    # for col in df_cpu.select_dtypes(include="object").columns:
    #     df_cpu[col] = df_cpu[col].astype(str)

    # st.subheader("🔍 Raw Ecofloc CPU Data")
    # st.dataframe(df_cpu)
    # energy_df = df_cpu[df_cpu["metric_name"].str.lower().str.contains("total energy")]
    # st.subheader("⚡ Total Energy per Process (Today)")

    # total_energy = (
    #     energy_df.groupby("process_name")["metric_value"]
    #     .sum()
    #     .reset_index()
    #     .sort_values(by="metric_value", ascending=False)
    # )

    # fig_bar = px.bar(
    #     total_energy,
    #     x="process_name",
    #     y="metric_value",
    #     labels={"process_name": "Process", "metric_value": "Total Energy (Joules)"},
    #     title="Total Energy by Process (Midnight to Now)",
    # )
    # st.plotly_chart(fig_bar, use_container_width=True)

    # st.subheader("📈 Energy Consumption Over Time")

    # fig_line = px.line(
    #     energy_df,
    #     x="timestamp",
    #     y="metric_value",
    #     color="process_name",
    #     labels={
    #         "timestamp": "Time",
    #         "metric_value": "Energy (Joules)",
    #         "process_name": "Process"
    #     },
    #     title="Energy Consumption per Process Over Time"
    # )

    # fig_line.update_layout(height=500)
    # st.plotly_chart(fig_line, use_container_width=True)

    # top5 = total_energy.head(5)
    # st.metric("Total Energy (All Processes)", f"{total_energy['metric_value'].sum():.2f} J")

    # st.subheader("🏭 Top 5 Energy Consumers")
    # st.table(top5)


    #     # --- Clean & filter data ---
    # df_cpu['timestamp'] = pd.to_datetime(df_cpu['timestamp'], errors='coerce')
    # df_cpu['metric_value'] = pd.to_numeric(df_cpu['metric_value'], errors='coerce')
    # df_cpu.dropna(subset=["timestamp", "metric_value"], inplace=True)

    # # Avoid Arrow error with mixed types
    # for col in df_cpu.select_dtypes(include="object").columns:
    #     df_cpu[col] = df_cpu[col].astype(str)

    # # ✅ Filter for today's data (00:00 to now)
    # now = datetime.now()
    # start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    # df_cpu = df_cpu[df_cpu['timestamp'] >= start_of_day]

    # # --- Show raw table ---
    # st.subheader("🔍 Raw Ecofloc CPU Data (Today)")
    # st.dataframe(df_cpu)

    # # --- Filter to only energy-related metrics ---
    # energy_df = df_cpu[df_cpu["metric_name"].str.lower().str.contains("total energy")]

    # # --- Total energy per process ---
    # st.subheader("⚡ Total Energy per Process (Today)")
    # total_energy = (
    #     energy_df.groupby("process_name")["metric_value"]
    #     .sum()
    #     .reset_index()
    #     .sort_values(by="metric_value", ascending=False)
    # )

    # fig_bar = px.bar(
    #     total_energy,
    #     x="process_name",
    #     y="metric_value",
    #     labels={"process_name": "Process", "metric_value": "Total Energy (Joules)"},
    #     title="Total Energy by Process (00:00 → Now)",
    # )
    # st.plotly_chart(fig_bar, use_container_width=True)

    # # --- Energy over time ---
    # st.subheader("📈 Energy Consumption Over Time (Today)")

    # fig_line = px.line(
    #     energy_df,
    #     x="timestamp",
    #     y="metric_value",
    #     color="process_name",
    #     labels={
    #         "timestamp": "Time",
    #         "metric_value": "Energy (Joules)",
    #         "process_name": "Process"
    #     },
    #     title="Energy Consumption per Process Over Time"
    # )
    # fig_line.update_layout(height=500)
    # st.plotly_chart(fig_line, use_container_width=True)

    # # --- Metrics ---
    # st.metric("🔋 Total Energy (All Processes)", f"{total_energy['metric_value'].sum():.2f} J")

    # # --- Top 5 Consumers ---
    # top5 = total_energy.head(5)
    # st.subheader("🏭 Top 5 Energy Consumers Today")
    # st.table(top5)

        # Auto-refresh every 10 seconds
    st_autorefresh(interval=10000, key="auto_refresh")

    # resource_type = st.selectbox("Select Resource Type", ["cpu", "ram", "gpu", "sd", "nic"])

    # # Fetch data
    # try:
    #     response = requests.get(f"{FASTAPI_BASE_URL}/ecofloc/{resource_type}")
    #     response.raise_for_status()
    #     data = response.json()
    #     df = pd.DataFrame(data)
    # except Exception as e:
    #     st.error(f"Error fetching data: {e}")
    #     st.stop()

    # # Validate and clean data
    # required = ['timestamp', 'metric_value', 'metric_name', 'process_name']
    # missing = [col for col in required if col not in df.columns]
    # if missing:
    #     st.error(f"Missing expected columns: {missing}")
    #     st.write("Available columns:", df.columns.tolist())
    #     st.stop()

    # df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    # df['metric_value'] = pd.to_numeric(df['metric_value'], errors='coerce')
    # df.dropna(subset=['timestamp', 'metric_value'], inplace=True)

    # for col in df.select_dtypes(include="object").columns:
    #     df[col] = df[col].astype(str)

    # # Filter to total energy only
    # energy_df = df[df['metric_name'].str.lower().str.contains("total energy")]

    # # Total energy consumed today
    # total_energy = (
    #     energy_df.groupby("process_name")["metric_value"]
    #     .sum()
    #     .reset_index()
    #     .sort_values(by="metric_value", ascending=False)
    # )

    # # Layout: bar + line plots
    # col1, col2 = st.columns(2)

    # with col1:
    #     st.subheader(f"⚡ Total Energy per Process ({resource_type.upper()})")
    #     fig_bar = px.bar(
    #         total_energy,
    #         x="process_name",
    #         y="metric_value",
    #         labels={"process_name": "Process", "metric_value": "Energy (J)"},
    #         title="Energy Consumption by Process"
    #     )
    #     #st.plotly_chart(fig_bar, use_container_width=True, key=f"{resource_type}_bar")

    # with col2:
    #     st.subheader("📈 Energy Over Time")
    #     fig_line = px.line(
    #         energy_df,
    #         x="timestamp",
    #         y="metric_value",
    #         color="process_name",
    #         labels={"timestamp": "Time", "metric_value": "Energy (J)", "process_name": "Process"},
    #         title="Energy Usage Over Time"
    #     )
    #     fig_line.update_layout(height=500)
    #   #  st.plotly_chart(fig_line, use_container_width=True, key=f"{resource_type}_line")

    # # Metrics summary
    # st.metric("🔋 Total Energy Today", f"{total_energy['metric_value'].sum():.2f} J")
    # top5 = total_energy.head(5)
    # st.subheader("🏭 Top 5 Energy Consumers")
    # st.table(top5)


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
        st.metric(f"🔋 Total Energy Today ({resource_type.upper()})", f"{total_energy_sum_j:.2f} J / {total_energy_sum_kwh:.2f} kWh")

        top5 = total_energy.head(5).copy()
        top5['metric_value_kwh'] = top5['metric_value'] / 3_600_000
        st.subheader(f"🏭 Top 5 Energy Consumers ({resource_type.upper()})")
        st.table(top5[['process_name', 'metric_value', 'metric_value_kwh']])


        st.markdown("---")

with tab3:
    st.title("Carbon Footprint Dashboard")

    try:
        # Fetch latest carbon intensity
        response = requests.get(f"{FASTAPI_BASE_URL}/carbon-intensity/last?zone=FR")
        response.raise_for_status()
        carbon_data = response.json()

        carbon_intensity = carbon_data.get("carbonIntensity")
        updated_at = carbon_data.get("updatedAt", "N/A")

        if carbon_intensity is None:
            st.error("Carbon intensity data is not available.")
        else:
            # st.subheader("Latest Stored Carbon Intensity")
            # st.metric("Carbon Intensity", f"{carbon_intensity} gCO₂eq/kWh")
            # st.caption(f"Updated at: {updated_at}")

            # Fetch carbon intensity history for line plot
            try:
                response_history = requests.get(f"{FASTAPI_BASE_URL}/carbon-intensity/history?zone=FR")
                response_history.raise_for_status()
                history_data = response_history.json()

                # Build DataFrame
                df_history = pd.DataFrame(history_data)
                df_history['updatedAt'] = pd.to_datetime(df_history['updatedAt'], errors='coerce')
                df_history['carbonIntensity'] = pd.to_numeric(df_history['carbonIntensity'], errors='coerce')
                df_history.dropna(subset=['updatedAt', 'carbonIntensity'], inplace=True)
                df_history = df_history.sort_values('updatedAt')

                # Create line plot
                fig_line = px.line(
                    df_history,
                    x='updatedAt',
                    y='carbonIntensity',
                    labels={'updatedAt': 'Updated Time', 'carbonIntensity': 'gCO₂/kWh'},
                    title='🧭 Carbon Intensity Over Time',
                    height=350
                )

                # Display metric + line plot side-by-side
                col1, col2 = st.columns([1, 3])

                with col1:
                    st.subheader("Live Carbon Intensity")
                    st.metric("Carbon Intensity", f"{carbon_intensity} gCO₂eq/kWh")
                    st.caption(f"Updated at: {updated_at}")

                with col2:
                    st.plotly_chart(fig_line, use_container_width=True)

            except Exception as e:
                st.warning(f"Could not load carbon intensity history: {e}")
        
            global_total_co2_kg = 0  # Accumulator for all resources

            for resource_type in resource_types:
                st.markdown(f"### 🔎 Resource: {resource_type.upper()}")

                # Fetch energy data
                try:
                    response = requests.get(f"{FASTAPI_BASE_URL}/ecofloc/{resource_type}")
                    response.raise_for_status()
                    df = pd.DataFrame(response.json())
                except Exception as e:
                    st.error(f"Error fetching data for {resource_type}: {e}")
                    continue

                # Ensure required columns
                required = ['timestamp', 'metric_value', 'metric_name', 'process_name']
                if not all(col in df.columns for col in required):
                    st.warning(f"Skipping {resource_type} due to missing columns.")
                    continue

                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                df['metric_value'] = pd.to_numeric(df['metric_value'], errors='coerce')
                df.dropna(subset=['timestamp', 'metric_value'], inplace=True)
                df['process_name'] = df['process_name'].astype(str)

                # Filter for total energy metrics
                energy_df = df[df['metric_name'].str.lower().str.contains("total energy")]
                if energy_df.empty:
                    st.info(f"No total energy data for {resource_type}.")
                    continue

                # Convert to kWh and compute CO₂
                energy_df['energy_kwh'] = energy_df['metric_value'] / 3_600_000
                energy_df['co2_g'] = energy_df['energy_kwh'] * carbon_intensity
                energy_df['co2_kg'] = energy_df['co2_g'] / 1000

                # Total CO₂ per process
                carbon_summary = (
                    energy_df.groupby("process_name")[["co2_kg", "energy_kwh"]]
                    .sum()
                    .reset_index()
                    .sort_values(by="co2_kg", ascending=False)
                )

                # Total CO₂ today
                total_co2_kg = carbon_summary['co2_kg'].sum()
                global_total_co2_kg += total_co2_kg

                st.metric(f"🌫️ Total CO₂ Emissions Today ({resource_type.upper()})", f"{total_co2_kg:.8f} kg")

                # 📊 Bar Plot: CO₂ by process
                fig_bar = px.bar(
                    carbon_summary,
                    x="process_name",
                    y="co2_kg",
                    labels={"process_name": "Process", "co2_kg": "CO₂ (kg)"},
                    title=f"{resource_type.upper()} - CO₂ Emissions by Process",
                )

                # 📈 Line Plot: CO₂ over time
                fig_line = px.line(
                    energy_df,
                    x="timestamp",
                    y="co2_kg",
                    color="process_name",
                    labels={"timestamp": "Time", "co2_kg": "CO₂ (kg)", "process_name": "Process"},
                    title=f"{resource_type.upper()} - CO₂ Over Time"
                )
                fig_line.update_layout(height=500)

                col1, col2 = st.columns(2)

                with col1:
                    st.subheader(f"📊 CO₂ by Process ({resource_type.upper()})")
                    st.plotly_chart(fig_bar, use_container_width=True, key=f"{resource_type}_co2_bar")

                with col2:
                    st.subheader("📈 CO₂ Over Time")
                    st.plotly_chart(fig_line, use_container_width=True, key=f"{resource_type}_co2_line")

                # 🏭 Table: Top 5 emitters
                top5 = carbon_summary.head(5).copy()
                st.subheader(f"🏭 Top 5 CO₂ Emitters ({resource_type.upper()})")
                st.table(top5[['process_name', 'co2_kg', 'energy_kwh']])

    except Exception as e:
        st.error(f"Failed to load carbon footprint: {e}")


with tab4:

    st.title("Carbon Footprint Summary")
    cols1 , col2 , cols3 = st.columns(3)
    with cols1:
        st.subheader("Scope 3 Value")
        def sum_impacts(*args):
            total_impacts = {}
            for data in args:
                if not data:
                    continue
                impacts = data.get("impacts", {})
                for impact_type, impact_vals in impacts.items():
                    if impact_type not in total_impacts:
                        total_impacts[impact_type] = {"manufacture": 0, "use": 0, "unit": impact_vals.get("unit", "")}
                    total_impacts[impact_type]["manufacture"] += impact_vals.get("manufacture", 0)
                    total_impacts[impact_type]["use"] += impact_vals.get("use", 0)
            return total_impacts
        
            # --- Sum all impacts ---
        total_impacts = sum_impacts(cpu_data, ram_data, case_data, motherboard_data)  # Add SSD, HDD, Case, etc.

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

