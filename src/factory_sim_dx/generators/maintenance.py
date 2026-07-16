import random
import uuid

class MaintenanceGenerator:
    def __init__(self, machines, employees):
        self.machines = machines
        self.technicians = [e for e in employees if e['Role'] == "Technician"]
        self.failures = ["Bearing Failure", "Overheating", "Voltage Spike", "Misalignment", "Hydraulic Leak", "Oil Leakage", "Sensor Failure", "Belt Damage"]

    def generate_from_failures(self, failed_machine_ids, current_date):
        logs = []
        for m_id in failed_machine_ids:
            repair_time_hours = random.uniform(2.0, 12.0)
            cost = repair_time_hours * 150 + random.uniform(500, 5000)
            
            # Find technician for this machine's factory
            m_factory = next((m['Factory'] for m in self.machines if m['Machine'] == m_id), None)
            f_techs = [t for t in self.technicians if t['Factory'] == m_factory] if m_factory else self.technicians
            tech = random.choice(f_techs)['Employee'] if f_techs else "Unknown"

            logs.append({
                "Date": current_date.strftime("%Y-%m-%d"),
                "Machine": m_id,
                "Failure": random.choice(self.failures),
                "Root Cause": "Wear and Tear" if random.random() > 0.3 else "Operational Error",
                "Severity": random.choice(["High", "Critical"]),
                "Technician": tech,
                "Downtime": round(repair_time_hours * random.uniform(1.1, 1.5), 1),
                "Repair Time": round(repair_time_hours, 1),
                "Cost": round(cost, 2)
            })
        return logs
