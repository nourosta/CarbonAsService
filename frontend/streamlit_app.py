import streamlit as st
import requests
import time
import pandas as pd
import plotly.express as px
from dbgpu import GPUDatabase
from streamlit_autorefresh import st_autorefresh


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
    st.header("🔄 Real-Time System Monitoring")

    st.header("🧾 Top Running Processes")
    #st_autorefresh(interval=5000)
    try:
       
        response = requests.get(f"{FASTAPI_BASE_URL}/top-processes")
        processes = response.json()
        df = pd.DataFrame(processes)
        df = df.rename(columns={
            'pid': 'PID',
            'name': 'Name',
            'cpu_percent': 'CPU (%)',
            'memory_percent': 'RAM (%)'
        })
        st.dataframe(df)
    except Exception as e:
        st.error(f"Error loading processes: {e}")


    st.subheader("🔋 Measure Energy Usage with EcoFloc")

    # 1. Input fields
    pid = st.number_input("Process PID", min_value=1, step=1)
    metric = st.selectbox("Metric", ["cpu", "ram", "gpu", "nic", "sd"])
    interval_ms = st.number_input("Sampling Interval (ms)", 100, 5000, 1000)
    duration_s = st.number_input("Duration (s)", 1, 30, 2)

    # 2. Run button
    if st.button("Measure Energy"):
        try:
            with st.spinner("Running EcoFloc..."):
                response = requests.get(
                    f"{FASTAPI_BASE_URL}/energy",  # Adjust if using another host
                    params={
                        "pid": pid,
                        "metric": metric,
                        "interval_ms": interval_ms,
                        "duration_s": duration_s
                    },
                    timeout=duration_s + 5
                )
                data = response.json()

            if "error" in data:
                st.error(f"❌ Error: {data['error']}")
                if "raw" in data:
                    st.text(data["raw"])
            else:
                st.success("✅ Energy measurement complete!")
                st.metric("Average Power (W)", f"{data['avg_power_w']:.3f}")
                st.metric("Total Energy (J)", f"{data['total_energy_j']:.3f}")
                st.json(data)

        except Exception as e:
            st.error(f"Request failed: {e}")
    

    st.divider()

    # ----------- Section 2: Auto Measure Top 10 ----------- #
    st.subheader("⚡ Auto-Measure Energy for Top 10 CPU Processes")

    metric_auto = st.selectbox("Metric to measure", ["cpu", "ram", "gpu", "nic", "sd"], key="metric_auto")
    interval_auto = st.number_input("Sampling Interval (ms)", 100, 5000, 1000, key="interval_auto")
    duration_auto = st.number_input("Duration (s)", 1, 30, 2, key="duration_auto")

    if st.button("Measure Top 10 Processes"):
        with st.spinner("Gathering process list..."):
            try:
                top_response = requests.get(f"{FASTAPI_BASE_URL}/processes")
                top_data = top_response.json()
                st.write("DEBUG top_data type:", type(top_data))
                st.write("DEBUG top_data content:", top_data)

                # FIX: Handle both dict and list responses
                if isinstance(top_data, dict) and "processes" in top_data:
                    top_10 = top_data["processes"][:10]
                else:
                    top_10 = top_data[:10]

            except Exception as e:
                st.error(f"Failed to fetch processes: {e}")
                top_10 = []

        results = []

        if top_10:
            with st.spinner(f"Measuring {metric_auto} energy for top 10..."):
                for proc in top_10:
                    pid = proc["pid"]
                    name = proc["name"]
                    try:
                        energy_resp = requests.get(
                            "http://localhost:8000/energy",
                            params={
                                "pid": pid,
                                "metric": metric_auto,
                                "interval_ms": interval_auto,
                                "duration_s": duration_auto
                            },
                            timeout=duration_auto + 5
                        )
                        energy_data = energy_resp.json()

                        if "avg_power_w" in energy_data:
                            results.append({
                                "PID": pid,
                                "Name": name,
                                "CPU %": proc["cpu_percent"],
                                "Memory %": proc["memory_percent"],
                                "Power (W)": energy_data["avg_power_w"],
                                "Energy (J)": energy_data["total_energy_j"]
                            })
                        else:
                            results.append({
                                "PID": pid,
                                "Name": name,
                                "CPU %": proc["cpu_percent"],
                                "Memory %": proc["memory_percent"],
                                "Power (W)": None,
                                "Energy (J)": None,
                                "Error": energy_data.get("error", "Unknown")
                            })

                    except Exception as e:
                        results.append({
                            "PID": pid,
                            "Name": name,
                            "CPU %": proc["cpu_percent"],
                            "Memory %": proc["memory_percent"],
                            "Power (W)": None,
                            "Energy (J)": None,
                            "Error": str(e)
                        })

            df_results = pd.DataFrame(results)
            st.dataframe(df_results, use_container_width=True)

            if "Energy (J)" in df_results.columns:
                st.bar_chart(df_results.set_index("Name")[["Energy (J)"]])

    st.subheader("EcoFloc Monitoring for Top Processes")

    # User-configurable options
    limit = st.slider("Number of Top Processes", 1, 20, 5)
    interval = st.number_input("Sampling Interval (ms)", min_value=100, value=1000, step=100)
    duration = st.number_input("Duration (s)", min_value=1, value=5, step=1)
    resources = st.multiselect(
        "Resources to Monitor", ["cpu", "ram", "gpu", "sd", "nic"], default=["cpu", "ram"]
    )

    if st.button("Run EcoFloc Monitor"):
        with st.spinner("Running EcoFloc..."):
            try:
                query_params = {
                    "limit": limit,
                    "interval": interval,
                    "duration": duration,
                    "resources": ",".join(resources)
                }

                response = requests.get(f"{FASTAPI_BASE_URL}/ecofloc/monitor", params=query_params)
                data = response.json().get("results", [])

                if "results" in data:
                    df = pd.DataFrame(data["results"])
                    if not df.empty:
                        st.success("Monitoring complete.")
                        st.dataframe(df[["pid", "name", "cpu_percent", "memory_percent", "resource"]])

                        with st.expander("Raw Output Logs"):
                            for row in data["results"]:
                                st.text(f"PID {row['pid']} ({row['name']}) - {row['resource']}")
                                st.code(row.get("ecofloc_output", "No output"))

                        st.warning("No results returned.")
                else:
                    st.error(data.get("error", "Unknown error occurred."))

            except Exception as e:
                st.error(f"Failed to fetch data: {e}")
