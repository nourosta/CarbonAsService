import streamlit as st
import requests
import time
import pandas as pd
import plotly.express as px
from dbgpu import GPUDatabase
from streamlit_autorefresh import st_autorefresh
from datetime import datetime


tab1, tab2 = st.tabs(["🏠 System Overview", "📈 Live Monitoring"])
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

    if st.button("Fetch CPU Data"):
        try:
            payload = {"name": cpu_name}
            response = requests.post(f"{FASTAPI_BASE_URL}/CPU_Calc", json=payload)
            response.raise_for_status()

            cpu_data = response.json()

            st.subheader("Impact Information:")

            impacts = cpu_data.get("impacts", {})
            for key, impact_info in impacts.items():
                st.text(f"{key.upper()}")
                st.text(f"Unit: {impact_info['unit']}")
                st.text(f"Manufacture Impact: {impact_info['manufacture']} {impact_info['unit']}")
                st.text(f"Use Impact: {impact_info['use']} {impact_info['unit']}")
                st.text("")
        except requests.RequestException as e:
            st.error(f"Failed to retrieve CPU data: {str(e)}")


    st.subheader("RAM Scope3 Calculations", divider=True)

    # --- Input Fields ---
    ram_capacity = st.number_input(
        "Enter RAM Capacity (GB):",
        min_value=1,
        value= 64 #int(math.ceil(float(parsed_info["RAM"].split()[0]) if parsed_info.get("RAM") != "Unknown" else 32))
    )
    ram_manufacturer = st.text_input("Enter RAM Manufacturer:", value="Samsung")
    ram_process = st.number_input("Enter Process (nm):", min_value=1, max_value=100, value=30)

    left, middle, right = st.columns(3)

    # --- Fetch RAM Data ---
    if right.button("Fetch RAM Data"):
        try:
            payload = {
                "capacity": ram_capacity,
                "manufacturer": ram_manufacturer,
                "process": ram_process
            }
            #st.info(f"Fetching RAM impact data with payload: {payload}...")
            
            response = requests.post(f"{FASTAPI_BASE_URL}/RAM-Calc", json=payload)
            response.raise_for_status()
            ram_data = response.json()

            # --- Display Results ---
            st.subheader("Impact Information:")

            impacts = ram_data.get("impacts", {})
            for key, impact_info in impacts.items():
                st.text(f"{key.upper()}")
                st.text(f"Unit: {impact_info['unit']}")
                st.text(f"Manufacture Impact: {impact_info['manufacture']} {impact_info['unit']}")
                st.text(f"Use Impact: {impact_info['use']} {impact_info['unit']}")
                st.text("")
        except requests.RequestException as e:
            st.error(f"Failed to retrieve CPU data: {str(e)}")


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

        ssd_capacity = st.number_input("Enter SSD Capacity (GB):", min_value=1.0, value=parse_disk_size(selected_ssd["size"]))
        ssd_manufacturer = st.text_input("Enter SSD Manufacturer:", value=selected_ssd["model"] or "Unknown")

        if st.button("Fetch SSD Data"):
            try:
                ssd_payload = {"capacity": ssd_capacity, "manufacturer": ssd_manufacturer}
                response = requests.post(f"{FASTAPI_BASE_URL}/SSD-Calc", json=ssd_payload)
                response.raise_for_status()
                ssd_data = response.json()

                # --- Display Results ---
                st.subheader("Impact Information:")

                impacts = ssd_data.get("impacts", {})
                for key, impact_info in impacts.items():
                    st.text(f"{key.upper()}")
                    st.text(f"Unit: {impact_info['unit']}")
                    st.text(f"Manufacture Impact: {impact_info['manufacture']} {impact_info['unit']}")
                    st.text(f"Use Impact: {impact_info['use']} {impact_info['unit']}")
                    st.text("")

            except requests.RequestException as e:
                st.error(f"Failed to retrieve CPU data: {str(e)}")

    # HDD Section
    if hdds:
        st.subheader("HDD Information")
        selected_hdd_index = st.selectbox(
                "Select HDD:", options=range(len(hdds)), format_func=lambda x: f"{hdds[x]['model']} ({hdds[x]['size']})"
            )
        selected_hdd = hdds[selected_hdd_index]

        hdd_capacity = st.number_input("Enter HDD Capacity (GB):", min_value=1, value=int(parse_disk_size(selected_hdd["size"])))
        hdd_units = st.number_input("Enter HDD Units:", min_value=1, value=1)

        if st.button("Fetch HDD Data"):
            try:
                hdd_payload = {"units": hdd_units, "type": "HDD", "capacity": hdd_capacity}
                response = requests.post(f"{FASTAPI_BASE_URL}//HDD-Calc", json=hdd_payload)
                response.raise_for_status()
                hdd_data = response.json()

                st.subheader("HDD Impact Information:")

                impacts = hdd_data.get("impacts", {})
                for key, impact_info in impacts.items():
                    st.text(f"{key.upper()}")
                    st.text(f"Unit: {impact_info['unit']}")
                    st.text(f"Manufacture Impact: {impact_info['manufacture']} {impact_info['unit']}")
                    st.text(f"Use Impact: {impact_info['use']} {impact_info['unit']}")
                    st.text("")

            except requests.RequestException as e:
                st.error(f"Failed to retrieve CPU data: {str(e)}")

    else:
        st.info("No HDDs detected.")

    st.title("Server Case Scope3 Calculation")

    st.subheader("Boavizta Case Calculations", divider = True)

    # Create input fields for SSD specifications
    case_type = st.selectbox("Case Type :", ("blade", "rack"),)
    left, middle, right = st.columns(3)

    if right.button("Fetch Case Data"):
        # HTTP POST request with inputs to FastAPI endpoint
        try:
            payload = {
                "case_type": case_type,
            }
            response = requests.post(f"{FASTAPI_BASE_URL}/Case-Calc", json=payload)
            response.raise_for_status()  # Raise error for bad responses
            case_data = response.json()

            # Display the first 6 impact entries
            st.subheader("Impact Information:")

            impacts = case_data.get("impacts", {})
            for key, impact_info in impacts.items():
                st.text(f"{key.upper()}")
                st.text(f"Unit: {impact_info['unit']}")
                st.text(f"Manufacture Impact: {impact_info['manufacture']} {impact_info['unit']}")
                st.text(f"Use Impact: {impact_info['use']} {impact_info['unit']}")
                st.text("")

        except requests.RequestException as e:
            st.error(f"Failed to retrieve Case data: {str(e)}")
        
    st.title("Motherboard Scope3 Calculation (API non functional)")

    st.subheader("Boavizta Motherboard Calculations", divider = True)

    motherboard_units = st.number_input("Enter Motherboaerd units:", min_value = 1, value = 1)
    motherboard_gwp = 66.10
    motherboard_adp = 3.69E-03
    motherboard_pe  = 836.00

    left, middle, right = st.columns(3)

    if right.button("Calculate Motherboard Impact"):

        st.text(f"Motherboard GWP : {motherboard_units * motherboard_gwp} kgCO2eq")
        st.text(f"Motherboard ADP :  {motherboard_units * motherboard_adp} kgSbeq")
        st.text(f"Motherboard PE :  {motherboard_units * motherboard_pe} MJ")

    detected_GPU = data.get("gpus")

    st.subheader("Boavizta GPU Calculations", divider=True, help="Based on formula found in the following article: https://hal.science/hal-04643414v1/document")

    gpus = [gpu for gpu in detected_GPU]  # Populate from /system-info

    if gpus:
        selected_gpu_index = st.selectbox("Select GPU:", range(len(gpus)), format_func=lambda x: f"GPU {x + 1}")
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

        if st.button("Calculate GPU Impact"):
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

    st_autorefresh(interval=10000, key="refresh")



    try:
        response = requests.get(f"{FASTAPI_BASE_URL}/ecofloc/cpu")
        response.raise_for_status()
        data = response.json()
        df_cpu = pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error fetching CPU data: {e}")
        st.stop()

    # Check if necessary columns exist
    required = ['timestamp', 'metric_value', 'metric_name', 'process_name']
    missing = [col for col in required if col not in df_cpu.columns]
    if missing:
        st.error(f"Missing expected columns: {missing}")
        st.write("Available columns:", df_cpu.columns.tolist())
        st.stop()

    # Type conversion
    df_cpu['timestamp'] = pd.to_datetime(df_cpu['timestamp'], errors='coerce')
    df_cpu['metric_value'] = pd.to_numeric(df_cpu['metric_value'], errors='coerce')
    df_cpu.dropna(subset=["timestamp", "metric_value"], inplace=True)

    # Fix Arrow error (optional)
    for col in df_cpu.select_dtypes(include="object").columns:
        df_cpu[col] = df_cpu[col].astype(str)

    st.subheader("🔍 Raw Ecofloc CPU Data")
    st.dataframe(df_cpu)
    energy_df = df_cpu[df_cpu["metric_name"].str.lower().str.contains("total energy")]
    st.subheader("⚡ Total Energy per Process (Today)")

    total_energy = (
        energy_df.groupby("process_name")["metric_value"]
        .sum()
        .reset_index()
        .sort_values(by="metric_value", ascending=False)
    )

    fig_bar = px.bar(
        total_energy,
        x="process_name",
        y="metric_value",
        labels={"process_name": "Process", "metric_value": "Total Energy (Joules)"},
        title="Total Energy by Process (Midnight to Now)",
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    st.subheader("📈 Energy Consumption Over Time")

    fig_line = px.line(
        energy_df,
        x="timestamp",
        y="metric_value",
        color="process_name",
        labels={
            "timestamp": "Time",
            "metric_value": "Energy (Joules)",
            "process_name": "Process"
        },
        title="Energy Consumption per Process Over Time"
    )

    fig_line.update_layout(height=500)
    st.plotly_chart(fig_line, use_container_width=True)

    top5 = total_energy.head(5)
    st.metric("Total Energy (All Processes)", f"{total_energy['metric_value'].sum():.2f} J")

    st.subheader("🏭 Top 5 Energy Consumers")
    st.table(top5)


        # --- Clean & filter data ---
    df_cpu['timestamp'] = pd.to_datetime(df_cpu['timestamp'], errors='coerce')
    df_cpu['metric_value'] = pd.to_numeric(df_cpu['metric_value'], errors='coerce')
    df_cpu.dropna(subset=["timestamp", "metric_value"], inplace=True)

    # Avoid Arrow error with mixed types
    for col in df_cpu.select_dtypes(include="object").columns:
        df_cpu[col] = df_cpu[col].astype(str)

    # ✅ Filter for today's data (00:00 to now)
    now = datetime.now()
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    df_cpu = df_cpu[df_cpu['timestamp'] >= start_of_day]

    # --- Show raw table ---
    st.subheader("🔍 Raw Ecofloc CPU Data (Today)")
    st.dataframe(df_cpu)

    # --- Filter to only energy-related metrics ---
    energy_df = df_cpu[df_cpu["metric_name"].str.lower().str.contains("total energy")]

    # --- Total energy per process ---
    st.subheader("⚡ Total Energy per Process (Today)")
    total_energy = (
        energy_df.groupby("process_name")["metric_value"]
        .sum()
        .reset_index()
        .sort_values(by="metric_value", ascending=False)
    )

    fig_bar = px.bar(
        total_energy,
        x="process_name",
        y="metric_value",
        labels={"process_name": "Process", "metric_value": "Total Energy (Joules)"},
        title="Total Energy by Process (00:00 → Now)",
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # --- Energy over time ---
    st.subheader("📈 Energy Consumption Over Time (Today)")

    fig_line = px.line(
        energy_df,
        x="timestamp",
        y="metric_value",
        color="process_name",
        labels={
            "timestamp": "Time",
            "metric_value": "Energy (Joules)",
            "process_name": "Process"
        },
        title="Energy Consumption per Process Over Time"
    )
    fig_line.update_layout(height=500)
    st.plotly_chart(fig_line, use_container_width=True)

    # --- Metrics ---
    st.metric("🔋 Total Energy (All Processes)", f"{total_energy['metric_value'].sum():.2f} J")

    # --- Top 5 Consumers ---
    top5 = total_energy.head(5)
    st.subheader("🏭 Top 5 Energy Consumers Today")
    st.table(top5)

        # Auto-refresh every 10 seconds
    st_autorefresh(interval=10000, key="auto_refresh")

    resource_type = st.selectbox("Select Resource Type", ["cpu", "ram", "gpu", "sd", "nic"])

    # Fetch data
    try:
        response = requests.get(f"{FASTAPI_BASE_URL}/ecofloc/{resource_type}")
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        st.stop()

    # Validate and clean data
    required = ['timestamp', 'metric_value', 'metric_name', 'process_name']
    missing = [col for col in required if col not in df.columns]
    if missing:
        st.error(f"Missing expected columns: {missing}")
        st.write("Available columns:", df.columns.tolist())
        st.stop()

    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df['metric_value'] = pd.to_numeric(df['metric_value'], errors='coerce')
    df.dropna(subset=['timestamp', 'metric_value'], inplace=True)

    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str)

    # Filter to total energy only
    energy_df = df[df['metric_name'].str.lower().str.contains("total energy")]

    # Total energy consumed today
    total_energy = (
        energy_df.groupby("process_name")["metric_value"]
        .sum()
        .reset_index()
        .sort_values(by="metric_value", ascending=False)
    )

    # Layout: bar + line plots
    col1, col2 = st.columns(2)

    with col1:
        st.subheader(f"⚡ Total Energy per Process ({resource_type.upper()})")
        fig_bar = px.bar(
            total_energy,
            x="process_name",
            y="metric_value",
            labels={"process_name": "Process", "metric_value": "Energy (J)"},
            title="Energy Consumption by Process"
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col2:
        st.subheader("📈 Energy Over Time")
        fig_line = px.line(
            energy_df,
            x="timestamp",
            y="metric_value",
            color="process_name",
            labels={"timestamp": "Time", "metric_value": "Energy (J)", "process_name": "Process"},
            title="Energy Usage Over Time"
        )
        fig_line.update_layout(height=500)
        st.plotly_chart(fig_line, use_container_width=True)

    # Metrics summary
    st.metric("🔋 Total Energy Today", f"{total_energy['metric_value'].sum():.2f} J")
    top5 = total_energy.head(5)
    st.subheader("🏭 Top 5 Energy Consumers")
    st.table(top5)
