import random
from datetime import timedelta
import numpy as np

class IoTSensorGenerator:
    def __init__(self, machines, config):
        self.machines = machines
        self.freq_mins = config['simulation'].get('sensor_frequency_minutes', 60)

    def generate_daily(self, current_date):
        daily_records = []
        failed_machines = []
        records_per_day = 24 * (60 // self.freq_mins)
        
        for m in self.machines:
            fail_prob = (1.0 - m['reliability']) / 365.0 
            is_failing = random.random() < fail_prob
            if is_failing: failed_machines.append(m['Machine'])
                
            for step in range(records_per_day):
                timestamp = current_date + timedelta(minutes=step * self.freq_mins)
                
                temp = m['normal_temp'] * random.uniform(0.95, 1.05)
                vibration = m['vibration_base'] * random.uniform(0.9, 1.1)
                power = m['power_kw'] * random.uniform(0.8, 1.0)
                rpm = m['max_rpm'] * random.uniform(0.8, 1.0) if m['max_rpm'] > 0 else 0
                voltage = 400 * random.uniform(0.98, 1.02)
                current = (power * 1000) / (voltage * 1.732) if voltage > 0 else 0
                pressure = random.uniform(90, 110)
                oil_level = random.uniform(70, 100)
                humidity = random.uniform(30, 60)
                noise = random.uniform(60, 85)
                
                if is_failing and step > (records_per_day // 2):
                    temp *= 1.5; vibration *= 3.0; power *= 1.2; noise *= 1.4; pressure *= 0.8
                    status = "Warning"
                    error_code = random.choice(["E101", "E204", "E309"])
                else:
                    status = "Running"
                    error_code = "None"
                    
                daily_records.append({
                    "Timestamp": timestamp,
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
                    "Error Code": error_code
                })
                
        return daily_records, failed_machines
