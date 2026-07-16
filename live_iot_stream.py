import time
import random
import pandas as pd
import logging
from datetime import datetime
import yaml
import os
import json
import snowflake.connector

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class LiveIoTStreamer:
    def __init__(self):
        logging.info("Initializing Granular Live IoT Sensor Streamer...")
        try:
            self.machines = pd.read_csv("output/dim_machine.csv").to_dict('records')
        except FileNotFoundError:
            logging.error("dim_machine.csv not found! Run the main simulation setup first.")
            exit(1)
            
        self.disturbances_file = "output/disturbances.json"
        if not os.path.exists(self.disturbances_file):
            with open(self.disturbances_file, 'w') as f:
                json.dump([], f)
                
        # Snowflake connection setup
        self.sf_user = os.getenv('SNOWFLAKE_USER', 'DATA_INGEST_SVC')
        self.sf_password = os.getenv('SNOWFLAKE_PASSWORD', '')
        self.sf_account = os.getenv('SNOWFLAKE_ACCOUNT', 'YOUR_ACCOUNT_IDENTIFIER')
        
        self.sf_database = 'MEIDENSMART_DB'
        self.sf_schema = 'BRONZE'
        self.sf_warehouse = 'COMPUTE_WH'
        
        if os.path.exists("output/snowflake_config.json"):
            try:
                with open("output/snowflake_config.json", "r") as f:
                    cfg = json.load(f)
                    if cfg.get("user"): self.sf_user = cfg.get("user")
                    if cfg.get("password"): self.sf_password = cfg.get("password")
                    if cfg.get("account"): self.sf_account = cfg.get("account")
                    if cfg.get("database"): self.sf_database = cfg.get("database")
                    if cfg.get("schema"): self.sf_schema = cfg.get("schema")
                    if cfg.get("warehouse"): self.sf_warehouse = cfg.get("warehouse")
            except Exception as e:
                logging.error(f"Failed to read Snowflake UI config: {e}")
        
        try:
            # Check for Key-Pair Auth first (Best Practice)
            if os.path.exists("output/rsa_key.p8"):
                from cryptography.hazmat.primitives import serialization
                from cryptography.hazmat.backends import default_backend
                
                with open("output/rsa_key.p8", "rb") as key_file:
                    p_key = serialization.load_pem_private_key(
                        key_file.read(),
                        password=None,
                        backend=default_backend()
                    )
                    
                self.sf_conn = snowflake.connector.connect(
                    user="DATA_INGEST_SVC",
                    account=self.sf_account,
                    private_key=p_key,
                    role="DATA_INGEST_ROLE",
                    database=self.sf_database,
                    schema=self.sf_schema,
                    warehouse=self.sf_warehouse
                )
                logging.info("Successfully connected to Snowflake using Secure Key-Pair Auth!")
            else:
                # Fallback to Password/SSO Auth
                self.sf_conn = snowflake.connector.connect(
                    user=self.sf_user,
                    password=self.sf_password,
                    account=self.sf_account,
                    database=self.sf_database,
                    schema=self.sf_schema,
                    warehouse=self.sf_warehouse,
                    authenticator="externalbrowser"
                )
                logging.info("Successfully connected to Snowflake using Browser SSO!")
                
            self.sf_cursor = self.sf_conn.cursor()
            self.use_snowflake = True
        except Exception as e:
            logging.error(f"Failed to connect to Snowflake: {e}. Live streaming will only write locally.")
            self.use_snowflake = False
            
        try:
            from sqlalchemy import create_engine
            self.pg_engine = create_engine('postgresql://postgres@localhost:5433/mdata')
            self.use_postgres = True
        except Exception as e:
            logging.error(f"Failed to setup Postgres engine: {e}")
            self.use_postgres = False

    def _get_active_disturbances(self):
        try:
            with open(self.disturbances_file, 'r') as f:
                data = json.load(f)
                rules = {}
                # Data format: [{"machine": "M-01", "sensor": "Temperature", "min": 80, "max": 100}]
                for item in data:
                    if isinstance(item, dict) and 'machine' in item:
                        m = item['machine']
                        s = item['sensor']
                        if m not in rules:
                            rules[m] = {}
                        rules[m][s] = (item['min'], item['max'])
                return rules
        except Exception:
            return {}

    def start_stream(self, interval_seconds=5):
        logging.info(f"Starting LIVE IoT data generation every {interval_seconds} seconds...")
        
        filepath = "output/fact_sensor_live.csv"
        columns = ["Timestamp", "Factory", "Production Line", "Machine", "Temperature", "Vibration", 
                   "Voltage", "Current", "Power Consumption", "Pressure", "RPM", "Oil Level", 
                   "Humidity", "Noise", "Running Status", "Error Code", "Mode"]
        # (Manual CSV initialization removed to avoid conflicts with pandas to_csv)

        try:
            while True:
                current_time = datetime.now()
                live_records = []
                forced_disturbances = self._get_active_disturbances()
                
                for m in self.machines:
                    m_id = m['Machine']
                    rules = forced_disturbances.get(m_id, {})
                    is_disturbed = len(rules) > 0
                    
                    # Check for custom baselines
                    custom_temp = m['normal_temp']
                    custom_vib = m['vibration_base']
                    try:
                        if os.path.exists("output/baselines.json"):
                            with open("output/baselines.json", "r") as bf:
                                b_data = json.load(bf)
                                if m_id in b_data:
                                    custom_temp = float(b_data[m_id].get('Temperature', custom_temp))
                                    custom_vib = float(b_data[m_id].get('Vibration', custom_vib))
                    except: pass

                    # Initialize state for smooth transitions
                    if not hasattr(self, 'machine_states'): self.machine_states = {}
                    if m_id not in self.machine_states:
                        self.machine_states[m_id] = {
                            "Temperature": custom_temp, "Vibration": custom_vib, "Power Consumption": m['power_kw'],
                            "RPM": m['max_rpm'], "Voltage": 400, "Current": (m['power_kw'] * 1000) / (400 * 1.732) if m['power_kw'] else 0,
                            "Pressure": 100, "Oil Level": 95, "Humidity": 45, "Noise": 62.5
                        }

                    # Ideal base stats targets
                    t_temp = custom_temp * random.uniform(0.98, 1.02)
                    t_vibration = custom_vib * random.uniform(0.95, 1.05)
                    t_power = m['power_kw'] * random.uniform(0.98, 1.02)
                    t_rpm = m['max_rpm'] * random.uniform(0.98, 1.02) if m['max_rpm'] > 0 else 0
                    t_voltage = 400 * random.uniform(0.99, 1.01)
                    t_current = (t_power * 1000) / (t_voltage * 1.732) if t_voltage > 0 else 0
                    t_pressure = random.uniform(98, 102)
                    t_oil_level = random.uniform(90, 100)
                    t_humidity = random.uniform(40, 50)
                    t_noise = random.uniform(60, 65)
                    
                    if is_disturbed:
                        mode = "Custom Disturbance"
                        status = "Warning"
                        error_code = random.choice(["E101", "E204", "E309"])
                        
                        # Override targets with disturbance rules
                        if "Temperature" in rules: t_temp = random.uniform(rules["Temperature"][0], rules["Temperature"][1])
                        if "Vibration" in rules: t_vibration = random.uniform(rules["Vibration"][0], rules["Vibration"][1])
                        if "Power Consumption" in rules: t_power = random.uniform(rules["Power Consumption"][0], rules["Power Consumption"][1])
                        if "Pressure" in rules: t_pressure = random.uniform(rules["Pressure"][0], rules["Pressure"][1])
                        if "RPM" in rules: t_rpm = random.uniform(rules["RPM"][0], rules["RPM"][1])
                        if "Noise" in rules: t_noise = random.uniform(rules["Noise"][0], rules["Noise"][1])
                        if "Voltage" in rules: t_voltage = random.uniform(rules["Voltage"][0], rules["Voltage"][1])
                        if "Current" in rules: t_current = random.uniform(rules["Current"][0], rules["Current"][1])
                        if "Oil Level" in rules: t_oil_level = random.uniform(rules["Oil Level"][0], rules["Oil Level"][1])
                        if "Humidity" in rules: t_humidity = random.uniform(rules["Humidity"][0], rules["Humidity"][1])
                    else:
                        status = "Running"
                        error_code = "None"
                        mode = "Ideal"

                    # Apply EMA Smoothing for a "slanting" transition (alpha = 0.15)
                    alpha = 0.15
                    ms = self.machine_states[m_id]
                    temp = ms["Temperature"] = ms["Temperature"] + alpha * (t_temp - ms["Temperature"])
                    vibration = ms["Vibration"] = ms["Vibration"] + alpha * (t_vibration - ms["Vibration"])
                    power = ms["Power Consumption"] = ms["Power Consumption"] + alpha * (t_power - ms["Power Consumption"])
                    rpm = ms["RPM"] = ms["RPM"] + alpha * (t_rpm - ms["RPM"])
                    voltage = ms["Voltage"] = ms["Voltage"] + alpha * (t_voltage - ms["Voltage"])
                    current = ms["Current"] = ms["Current"] + alpha * (t_current - ms["Current"])
                    pressure = ms["Pressure"] = ms["Pressure"] + alpha * (t_pressure - ms["Pressure"])
                    oil_level = ms["Oil Level"] = ms["Oil Level"] + alpha * (t_oil_level - ms["Oil Level"])
                    humidity = ms["Humidity"] = ms["Humidity"] + alpha * (t_humidity - ms["Humidity"])
                    noise = ms["Noise"] = ms["Noise"] + alpha * (t_noise - ms["Noise"])
                        
                    live_records.append({
                        "Timestamp": current_time.isoformat(),
                        "Factory": m['Factory'],
                        "Production Line": m['Production Line'],
                        "Machine": m['Machine'],
                        "Temperature": round(temp, 2),
                        "Vibration": round(vibration, 3),
                        "Voltage": round(voltage, 2),
                        "Current": round(current, 2),
                        "Power Consumption": round(power, 2),
                        "Pressure": round(pressure, 2),
                        "RPM": round(rpm, 0),
                        "Oil Level": round(oil_level, 2),
                        "Humidity": round(humidity, 2),
                        "Noise": round(noise, 2),
                        "Running Status": status,
                        "Error Code": error_code,
                        "Mode": mode
                    })
                
                # Atomic write to prevent file lock issues with Power BI refresh
                try:
                    if os.path.exists(filepath):
                        full_df = pd.read_csv(filepath)
                        new_df = pd.DataFrame(live_records, columns=columns)
                        full_df = pd.concat([full_df, new_df], ignore_index=True)
                    else:
                        full_df = pd.DataFrame(live_records, columns=columns)
                        
                    max_rows = 10 * len(self.machines)
                    if len(full_df) > max_rows:
                        full_df = full_df.tail(max_rows)
                        
                    temp_filepath = filepath + ".tmp"
                    full_df.to_csv(temp_filepath, index=False)
                    os.replace(temp_filepath, filepath)
                    
                    if hasattr(self, 'use_postgres') and self.use_postgres:
                        try:
                            # Write to postgres. 'replace' works but it drops the table briefly. 
                            # 'append' requires a TRUNCATE first.
                            # First ensure table exists (to_sql handles creation if not exist)
                            try:
                                with self.pg_engine.begin() as conn:
                                    conn.execute(text("TRUNCATE TABLE fact_sensor_live"))
                            except:
                                pass # Table doesn't exist yet, that's fine
                            
                            full_df.to_sql('fact_sensor_live', self.pg_engine, if_exists='append', index=False)
                        except Exception as e:
                            logging.error(f"Error writing to Postgres: {e}")

                except Exception as e:
                    logging.error(f"Error updating CSV: {e}")
                if self.use_snowflake:
                    try:
                        logging.info("Executing USE WAREHOUSE")
                        self.sf_cursor.execute(f"USE WAREHOUSE {self.sf_warehouse}")
                        logging.info("Executing USE DATABASE")
                        self.sf_cursor.execute(f"USE DATABASE {self.sf_database}")
                        logging.info("Executing USE SCHEMA")
                        self.sf_cursor.execute(f"USE SCHEMA {self.sf_schema}")
                        logging.info("Executing INSERT INTO")
                        insert_query = """
                        INSERT INTO FACT_SENSOR (
                            TIMESTAMP, FACTORY, PRODUCTION_LINE, MACHINE, TEMPERATURE, VIBRATION, VOLTAGE, "CURRENT", POWER_CONSUMPTION, PRESSURE, RPM, OIL_LEVEL, HUMIDITY, NOISE, RUNNING_STATUS, ERROR_CODE, MODE
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """
                        data_tuples = [
                            (
                                r["Timestamp"], r["Factory"], r["Production Line"], r["Machine"], 
                                r["Temperature"], r["Vibration"], r["Voltage"], r["Current"], 
                                r["Power Consumption"], r["Pressure"], r["RPM"], r["Oil Level"], 
                                r["Humidity"], r["Noise"], r["Running Status"], r["Error Code"], r["Mode"]
                            ) for r in live_records
                        ]
                        self.sf_cursor.executemany(insert_query, data_tuples)
                        logging.info(f"Successfully uploaded {len(data_tuples)} records to Snowflake.")
                    except Exception as e:
                        logging.error(f"Error uploading to Snowflake: {e}")
                
                logging.info(f"[{current_time.strftime('%H:%M:%S')}] Wrote {len(live_records)} live IoT records. Custom Disturbed Machines: {len(forced_disturbances)}")
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            logging.info("Live stream stopped.")

if __name__ == "__main__":
    streamer = LiveIoTStreamer()
    streamer.start_stream(interval_seconds=5)
