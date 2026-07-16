import random

class EnergyGenerator:
    def __init__(self, machines):
        self.machines = machines
        # Hardcoding the energy config to match MD spec directly
        self.cost_per_kwh = 0.15
        self.co2_per_kwh = 0.4
        
    def generate_daily(self, iot_records, current_date):
        daily_kwh = {}
        peak_usage = {}
        for record in iot_records:
            m_id = record['Machine']
            daily_kwh[m_id] = daily_kwh.get(m_id, 0) + record['Power Consumption']
            peak_usage[m_id] = max(peak_usage.get(m_id, 0), record['Power Consumption'])
            
        energy_records = []
        for m_id, kwh in daily_kwh.items():
            total_kwh = kwh * random.uniform(1.05, 1.1)
            cost = total_kwh * self.cost_per_kwh
            co2 = total_kwh * self.co2_per_kwh
            
            energy_records.append({
                "Date": current_date.strftime("%Y-%m-%d"),
                "Machine": m_id,
                "Energy": round(total_kwh, 2),
                "Cost": round(cost, 2),
                "Carbon Emission": round(co2, 2),
                "Peak Usage": round(peak_usage[m_id], 2)
            })
        return energy_records
