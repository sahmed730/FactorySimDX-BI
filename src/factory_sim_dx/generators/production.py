import random
import uuid
from datetime import timedelta

class ProductionGenerator:
    def __init__(self, factories, machines, products, employees):
        self.factories = factories
        self.machines = machines
        self.products = products
        self.operators = [e for e in employees if e['Role'] in ["Operator", "Senior Operator"]]

    def generate_daily(self, current_date, failed_machine_ids):
        prod_records = []
        shifts = [("Morning", 6, 14), ("Evening", 14, 22), ("Night", 22, 6)]
        
        for factory in self.factories:
            f_machines = [m for m in self.machines if m['Factory'] == factory['Factory']]
            f_prods = [p for p in self.products if p['Factory Type'] == factory['Type']]
            f_ops = [o for o in self.operators if o['Factory'] == factory['Factory']]
            
            if not f_prods or not f_ops: continue
            
            failed_in_factory = [m for m in f_machines if m['Machine'] in failed_machine_ids]
            uptime_factor = 1.0 - (len(failed_in_factory) / len(f_machines)) if f_machines else 1.0
            
            for shift_name, start_hr, end_hr in shifts:
                num_orders = random.randint(2, 5)
                
                for _ in range(num_orders):
                    product = random.choice(f_prods)['Product']
                    operator = random.choice(f_ops)
                    
                    planned_qty = random.randint(100, 500)
                    produced_qty = int(planned_qty * random.uniform(0.9, 1.0) * uptime_factor)
                    if shift_name == "Night": produced_qty = int(produced_qty * 0.9)
                    
                    scrap_rate = random.uniform(0.01, 0.05)
                    if operator['Role'] == "Operator": scrap_rate *= 1.2
                    if failed_in_factory: scrap_rate *= 1.5
                        
                    scrap_qty = int(produced_qty * scrap_rate)
                    start_time = current_date.replace(hour=start_hr, minute=0)
                    end_time = start_time + timedelta(hours=8)
                    
                    prod_records.append({
                        "Production Order": f"ORD-{uuid.uuid4().hex[:8].upper()}",
                        "Product": product,
                        "Quantity Planned": planned_qty,
                        "Quantity Produced": produced_qty,
                        "Scrap": scrap_qty,
                        "Operator": operator['Employee'],
                        "Shift": shift_name,
                        "Start Time": start_time,
                        "End Time": end_time,
                        # Add hidden context fields to pass to other generators
                        "__factory": factory['Factory'],
                        "__product_type": factory['Type']
                    })
        return prod_records
