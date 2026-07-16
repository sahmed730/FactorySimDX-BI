import random
import uuid

class QualityGenerator:
    def __init__(self, employees):
        self.inspectors = [e for e in employees if e['Role'] == "Inspector"]
        self.defect_types = ["Surface Scratch", "Wrong Dimension", "Insulation Failure", "Poor Welding", "Paint Defect"]

    def generate_inspections(self, prod_records, failed_machine_ids, current_date):
        inspections = []
        for record in prod_records:
            qty = record['Quantity Produced'] + record['Scrap']
            if qty <= 0: continue
            
            inspected_qty = max(1, int(qty * 0.1))
            scrap_rate = record['Scrap'] / qty if qty > 0 else 0
            
            f_inspectors = [i for i in self.inspectors if i['Factory'] == record['__factory']]
            inspector = random.choice(f_inspectors)['Employee'] if f_inspectors else "Unknown"
            
            for _ in range(inspected_qty):
                is_defective = random.random() < (0.02 + scrap_rate) 
                
                pass_val = 0 if is_defective else 1
                fail_val = 1 if is_defective else 0
                defect_type = random.choice(self.defect_types) if is_defective else "None"
                
                inspections.append({
                    "Date": current_date.strftime("%Y-%m-%d"),
                    "Product": record['Product'],
                    "Inspection": f"INSP-{uuid.uuid4().hex[:8].upper()}",
                    "Defect Type": defect_type,
                    "Pass": pass_val,
                    "Fail": fail_val,
                    "Inspector": inspector
                })
        return inspections
