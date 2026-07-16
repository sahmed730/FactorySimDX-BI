import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import pandas as pd
import os
import json
import threading
import time
import yaml
import pickle
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from src.factory_sim_dx.engine import SimulationEngine
import snowflake.connector

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class InteractiveERD(ctk.CTkFrame):
    def __init__(self, master, schema_def, on_node_click):
        super().__init__(master)
        self.schema_def = schema_def
        self.on_node_click = on_node_click
        
        self.canvas = tk.Canvas(self, bg="#1a1a1a", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        self.nodes = {}
        self.lines = []
        
        # Draw Background Zones
        self.canvas.create_rectangle(20, 20, 300, 480, fill="#2b2b2b", outline="#444444", width=2, tags="zone")
        self.canvas.create_text(160, 40, text="DIMENSIONS (Reference Data)", fill="#888888", font=("Arial", 12, "bold"))
        
        self.canvas.create_rectangle(400, 20, 680, 480, fill="#2b2b2b", outline="#444444", width=2, tags="zone")
        self.canvas.create_text(540, 40, text="FACTS (Transactional Data)", fill="#888888", font=("Arial", 12, "bold"))
        
        positions = {
            "DIM_FACTORY": (50, 70),
            "DIM_PRODUCTION_LINE": (50, 115),
            "DIM_MACHINE": (50, 160),
            "DIM_EMPLOYEE": (50, 205),
            "DIM_PRODUCT": (50, 250),
            "DIM_SUPPLIER": (50, 295),
            "DIM_WAREHOUSE": (50, 340),
            "DIM_PART": (50, 385),
            "DIM_CUSTOMER": (50, 430),
            
            "FACT_SENSOR": (430, 70),
            "FACT_MAINTENANCE": (430, 140),
            "FACT_ERP_PRODUCTION": (430, 210),
            "FACT_QUALITY": (430, 280),
            "FACT_INVENTORY": (430, 350),
            "FACT_SHIPMENTS": (430, 420)
        }
        
        # Draw lines
        for table, info in self.schema_def.items():
            if table in positions:
                x1, y1 = positions[table]
                for link in info.get("links", []):
                    if link in positions:
                        x2, y2 = positions[link]
                        line = self.canvas.create_line(x1+200, y1+15, x2, y2+15, fill="#444444", width=2)
                        self.lines.append((table, link, line))
        
        # Draw buttons
        self.buttons = {}
        for table, pos in positions.items():
            if table in self.schema_def:
                btn = ctk.CTkButton(self.canvas, text=table, width=200, height=30,
                                    fg_color="#333333", hover_color="#555555",
                                    command=lambda t=table: self.click_node(t))
                self.canvas.create_window(pos[0], pos[1], window=btn, anchor="nw")
                self.buttons[table] = btn
                
        # Configure scrolling
        self.canvas.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.canvas.bind('<MouseWheel>', lambda event: self.canvas.yview_scroll(int(-1*(event.delta/120)), "units"))
                
    def click_node(self, selected_table):
        for table, link, line in self.lines:
            self.canvas.itemconfig(line, fill="#444444", width=2)
        for t, b in self.buttons.items():
            b.configure(fg_color="#333333")
            
        self.buttons[selected_table].configure(fg_color="#1f538d") # Blue
        
        for table, link, line in self.lines:
            if table == selected_table or link == selected_table:
                self.canvas.itemconfig(line, fill="#26c6da", width=3) # Bright Cyan
                if table == selected_table and link in self.buttons:
                    self.buttons[link].configure(fg_color="#006064") # Dark Cyan
                elif link == selected_table and table in self.buttons:
                    self.buttons[table].configure(fg_color="#006064")
                    
        self.on_node_click(selected_table)

class FactorySimDesktop(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("FactorySimDX Desktop Command Center")
        self.geometry("1400x900")
        
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(padx=10, pady=10, fill="both", expand=True)
        
        self.tab_batch = self.tabview.add("Batch Data Generator")
        self.tab_live = self.tabview.add("LIVE IoT Stream Dashboard")
        self.tab_schema = self.tabview.add("Data Catalog (Bronze)")
        
        with open("config.yaml", "r") as f:
            self.config = yaml.safe_load(f)
            
        self.setup_batch_tab()
        self.setup_live_tab()
        self.setup_schema_tab()
        
        self.live_running = True
        self.live_thread = threading.Thread(target=self.update_live_loop, daemon=True)
        self.live_thread.start()

    # ==========================
    # TAB 1: BATCH GENERATOR
    # ==========================
    def setup_batch_tab(self):
        self.tab_batch.grid_columnconfigure(0, weight=1)
        self.tab_batch.grid_columnconfigure(1, weight=3)
        self.tab_batch.grid_rowconfigure(0, weight=1)
        
        # Left Panel (Controls)
        left = ctk.CTkFrame(self.tab_batch, fg_color="#1a1a1a", corner_radius=15)
        left.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        
        ctk.CTkLabel(left, text="🏭 Data Simulation Engine", font=ctk.CTkFont(size=24, weight="bold"), text_color="#26c6da").pack(pady=(25, 5))
        ctk.CTkLabel(left, text="Generate years of realistic historical\nmanufacturing data across all systems.", font=ctk.CTkFont(size=14), text_color="#aaaaaa", justify="center").pack(pady=(0, 25))
        
        # Settings Card
        settings_f = ctk.CTkFrame(left, fg_color="#2b2b2b", corner_radius=10)
        settings_f.pack(fill="x", padx=20, pady=10)
        
        self.lbl_years = ctk.CTkLabel(settings_f, text="Simulation Timespan: 3 Years", font=ctk.CTkFont(size=16, weight="bold"))
        self.lbl_years.pack(pady=(15, 5))
        
        self.slider_years = ctk.CTkSlider(settings_f, from_=1, to=5, number_of_steps=4, button_color="#26c6da", button_hover_color="#00bcd4",
                                          command=lambda v: self.lbl_years.configure(text=f"Simulation Timespan: {int(v)} Years"))
        self.slider_years.set(3)
        self.slider_years.pack(pady=(5, 15), padx=20, fill="x")
        
        self.btn_gen = ctk.CTkButton(left, text="🚀  GENERATE ENTERPRISE DATA", font=ctk.CTkFont(size=16, weight="bold"),
                                     height=50, fg_color="#00b0ff", hover_color="#0081cb", command=self.run_generation)
        self.btn_gen.pack(pady=(30, 10), padx=20, fill="x")

        self.btn_upload_sf = ctk.CTkButton(left, text="☁️ WIPE & UPLOAD TO SNOWFLAKE", font=ctk.CTkFont(size=16, weight="bold"),
                                     height=50, fg_color="#6200ea", hover_color="#3700b3", command=self.run_snowflake_upload)
        self.btn_upload_sf.pack(pady=(0, 30), padx=20, fill="x")
        
        # Status Card
        status_f = ctk.CTkFrame(left, fg_color="#222222", corner_radius=10, border_width=1, border_color="#444444")
        status_f.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        ctk.CTkLabel(status_f, text="SYSTEM STATUS", font=ctk.CTkFont(size=12, weight="bold"), text_color="#888888").pack(anchor="w", padx=15, pady=(10, 0))
        self.progressbar = ctk.CTkProgressBar(status_f, progress_color="#00e676")
        self.progressbar.pack(pady=15, fill="x", padx=15)
        self.progressbar.set(0)
        
        self.status_lbl = ctk.CTkLabel(status_f, text="Engine Idle. Ready to simulate.", font=ctk.CTkFont(family="Consolas", size=13), text_color="#00e676")
        self.status_lbl.pack(pady=(0, 15), padx=15, anchor="w")

        # Right Panel (Preview)
        right = ctk.CTkFrame(self.tab_batch, fg_color="#1a1a1a", corner_radius=15)
        right.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)
        
        # Header area
        header_f = ctk.CTkFrame(right, fg_color="transparent")
        header_f.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(header_f, text="📂 Local Data Lake", font=ctk.CTkFont(size=24, weight="bold"), text_color="#26c6da").pack(side="left")
        
        self.lbl_file_size = ctk.CTkLabel(header_f, text="Size: 0 MB", font=ctk.CTkFont(size=14, weight="bold"), text_color="#ffb300")
        self.lbl_file_size.pack(side="right", padx=10)
        
        def get_files():
            if not os.path.exists("output"): return ["No Data"]
            files = [f for f in os.listdir("output") if f.endswith('.csv') and 'live' not in f]
            return files if files else ["No Data"]
            
        self.batch_sel = ctk.CTkOptionMenu(header_f, values=get_files(), width=250, command=self.load_batch_preview,
                                           fg_color="#333333", button_color="#444444")
        self.batch_sel.pack(side="right", padx=20)
        
        # Treeview
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", rowheight=30, font=("Arial", 11))
        style.configure("Treeview.Heading", background="#333333", foreground="#26c6da", font=("Arial", 12, "bold"))
        style.map("Treeview", background=[('selected', '#1f538d')])
        
        self.batch_tree = ttk.Treeview(right)
        self.batch_tree.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        files = get_files()
        if files and files[0] != "No Data":
            self.load_batch_preview(files[0])

    def load_batch_preview(self, filename):
        if filename == "No Data": return
        path = os.path.join("output", filename)
        try:
            size_mb = os.path.getsize(path) / (1024 * 1024)
            self.lbl_file_size.configure(text=f"Size: {size_mb:.2f} MB")
        except:
            self.lbl_file_size.configure(text="Size: Unknown")
            
        df = pd.read_csv(path, nrows=50)
        self.batch_tree.delete(*self.batch_tree.get_children())
        self.batch_tree["column"] = list(df.columns)
        self.batch_tree["show"] = "headings"
        for col in df.columns:
            self.batch_tree.heading(col, text=col)
            self.batch_tree.column(col, width=120)
        for _, row in df.iterrows():
            self.batch_tree.insert("", "end", values=list(row))

    def run_generation(self):
        self.btn_gen.configure(state="disabled", fg_color="#555555")
        self.config['simulation']['years'] = int(self.slider_years.get())
        
        def _task():
            engine = SimulationEngine(self.config)
            engine.setup()
            def update_cb(c, t):
                self.progressbar.set(c/t)
                self.status_lbl.configure(text=f"Generating day {c} of {t}...\nWriting telemetry...", text_color="#ffb300")
            engine.run(progress_callback=update_cb)
            self.status_lbl.configure(text="✓ Simulation Complete!\nAll datasets written to /output", text_color="#00e676")
            self.btn_gen.configure(state="normal", fg_color="#00b0ff")
            
            files = [f for f in os.listdir("output") if f.endswith('.csv') and 'live' not in f]
            self.batch_sel.configure(values=files)
            if files: self.load_batch_preview(files[0])
            
        threading.Thread(target=_task, daemon=True).start()

    def run_snowflake_upload(self):
        if not os.path.exists("output/snowflake_config.json"):
            self.status_lbl.configure(text="❌ Snowflake config missing! Click '☁ Snowflake Config' to save your credentials first.", text_color="red")
            return
            
        self.btn_upload_sf.configure(state="disabled", fg_color="#555555")
        
        def _task():
            try:
                with open("output/snowflake_config.json", "r") as f:
                    cfg = json.load(f)
                    
                self.status_lbl.configure(text="Connecting to Snowflake (Check browser for SSO)...", text_color="#ffb300")
                conn = snowflake.connector.connect(
                    user=cfg["user"],
                    password=cfg["password"],
                    account=cfg["account"],
                    database=cfg["database"],
                    schema=cfg["schema"],
                    warehouse=cfg["warehouse"],
                    authenticator="externalbrowser"
                )
                
                self.status_lbl.configure(text="Recreating tables to ensure fresh start...", text_color="#ffb300")
                cursor = conn.cursor()
                cursor.execute(f"USE WAREHOUSE {cfg['warehouse']}")
                cursor.execute(f"USE DATABASE {cfg['database']}")
                cursor.execute(f"USE SCHEMA {cfg['schema']}")
                
                with open("snowflake/02_bronze_ddl.sql", "r") as f:
                    ddl = f.read()
                
                for stmt in ddl.split(';'):
                    if stmt.strip():
                        cursor.execute(stmt)
                
                # Use standard upload mapping
                file_map = {
                    "dim_factory.csv": "DIM_FACTORY",
                    "dim_production_line.csv": "DIM_PRODUCTION_LINE",
                    "dim_machine.csv": "DIM_MACHINE",
                    "dim_product.csv": "DIM_PRODUCT",
                    "dim_employee.csv": "DIM_EMPLOYEE",
                    "dim_supplier.csv": "DIM_SUPPLIER",
                    "dim_customer.csv": "DIM_CUSTOMER",
                    "dim_warehouse.csv": "DIM_WAREHOUSE",
                    "dim_part.csv": "DIM_PART",
                    "fact_sensor_historical.csv": "FACT_SENSOR",
                    "fact_erp_production.csv": "FACT_ERP_PRODUCTION",
                    "fact_maintenance.csv": "FACT_MAINTENANCE",
                    "fact_quality.csv": "FACT_QUALITY",
                    "fact_inventory.csv": "FACT_INVENTORY",
                    "fact_energy.csv": "FACT_ENERGY",
                    "fact_shipments.csv": "FACT_SHIPMENTS"
                }
                
                from snowflake.connector.pandas_tools import write_pandas
                import pandas as pd
                
                files_found = [f for f in os.listdir("output") if f in file_map]
                total = len(files_found)
                
                for i, filename in enumerate(files_found):
                    table = file_map[filename]
                    self.progressbar.set((i+1)/total)
                    self.status_lbl.configure(text=f"Uploading {filename} to {table}...", text_color="#ffb300")
                    
                    df = pd.read_csv(os.path.join("output", filename))
                    df.columns = [c.upper().replace(" ", "_") for c in df.columns]
                    # We pass the uppercase table name to write_pandas
                    write_pandas(conn, df, table.upper())
                
                conn.close()
                self.status_lbl.configure(text="✓ Snowflake Upload Complete! Database wiped and loaded.", text_color="#00e676")
            except Exception as e:
                self.status_lbl.configure(text=f"❌ Upload failed: {e}", text_color="red")
            finally:
                self.btn_upload_sf.configure(state="normal", fg_color="#6200ea")

        threading.Thread(target=_task, daemon=True).start()

    def on_closing(self):
        self.live_running = False
        self.destroy()

    def toggle_controls(self):
        if self.controls_visible:
            self.controls_container.pack_forget()
            self.btn_toggle.configure(text="▶ Show Disturbance Controls")
            self.controls_visible = False
        else:
            self.controls_container.pack(fill="x", after=self.btn_toggle)
            self.btn_toggle.configure(text="▼ Hide Disturbance Controls")
            self.controls_visible = True

    # ==========================
    # TAB 2: LIVE IOT STREAM
    # ==========================
    
    def open_snowflake_config(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Snowflake Configuration")
        popup.transient(self)
        
        if os.path.exists("output/snowflake_config.json"):
            popup.geometry("400x200")
            ctk.CTkLabel(popup, text="✅ Snowflake Account Connected", font=ctk.CTkFont(size=18, weight="bold"), text_color="#00e676").pack(pady=30)
            
            def remove_account():
                try:
                    os.remove("output/snowflake_config.json")
                except: pass
                status_lbl = getattr(self, "lbl_sf_status", None)
                if status_lbl:
                    status_lbl.configure(text="⚪ Snowflake: Not Configured", text_color="#888888")
                popup.destroy()
                self.open_snowflake_config()
                
            ctk.CTkButton(popup, text="Remove Account", command=remove_account, fg_color="#ff5555", hover_color="#cc0000").pack(pady=10)
        else:
            popup.geometry("450x450")
            ctk.CTkLabel(popup, text="Connect to Snowflake", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
            
            u_entry = ctk.CTkEntry(popup, placeholder_text="Username", width=300)
            u_entry.pack(pady=5)
            p_entry = ctk.CTkEntry(popup, placeholder_text="Password", show="*", width=300)
            p_entry.pack(pady=5)
            a_entry = ctk.CTkEntry(popup, placeholder_text="Account Identifier", width=300)
            a_entry.pack(pady=5)
            
            ctk.CTkLabel(popup, text="Target Destination:", font=ctk.CTkFont(weight="bold")).pack(pady=(15, 0))
            
            db_entry = ctk.CTkEntry(popup, placeholder_text="Database (e.g. MEIDENSMART_DB)", width=300)
            db_entry.pack(pady=5)
            db_entry.insert(0, "MEIDENSMART_DB")
            schema_entry = ctk.CTkEntry(popup, placeholder_text="Schema (e.g. BRONZE)", width=300)
            schema_entry.pack(pady=5)
            schema_entry.insert(0, "BRONZE")
            wh_entry = ctk.CTkEntry(popup, placeholder_text="Warehouse (e.g. COMPUTE_WH)", width=300)
            wh_entry.pack(pady=5)
            wh_entry.insert(0, "COMPUTE_WH")

            def save():
                cfg = {
                    "user": u_entry.get(),
                    "password": p_entry.get(),
                    "account": a_entry.get(),
                    "database": db_entry.get(),
                    "schema": schema_entry.get(),
                    "warehouse": wh_entry.get()
                }
                
                status_lbl = getattr(self, "lbl_sf_status", None)
                try:
                    popup.title("Testing connection... (Check your Web Browser!)")
                    popup.update()
                    conn = snowflake.connector.connect(
                        user=cfg["user"],
                        password=cfg["password"],
                        account=cfg["account"],
                        database=cfg["database"],
                        schema=cfg["schema"],
                        warehouse=cfg["warehouse"],
                        authenticator="externalbrowser"
                    )
                    conn.cursor().execute("SELECT 1")
                    conn.close()
                    with open("output/snowflake_config.json", "w") as f:
                        json.dump(cfg, f)
                    if status_lbl:
                        status_lbl.configure(text="🟢 Snowflake: Connected", text_color="#00e676")
                    popup.destroy()
                except Exception as e:
                    popup.title("Snowflake Configuration")
                    err_lbl = ctk.CTkLabel(popup, text=f"Error: {str(e)}", text_color="red", wraplength=400)
                    err_lbl.pack(pady=5)
                    if status_lbl:
                        status_lbl.configure(text="🔴 Snowflake: Failed", text_color="#ff5555")
                
            ctk.CTkButton(popup, text="Save & Connect", command=save, fg_color="#00b0ff").pack(pady=15)

    def setup_live_tab(self):
        self.controls_visible = True
        
        self.btn_toggle = ctk.CTkButton(self.tab_live, text="▼ Hide Disturbance Controls", 
                                        fg_color="#333333", hover_color="#444444", 
                                        command=self.toggle_controls, height=24, font=ctk.CTkFont(weight="bold"))
        self.btn_toggle.pack(fill="x", pady=(5,0), padx=10)
        
        self.controls_container = ctk.CTkFrame(self.tab_live, fg_color="transparent", height=0)
        self.controls_container.pack(fill="x")
        
        self.top_controls = ctk.CTkFrame(self.controls_container)
        self.top_controls.pack(fill="x", pady=5, padx=10)
        
        dist_f = ctk.CTkFrame(self.top_controls)
        dist_f.pack(side="left", fill="y", padx=10, pady=5)
        ctk.CTkLabel(dist_f, text="Disturbance Control", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=2, pady=5)
        
        try: machines = pd.read_csv("output/dim_machine.csv")['Machine'].tolist()
        except: machines = ["M-00001"]
        self.machine_sel = ctk.CTkOptionMenu(dist_f, values=machines)
        self.machine_sel.grid(row=1, column=0, padx=5, pady=5)
        
        self.sensor_sel = ctk.CTkOptionMenu(dist_f, values=["Temperature", "Vibration", "Power Consumption"])
        self.sensor_sel.grid(row=1, column=1, padx=5, pady=5)
        
        self.min_entry = ctk.CTkEntry(dist_f, placeholder_text="Min", width=80)
        self.min_entry.grid(row=2, column=0, padx=5, pady=5)
        self.max_entry = ctk.CTkEntry(dist_f, placeholder_text="Max", width=80)
        self.max_entry.grid(row=2, column=1, padx=5, pady=5)
        
        ctk.CTkButton(dist_f, text="Inject", fg_color="red", width=80, command=self.inject_dist).grid(row=3, column=0, pady=5)
        ctk.CTkButton(dist_f, text="Clear", width=80, command=self.clear_dist).grid(row=3, column=1, pady=5)
        
        base_f = ctk.CTkFrame(self.top_controls)
        base_f.pack(side="left", fill="y", padx=10, pady=5)
        ctk.CTkLabel(base_f, text="Machine Ideal Baselines", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=2, pady=5)
        self.base_machine_sel = ctk.CTkOptionMenu(base_f, values=machines)
        self.base_machine_sel.grid(row=1, column=0, columnspan=2, padx=5, pady=5)
        self.base_temp_entry = ctk.CTkEntry(base_f, placeholder_text="Ideal Temp (°C)", width=110)
        self.base_temp_entry.grid(row=2, column=0, padx=5, pady=5)
        self.base_vib_entry = ctk.CTkEntry(base_f, placeholder_text="Ideal Vib (mm/s)", width=110)
        self.base_vib_entry.grid(row=2, column=1, padx=5, pady=5)
        ctk.CTkButton(base_f, text="Set Ideal State", width=230, command=self.set_baseline).grid(row=3, column=0, columnspan=2, pady=5)
        
        self.active_f = ctk.CTkScrollableFrame(self.top_controls, height=100)
        self.active_f.pack(side="left", fill="both", expand=True, padx=10, pady=5)
        ctk.CTkLabel(self.active_f, text="Active Disturbances (Alerts):", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        self.lbl_active = ctk.CTkLabel(self.active_f, text="None", text_color="green")
        self.lbl_active.pack(anchor="w")

        # --- FACTORY INFORMATION SECTION ---
        self.factory_info_frame = ctk.CTkFrame(self.tab_live)
        self.factory_info_frame.pack(fill="x", pady=5, padx=10)
        
        ctk.CTkLabel(self.factory_info_frame, text="Factory Information:", font=ctk.CTkFont(weight="bold")).pack(side="top", anchor="w", padx=10, pady=(5,0))
        
        try: 
            factories = pd.read_csv("output/dim_factory.csv")['Factory'].tolist()
            self.dim_machine_df = pd.read_csv("output/dim_machine.csv")
        except: 
            factories = ["Tokyo Transformer Plant"]
            self.dim_machine_df = pd.DataFrame([{"Machine": "M-00001", "Factory": "Tokyo Transformer Plant"}])
            
        self.machine_buttons = {}
        # Make the grid scrollable so it handles many machines elegantly
        self.machines_grid_frame = ctk.CTkScrollableFrame(self.factory_info_frame, fg_color="transparent", height=120)
        self.machines_grid_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        def on_factory_change(choice):
            for widget in self.machines_grid_frame.winfo_children():
                widget.destroy()
            self.machine_buttons.clear()
            
            mach_list = self.dim_machine_df[self.dim_machine_df['Factory'] == choice]['Machine'].tolist()
            
            row, col = 0, 0
            for m in mach_list:
                btn = ctk.CTkButton(self.machines_grid_frame, text=m, fg_color="gray", width=100, hover_color="#333333")
                btn.grid(row=row, column=col, padx=5, pady=5)
                self.machine_buttons[m] = btn
                col += 1
                if col > 7:
                    col = 0
                    row += 1
                    
        self.factory_sel = ctk.CTkOptionMenu(self.factory_info_frame, values=factories, command=on_factory_change)
        self.factory_sel.pack(side="top", anchor="w", padx=10, pady=5)
        if factories:
            on_factory_change(factories[0])
        # -----------------------------------

        kpi_f = ctk.CTkFrame(self.tab_live)
        kpi_f.pack(fill="x", pady=5, padx=10)
        self.lbl_kpi_mach = ctk.CTkLabel(kpi_f, text="Machines: 0", font=ctk.CTkFont(size=16, weight="bold"))
        self.lbl_kpi_mach.pack(side="left", expand=True)
        self.lbl_kpi_warn = ctk.CTkLabel(kpi_f, text="Warnings: 0", font=ctk.CTkFont(size=16, weight="bold"))
        self.lbl_kpi_warn.pack(side="left", expand=True)
        self.lbl_kpi_pwr = ctk.CTkLabel(kpi_f, text="Avg Power: 0 kW", font=ctk.CTkFont(size=16, weight="bold"))
        self.lbl_kpi_pwr.pack(side="left", expand=True)
        
        # AI PREDICTION KPI
        self.lbl_kpi_ai = ctk.CTkLabel(kpi_f, text="🧠 AI Failure Risk: N/A", font=ctk.CTkFont(size=18, weight="bold"), text_color="#00e676")
        self.lbl_kpi_ai.pack(side="left", expand=True)

        try:
            with open("output/predictive_maintenance_model.pkl", "rb") as f:
                self.ai_model = pickle.load(f)
        except:
            self.ai_model = None

        ctrl_f = ctk.CTkFrame(self.tab_live, fg_color="transparent")
        ctrl_f.pack(fill="x", padx=10, pady=5)
        
        self.auto_refresh_var = ctk.BooleanVar(value=True)
        self.chk_auto = ctk.CTkCheckBox(ctrl_f, text="Enable Live Auto-Refresh (Pause/Resume)", variable=self.auto_refresh_var)
        self.chk_auto.pack(side="left", padx=10)
        
        ctk.CTkButton(ctrl_f, text="Manual Refresh", width=120, command=self.do_ui_update).pack(side="left", padx=10)
        
        ctk.CTkLabel(ctrl_f, text="Chart Machine:").pack(side="left", padx=(30, 5))
        self.chart_machine_sel = ctk.CTkOptionMenu(ctrl_f, values=machines)
        self.chart_machine_sel.pack(side="left")
        
        ctk.CTkButton(ctrl_f, text="☁ Snowflake Config", width=140, fg_color="#0081cb", hover_color="#00b0ff", command=self.open_snowflake_config).pack(side="right", padx=10)
        
        self.lbl_sf_status = ctk.CTkLabel(ctrl_f, text="Snowflake: Unknown", text_color="#ffb300", font=ctk.CTkFont(weight="bold"))
        self.lbl_sf_status.pack(side="right", padx=10)
        
        # Async initial check
        def check_initial():
            if os.path.exists("output/snowflake_config.json"):
                self.lbl_sf_status.configure(text="⚪ Snowflake: Config Saved", text_color="#26c6da")
            else:
                self.lbl_sf_status.configure(text="⚪ Snowflake: Not Configured", text_color="#888888")
                
        threading.Thread(target=check_initial, daemon=True).start()
        
        self.chart_frame = ctk.CTkFrame(self.tab_live)
        self.chart_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.fig = Figure(figsize=(8, 4), dpi=100)
        self.fig.patch.set_facecolor('#1a1a1a')
        
        self.ax_temp = self.fig.add_subplot(311)
        self.ax_vib = self.fig.add_subplot(312)
        self.ax_ai = self.fig.add_subplot(313)
        
        for ax in [self.ax_temp, self.ax_vib, self.ax_ai]:
            ax.set_facecolor('#2b2b2b')
            ax.tick_params(colors='white')
            
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.chart_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
        self.live_tree = ttk.Treeview(self.tab_live, height=5)
        self.live_tree.pack(fill="both", expand=False, padx=10, pady=5)
        cols = ['Timestamp', 'Mode', 'Temperature', 'Vibration', 'Running Status', 'Error Code']
        self.live_tree["column"] = cols
        self.live_tree["show"] = "headings"
        for col in cols:
            self.live_tree.heading(col, text=col)
            self.live_tree.column(col, width=100)

    def inject_dist(self):
        try:
            with open("output/disturbances.json", "r") as f: d = json.load(f)
        except: d = []
        rule = {"machine": self.machine_sel.get(), "sensor": self.sensor_sel.get(), 
                "min": float(self.min_entry.get() or 0), "max": float(self.max_entry.get() or 100)}
        d = [x for x in d if not (x['machine']==rule['machine'] and x['sensor']==rule['sensor'])]
        d.append(rule)
        with open("output/disturbances.json", "w") as f: json.dump(d, f)

    def clear_dist(self):
        with open("output/disturbances.json", "w") as f: json.dump([], f)

    def set_baseline(self):
        machine = self.base_machine_sel.get()
        t = self.base_temp_entry.get()
        v = self.base_vib_entry.get()
        
        try:
            if os.path.exists("output/baselines.json"):
                with open("output/baselines.json", "r") as f:
                    b_data = json.load(f)
            else:
                b_data = {}
        except:
            b_data = {}
            
        if machine not in b_data:
            b_data[machine] = {}
            
        try:
            if t.strip(): b_data[machine]["Temperature"] = float(t)
            if v.strip(): b_data[machine]["Vibration"] = float(v)
            
            with open("output/baselines.json", "w") as f:
                json.dump(b_data, f)
                
            self.base_temp_entry.delete(0, 'end')
            self.base_vib_entry.delete(0, 'end')
        except ValueError:
            pass # Ignore invalid inputs for now

    def update_live_loop(self):
        while self.live_running:
            if self.auto_refresh_var.get():
                self.do_ui_update()
            time.sleep(2)
            
    def do_ui_update(self):
        try:
            try:
                with open("output/disturbances.json", "r") as f: d = json.load(f)
                txt_lines = [f"⚠️ {r['machine']} | {r['sensor']} forced to {r['min']}-{r['max']}" for r in d]
                
                try:
                    if os.path.exists("output/baselines.json"):
                        with open("output/baselines.json", "r") as f: b = json.load(f)
                        for m, vals in b.items():
                            s = []
                            if "Temperature" in vals: s.append(f"Temp: {vals['Temperature']}")
                            if "Vibration" in vals: s.append(f"Vib: {vals['Vibration']}")
                            if s:
                                txt_lines.append(f"🎯 {m} Baseline | " + ", ".join(s))
                except: pass
                
                txt = "\n".join(txt_lines)
                if txt:
                    self.lbl_active.configure(text=txt, text_color="orange")
                else:
                    self.lbl_active.configure(text="All sensors in IDEAL state.", text_color="green")
            except: pass

            if os.path.exists("output/fact_sensor_live.csv"):
                df = pd.read_csv("output/fact_sensor_live.csv", on_bad_lines='skip').tail(500)
                if not df.empty:
                    self.lbl_kpi_mach.configure(text=f"Machines: {df['Machine'].nunique()}")
                    warns = len(df[df['Running Status'] == 'Warning'])
                    self.lbl_kpi_warn.configure(text=f"Warnings: {warns}", text_color="red" if warns > 0 else "white")
                    self.lbl_kpi_pwr.configure(text=f"Avg Power: {df['Power Consumption'].mean():.1f} kW")
                    
                    # Update factory machine buttons color based on latest status
                    latest_status = df.drop_duplicates(subset=['Machine'], keep='last')
                    for _, row in latest_status.iterrows():
                        m_id = row['Machine']
                        status = row.get('Running Status', 'Ideal')
                        if m_id in getattr(self, 'machine_buttons', {}):
                            if status in ['Running', 'Ideal']:
                                self.machine_buttons[m_id].configure(fg_color="#00e676", hover_color="#00c853") # Green
                            else:
                                self.machine_buttons[m_id].configure(fg_color="#ff3d00", hover_color="#dd2c00") # Red
                    
                    m_df = df[df['Machine'] == self.chart_machine_sel.get()]
                    if not m_df.empty:
                        # --- AI INFERENCE START ---
                        if self.ai_model is not None:
                            latest_row = m_df.iloc[-1]
                            X_live = pd.DataFrame([{
                                'Temperature': latest_row['Temperature'],
                                'Vibration': latest_row['Vibration'],
                                'Power Consumption': latest_row['Power Consumption']
                            }])
                            risk_proba = self.ai_model.predict_proba(X_live)[0][1] * 100
                            color = "#00e676" if risk_proba < 30 else ("#ffb300" if risk_proba < 75 else "#ff3d00")
                            self.lbl_kpi_ai.configure(text=f"🧠 AI Failure Risk: {risk_proba:.1f}%", text_color=color)
                        # --- AI INFERENCE END ---
                        
                        self.ax_temp.clear()
                        self.ax_vib.clear()
                        self.ax_ai.clear()
                        
                        for ax in [self.ax_temp, self.ax_vib, self.ax_ai]:
                            ax.set_facecolor('#2b2b2b')
                            ax.grid(True, color='#444444', linestyle='--', linewidth=0.5, alpha=0.5)
                            ax.spines['top'].set_visible(False)
                            ax.spines['right'].set_visible(False)
                            ax.spines['left'].set_color('#555555')
                            ax.spines['bottom'].set_color('#555555')
                            ax.tick_params(colors='white', labelsize=8)
                        
                        x = range(len(m_df))
                        
                        # Temp
                        self.ax_temp.plot(x, m_df['Temperature'], color='#ff7043', linewidth=1.5)
                        self.ax_temp.fill_between(x, m_df['Temperature'], color='#ff7043', alpha=0.15)
                        self.ax_temp.set_title("Temperature (°C)", color='#ff7043', fontsize=9, loc='left', pad=2)
                        
                        # Vib
                        self.ax_vib.plot(x, m_df['Vibration'], color='#26c6da', linewidth=1.5)
                        self.ax_vib.fill_between(x, m_df['Vibration'], color='#26c6da', alpha=0.15)
                        self.ax_vib.set_title("Vibration (mm/s)", color='#26c6da', fontsize=9, loc='left', pad=2)
                        
                        # AI Risk
                        recent = m_df.tail(100)
                        if self.ai_model is not None:
                            X_batch = recent[['Temperature', 'Vibration', 'Power Consumption']]
                            risks = self.ai_model.predict_proba(X_batch)[:, 1] * 100
                            x_recent = range(len(m_df)-len(recent), len(m_df))
                            self.ax_ai.plot(x_recent, risks, color='#00e676', linewidth=1.5)
                            self.ax_ai.fill_between(x_recent, risks, color='#00e676', alpha=0.15)
                            self.ax_ai.set_ylim(-5, 105)
                        self.ax_ai.set_title("AI Predictive Risk (%)", color='#00e676', fontsize=9, loc='left', pad=2)
                        
                        self.fig.tight_layout()
                        self.canvas.draw()
                        
                        recent = m_df.tail(5)[['Timestamp', 'Mode', 'Temperature', 'Vibration', 'Running Status', 'Error Code']]
                        self.live_tree.delete(*self.live_tree.get_children())
                        for _, row in recent.iterrows():
                            self.live_tree.insert("", "end", values=list(row))
        except Exception as e:
            print("Live Update Error:", e)

    # ==========================
    # TAB 3: SCHEMA EXPLORER
    # ==========================
    def setup_schema_tab(self):
        self.tab_schema.grid_columnconfigure(0, weight=1)
        self.tab_schema.grid_rowconfigure(0, weight=3) # Canvas height
        self.tab_schema.grid_rowconfigure(1, weight=2) # Info height
        
        self.schema_def = {
            "DIM_FACTORY": {"desc": "Master facilities list.", "cols": ["Factory (PK)", "Type", "Location"], "links": []},
            "DIM_PRODUCTION_LINE": {"desc": "Production lines in a factory.", "cols": ["Production_Line (PK)", "Factory (FK)"], "links": ["DIM_FACTORY"]},
            "DIM_MACHINE": {"desc": "IoT-enabled machines.", "cols": ["Machine (PK)", "Production_Line (FK)", "Factory (FK)", "Type"], "links": ["DIM_PRODUCTION_LINE", "DIM_FACTORY"]},
            "DIM_EMPLOYEE": {"desc": "Staff details.", "cols": ["Employee (PK)", "Factory (FK)", "Role"], "links": ["DIM_FACTORY"]},
            "DIM_PRODUCT": {"desc": "Product catalog.", "cols": ["Product (PK)", "Factory_Type"], "links": []},
            "DIM_SUPPLIER": {"desc": "Vendor info.", "cols": ["Supplier (PK)", "Delivery_Time_Days"], "links": []},
            "DIM_WAREHOUSE": {"desc": "Storage locations.", "cols": ["Warehouse (PK)", "Factory (FK)", "Type"], "links": ["DIM_FACTORY"]},
            "DIM_PART": {"desc": "Manufacturing parts.", "cols": ["Part (PK)", "Supplier (FK)"], "links": ["DIM_SUPPLIER"]},
            "DIM_CUSTOMER": {"desc": "Client list.", "cols": ["Customer (PK)", "Type"], "links": []},
            
            "FACT_SENSOR": {"desc": "Live IoT telemetry.", "cols": ["Timestamp", "Machine (FK)", "Temperature", "Vibration", "Power", "Status", "Mode"], "links": ["DIM_MACHINE"]},
            "FACT_MAINTENANCE": {"desc": "Repair logs.", "cols": ["Date", "Machine (FK)", "Technician (FK)", "Failure", "Cost"], "links": ["DIM_MACHINE", "DIM_EMPLOYEE"]},
            "FACT_ERP_PRODUCTION": {"desc": "Production output.", "cols": ["Production_Order (PK)", "Product (FK)", "Operator (FK)", "Quantity", "Scrap"], "links": ["DIM_PRODUCT", "DIM_EMPLOYEE"]},
            "FACT_QUALITY": {"desc": "QC inspections.", "cols": ["Inspection_ID (PK)", "Product (FK)", "Inspector (FK)", "Pass", "Fail"], "links": ["DIM_PRODUCT", "DIM_EMPLOYEE"]},
            "FACT_INVENTORY": {"desc": "Stock levels.", "cols": ["Date", "Part (FK)", "Warehouse (FK)", "Stock_Level"], "links": ["DIM_PART", "DIM_WAREHOUSE", "DIM_SUPPLIER"]},
            "FACT_SHIPMENTS": {"desc": "Fulfillment.", "cols": ["Shipment_ID (PK)", "Product (FK)", "Customer (FK)"], "links": ["DIM_PRODUCT", "DIM_CUSTOMER", "FACT_ERP_PRODUCTION"]}
        }
        
        # TOP: Interactive Node Graph Canvas
        top_f = ctk.CTkFrame(self.tab_schema, fg_color="transparent")
        top_f.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)
        
        self.erd = InteractiveERD(top_f, self.schema_def, self.update_schema_info)
        self.erd.pack(fill="both", expand=True)
        
        # BOTTOM: Details Panel
        bot_f = ctk.CTkFrame(self.tab_schema, fg_color="transparent")
        bot_f.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
        bot_f.grid_columnconfigure(0, weight=1)
        bot_f.grid_columnconfigure(1, weight=4)
        bot_f.grid_rowconfigure(0, weight=1)
        
        # Bottom-Left: Info Card
        info_f = ctk.CTkFrame(bot_f, fg_color="#1a1a1a", corner_radius=10)
        info_f.grid(row=0, column=0, sticky="nsew", padx=5, pady=0)
        
        self.lbl_selected = ctk.CTkLabel(info_f, text="Select a Node", font=ctk.CTkFont(size=22, weight="bold"), text_color="#26c6da")
        self.lbl_selected.pack(pady=(15, 5), padx=15, anchor="w")
        
        self.lbl_desc = ctk.CTkLabel(info_f, text="", font=ctk.CTkFont(size=14, slant="italic"), text_color="#aaaaaa", wraplength=250, justify="left")
        self.lbl_desc.pack(pady=5, padx=15, anchor="w")
        
        self.col_frame = ctk.CTkScrollableFrame(info_f, fg_color="transparent")
        self.col_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Bottom-Right: Treeview Card
        tree_f = ctk.CTkFrame(bot_f, fg_color="#1a1a1a", corner_radius=10)
        tree_f.grid(row=0, column=1, sticky="nsew", padx=5, pady=0)
        
        ctk.CTkLabel(tree_f, text="Live Data Explorer (Top 50 Rows)", font=ctk.CTkFont(size=18, weight="bold"), text_color="#26c6da").pack(pady=(15, 5), padx=15, anchor="w")
        
        self.schema_tree = ttk.Treeview(tree_f)
        self.schema_tree.pack(fill="both", expand=True, padx=15, pady=(5, 15))
        
        # Default selection
        self.erd.click_node("DIM_FACTORY")

    def update_schema_info(self, table):
        self.lbl_selected.configure(text=table)
        info = self.schema_def.get(table, {"desc":"", "cols":[], "links":[]})
        self.lbl_desc.configure(text=info['desc'])
        
        # Refresh column list UI
        for widget in self.col_frame.winfo_children():
            widget.destroy()
            
        for c in info['cols']:
            color = "white"
            icon = "📄"
            if "(PK)" in c: 
                color = "#ffb300" # Amber
                icon = "🔑"
            elif "(FK)" in c: 
                color = "#29b6f6" # Light blue
                icon = "🔗"
            ctk.CTkLabel(self.col_frame, text=f"{icon}  {c}", text_color=color, font=ctk.CTkFont(weight="bold" if "(PK)" in c else "normal")).pack(anchor="w", pady=2)
        
        # Refresh Treeview
        path = os.path.join("output", table.lower() + ".csv")
        self.schema_tree.delete(*self.schema_tree.get_children())
        if os.path.exists(path):
            df = pd.read_csv(path, nrows=50)
            self.schema_tree["column"] = list(df.columns)
            self.schema_tree["show"] = "headings"
            for col in df.columns:
                self.schema_tree.heading(col, text=col)
                self.schema_tree.column(col, width=120)
            for _, row in df.iterrows():
                self.schema_tree.insert("", "end", values=list(row))

    def destroy(self):
        self.live_running = False
        super().destroy()

if __name__ == "__main__":
    app = FactorySimDesktop()
    app.mainloop()
