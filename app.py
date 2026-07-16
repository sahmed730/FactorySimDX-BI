import streamlit as st
import yaml
import os
import json
import pandas as pd
import time
import streamlit.components.v1 as components
from src.factory_sim_dx.engine import SimulationEngine

st.set_page_config(page_title="FactorySimDX", layout="wide")

st.title("FactorySimDX Command Center")

tab1, tab2, tab3 = st.tabs(["Historical Data Generator", "LIVE IoT Streaming Dashboard", "Data Architecture (ERD)"])

config_path = "config.yaml"
with open(config_path, "r") as f:
    config = yaml.safe_load(f)

with tab1:
    st.subheader("Generate Master & Transaction Data")
    st.markdown("Use this to generate the foundational 3-year historical dataset (ERP, Quality, Inventory, Maintenance) for Snowflake ingestion.")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        sim_years = st.slider("Simulation Years", 1, 5, config['simulation']['years'])
        if st.button("Start Generation", type="primary"):
            config['simulation']['years'] = sim_years
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            def update_progress(current, total):
                progress_bar.progress(min(current / total, 1.0))
                status_text.text(f"Simulating Day {current} of {total}...")
                
            engine = SimulationEngine(config)
            engine.setup()
            engine.run(progress_callback=update_progress)
            status_text.success("Batch Data Generated in /output!")

    with col2:
        st.write("### Batch Data Preview")
        output_dir = "output"
        if os.path.exists(output_dir):
            files = [f for f in os.listdir(output_dir) if f.endswith('.csv') and 'live' not in f]
            if files:
                selected_file = st.selectbox("Select table:", files)
                df = pd.read_csv(os.path.join(output_dir, selected_file), nrows=100)
                st.dataframe(df, use_container_width=True)

with tab2:
    st.subheader("Real-Time Machine Telemetry & Granular Disturbance Injection")
    
    disturbances_file = "output/disturbances.json"
    if not os.path.exists(disturbances_file):
        with open(disturbances_file, 'w') as f: json.dump([], f)
        
    with open(disturbances_file, 'r') as f:
        try: active_disturbances = json.load(f)
        except: active_disturbances = []
        
    st.write("### Disturbance Control Panel")
    col_d1, col_d2 = st.columns(2)
    
    try:
        machines_df = pd.read_csv("output/dim_machine.csv")
        machine_list = machines_df['Machine'].tolist()
        
        sensors = ["Temperature", "Vibration", "Power Consumption", "Pressure", "RPM", "Noise", "Voltage", "Current", "Oil Level", "Humidity"]
        
        with col_d1:
            st.write("**Add Custom Sensor Disturbance**")
            selected_machine = st.selectbox("Select Machine:", machine_list)
            selected_sensor = st.selectbox("Select Sensor:", sensors)
            
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                min_val = st.number_input(f"{selected_sensor} Lower Limit", value=0.0)
            with col_r2:
                max_val = st.number_input(f"{selected_sensor} Upper Limit", value=100.0)
                
            if st.button("Inject Custom Disturbance"):
                active_disturbances = [d for d in active_disturbances if not (d.get('machine') == selected_machine and d.get('sensor') == selected_sensor)]
                active_disturbances.append({
                    "machine": selected_machine,
                    "sensor": selected_sensor,
                    "min": float(min_val),
                    "max": float(max_val)
                })
                with open(disturbances_file, 'w') as f: json.dump(active_disturbances, f)
                st.success(f"Disturbance applied to {selected_machine} -> {selected_sensor}")
                
        with col_d2:
            st.write("**Currently Disturbed Sensors (Alerts Active):**")
            if active_disturbances:
                for rule in active_disturbances:
                    st.error(f"[ALERT] {rule['machine']} | {rule['sensor']} forced between {rule['min']} - {rule['max']}")
                if st.button("Clear All Disturbances (Return to Ideal)"):
                    with open(disturbances_file, 'w') as f: json.dump([], f)
                    st.success("All machines returned to Ideal state.")
            else:
                st.success("All sensors are in IDEAL state.")
    except Exception as e:
        st.warning("Master data not found. Generate historical data first to load machines.")
        
    st.markdown("---")
    
    live_file = "output/fact_sensor_live.csv"
    
    if os.path.exists(live_file):
        st.button("Manual Refresh")
        try:
            df_live = pd.read_csv(live_file).tail(1500)
            
            if not df_live.empty:
                latest_time = df_live.iloc[-1]['Timestamp']
                st.caption(f"Last updated: {latest_time}")
                
                col_a, col_b, col_c, col_d = st.columns(4)
                active_machines_count = df_live['Machine'].nunique()
                warnings = len(df_live[df_live['Running Status'] == 'Warning'])
                avg_power = df_live['Power Consumption'].mean()
                
                col_a.metric("Machines Streaming", active_machines_count)
                col_b.metric("Active Warnings", warnings, f"{warnings} Alert(s)" if warnings > 0 else "Normal", delta_color="inverse")
                col_c.metric("Avg Power (kW)", f"{avg_power:.1f}")
                
                selected_chart_machine = st.selectbox("Select Machine for Live Telemetry Chart:", df_live['Machine'].unique(), key="chart_machine")
                
                df_machine = df_live[df_live['Machine'] == selected_chart_machine]
                
                st.write(f"**Live Feed: {selected_chart_machine}** (Current Mode: `{df_machine.iloc[-1]['Mode']}`)")
                
                st.line_chart(df_machine.set_index('Timestamp')[['Temperature', 'Vibration', 'Power Consumption']])
                
                st.dataframe(df_machine.tail(5)[['Timestamp', 'Mode', 'Temperature', 'Vibration', 'Running Status', 'Error Code']], use_container_width=True)
                
        except Exception as e:
            st.error(f"Error reading live stream: {e}")
            
        auto_refresh = st.checkbox("🔄 Enable Live Auto-Refresh", value=True)
        if auto_refresh:
            time.sleep(2)
            st.rerun()
    else:
        st.info("Live data stream not found. Please open a terminal and run `python live_iot_stream.py`.")

with tab3:
    st.subheader("Graphical Data Architecture (ERD)")
    graphviz_code = """
    digraph ERD {
        node [shape=record, fontname="Arial", fontsize=10];
        edge [fontname="Arial", fontsize=9, color="gray"];
        rankdir=LR;

        DIM_FACTORY [label="{DIM_FACTORY|Factory (PK)\\nType\\nLocation}", style=filled, fillcolor="#e1f5fe"];
        DIM_PRODUCTION_LINE [label="{DIM_PRODUCTION_LINE|Production_Line (PK)\\nFactory (FK)}", style=filled, fillcolor="#e1f5fe"];
        DIM_MACHINE [label="{DIM_MACHINE|Machine (PK)\\nProduction_Line (FK)\\nFactory (FK)\\nType}", style=filled, fillcolor="#e1f5fe"];
        DIM_PRODUCT [label="{DIM_PRODUCT|Product (PK)\\nFactory_Type}", style=filled, fillcolor="#e1f5fe"];
        DIM_EMPLOYEE [label="{DIM_EMPLOYEE|Employee (PK)\\nFactory (FK)\\nRole}", style=filled, fillcolor="#e1f5fe"];
        DIM_SUPPLIER [label="{DIM_SUPPLIER|Supplier (PK)\\nDelivery_Time}", style=filled, fillcolor="#e1f5fe"];
        DIM_CUSTOMER [label="{DIM_CUSTOMER|Customer (PK)\\nType}", style=filled, fillcolor="#e1f5fe"];
        DIM_WAREHOUSE [label="{DIM_WAREHOUSE|Warehouse (PK)\\nFactory (FK)}", style=filled, fillcolor="#e1f5fe"];
        DIM_PART [label="{DIM_PART|Part (PK)\\nSupplier (FK)}", style=filled, fillcolor="#e1f5fe"];

        FACT_SENSOR [label="{FACT_SENSOR|Timestamp\\nMachine (FK)\\nTemperature\\nVibration\\nPower\\nStatus\\nMode}", style=filled, fillcolor="#fff3e0"];
        FACT_MAINTENANCE [label="{FACT_MAINTENANCE|Date\\nMachine (FK)\\nTechnician (FK)\\nFailure\\nCost}", style=filled, fillcolor="#fff3e0"];
        FACT_ERP_PRODUCTION [label="{FACT_ERP|Production_Order (PK)\\nProduct (FK)\\nOperator (FK)\\nQuantity\\nScrap}", style=filled, fillcolor="#fff3e0"];
        FACT_QUALITY [label="{FACT_QUALITY|Inspection_ID (PK)\\nProduct (FK)\\nInspector (FK)\\nPass/Fail}", style=filled, fillcolor="#fff3e0"];
        FACT_INVENTORY [label="{FACT_INVENTORY|Date\\nPart (FK)\\nWarehouse (FK)\\nSupplier (FK)\\nStock}", style=filled, fillcolor="#fff3e0"];
        FACT_ENERGY [label="{FACT_ENERGY|Date\\nMachine (FK)\\nEnergy\\nCost}", style=filled, fillcolor="#fff3e0"];
        FACT_SHIPMENTS [label="{FACT_SHIPMENTS|Shipment_ID (PK)\\nOrder (FK)\\nCustomer (FK)\\nProduct (FK)\\nDelayed}", style=filled, fillcolor="#fff3e0"];

        DIM_FACTORY -> DIM_PRODUCTION_LINE [label=" houses"];
        DIM_FACTORY -> DIM_WAREHOUSE [label=" houses"];
        DIM_FACTORY -> DIM_EMPLOYEE [label=" employs"];
        DIM_PRODUCTION_LINE -> DIM_MACHINE [label=" contains"];
        DIM_SUPPLIER -> DIM_PART [label=" supplies"];
        DIM_MACHINE -> FACT_SENSOR [label=" monitors", dir=back, color="#ef6c00"];
        DIM_MACHINE -> FACT_MAINTENANCE [label=" repairs", dir=back, color="#ef6c00"];
        DIM_EMPLOYEE -> FACT_MAINTENANCE [label=" performed_by", dir=back];
        DIM_PRODUCT -> FACT_ERP_PRODUCTION [label=" manufactures", dir=back, color="#ef6c00"];
        DIM_EMPLOYEE -> FACT_ERP_PRODUCTION [label=" operated_by", dir=back];
        DIM_PRODUCT -> FACT_QUALITY [label=" inspects", dir=back, color="#ef6c00"];
        DIM_EMPLOYEE -> FACT_QUALITY [label=" inspected_by", dir=back];
        DIM_PART -> FACT_INVENTORY [label=" stocks", dir=back, color="#ef6c00"];
        DIM_WAREHOUSE -> FACT_INVENTORY [label=" stored_in", dir=back];
        DIM_SUPPLIER -> FACT_INVENTORY [label=" supplied_by", dir=back];
        DIM_MACHINE -> FACT_ENERGY [label=" consumes", dir=back, color="#ef6c00"];
        FACT_ERP_PRODUCTION -> FACT_SHIPMENTS [label=" fulfills", dir=back, color="#ef6c00"];
        DIM_CUSTOMER -> FACT_SHIPMENTS [label=" delivers_to", dir=back];
        DIM_PRODUCT -> FACT_SHIPMENTS [label=" contains", dir=back];
    }
    """
    try:
        st.graphviz_chart(graphviz_code, use_container_width=True)
    except Exception as e:
        st.error(f"Could not render Graphviz: {e}. Make sure graphviz is installed on the system.")

    st.markdown("---")
    st.subheader("Data Catalog & Schema Explorer")
    st.markdown("Use this interactive dictionary to dive into the details of the Medallion Architecture (Bronze Layer).")

    schema_def = {
        "DIM_FACTORY": {"type": "Dimension", "desc": "Master list of manufacturing facilities.", "columns": ["Factory (PK)", "Type", "Location"], "links_to": []},
        "DIM_PRODUCTION_LINE": {"type": "Dimension", "desc": "Lines within a factory.", "columns": ["Production_Line (PK)", "Factory (FK)"], "links_to": ["DIM_FACTORY"]},
        "DIM_MACHINE": {"type": "Dimension", "desc": "Individual IoT-enabled machines.", "columns": ["Machine (PK)", "Production_Line (FK)", "Factory (FK)", "Type"], "links_to": ["DIM_PRODUCTION_LINE", "DIM_FACTORY"]},
        "DIM_PRODUCT": {"type": "Dimension", "desc": "Catalog of manufactured products.", "columns": ["Product (PK)", "Factory_Type"], "links_to": []},
        "DIM_EMPLOYEE": {"type": "Dimension", "desc": "Operators, Inspectors, Technicians.", "columns": ["Employee (PK)", "Factory (FK)", "Role"], "links_to": ["DIM_FACTORY"]},
        "DIM_SUPPLIER": {"type": "Dimension", "desc": "Raw material suppliers.", "columns": ["Supplier (PK)", "Delivery_Time"], "links_to": []},
        "DIM_CUSTOMER": {"type": "Dimension", "desc": "End buyers of products.", "columns": ["Customer (PK)", "Type"], "links_to": []},
        "DIM_WAREHOUSE": {"type": "Dimension", "desc": "Storage facilities for parts.", "columns": ["Warehouse (PK)", "Factory (FK)", "Type"], "links_to": ["DIM_FACTORY"]},
        "DIM_PART": {"type": "Dimension", "desc": "Raw materials for production.", "columns": ["Part (PK)", "Supplier (FK)"], "links_to": ["DIM_SUPPLIER"]},
        
        "FACT_SENSOR": {"type": "Fact", "desc": "Live IoT telemetry (Every 5 seconds).", "columns": ["Timestamp", "Machine (FK)", "Temperature", "Vibration", "Power", "Status", "Mode"], "links_to": ["DIM_MACHINE"]},
        "FACT_MAINTENANCE": {"type": "Fact", "desc": "Machine breakdown and repair logs.", "columns": ["Date", "Machine (FK)", "Technician (FK)", "Failure", "Cost"], "links_to": ["DIM_MACHINE", "DIM_EMPLOYEE"]},
        "FACT_ERP_PRODUCTION": {"type": "Fact", "desc": "Daily production runs and scrap counts.", "columns": ["Production_Order (PK)", "Product (FK)", "Operator (FK)", "Quantity", "Scrap"], "links_to": ["DIM_PRODUCT", "DIM_EMPLOYEE"]},
        "FACT_QUALITY": {"type": "Fact", "desc": "QA inspection results of finished goods.", "columns": ["Inspection_ID (PK)", "Product (FK)", "Inspector (FK)", "Pass", "Fail"], "links_to": ["DIM_PRODUCT", "DIM_EMPLOYEE"]},
        "FACT_INVENTORY": {"type": "Fact", "desc": "Daily stock levels of raw materials.", "columns": ["Date", "Part (FK)", "Warehouse (FK)", "Supplier (FK)", "Stock"], "links_to": ["DIM_PART", "DIM_WAREHOUSE", "DIM_SUPPLIER"]},
        "FACT_ENERGY": {"type": "Fact", "desc": "Daily power consumption and carbon emission.", "columns": ["Date", "Machine (FK)", "Energy", "Cost", "Carbon_Emission"], "links_to": ["DIM_MACHINE"]},
        "FACT_SHIPMENTS": {"type": "Fact", "desc": "Logistics and customer deliveries.", "columns": ["Shipment_ID (PK)", "Production_Order (FK)", "Customer (FK)", "Product (FK)", "Delayed"], "links_to": ["FACT_ERP_PRODUCTION", "DIM_CUSTOMER", "DIM_PRODUCT"]}
    }

    col_s1, col_s2 = st.columns([1, 2])
    
    with col_s1:
        st.write("### Select Table")
        selected_table = st.selectbox("Bronze Layer Tables:", list(schema_def.keys()))
        
        table_info = schema_def[selected_table]
        st.info(f"**Type:** {table_info['type']} Table\n\n**Description:** {table_info['desc']}")
        
        st.write("### Schema & Linkages")
        for col in table_info['columns']:
            if "(PK)" in col: st.markdown(f"- 🔑 **{col}** *(Primary Key)*")
            elif "(FK)" in col: st.markdown(f"- 🔗 **{col}** *(Foreign Key)*")
            else: st.markdown(f"- 📄 {col}")
            
        if table_info['links_to']:
            st.write("### Foreign Key References:")
            for link in table_info['links_to']:
                st.markdown(f"- ➡️ `{link}`")

    with col_s2:
        st.write("### Live Data Preview (from CSV)")
        csv_filename = selected_table.lower() + ".csv"
        csv_path = os.path.join("output", csv_filename)
        
        if os.path.exists(csv_path):
            try:
                df_preview = pd.read_csv(csv_path, nrows=50)
                st.dataframe(df_preview, use_container_width=True)
                st.caption(f"Showing top 50 rows from `output/{csv_filename}`")
            except Exception as e:
                st.error(f"Could not load data preview: {e}")
        else:
            st.warning(f"Data file `{csv_filename}` not found. Please run the Generator in Tab 1.")
