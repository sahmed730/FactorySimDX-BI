import random

class InventoryGenerator:
    def __init__(self, parts, warehouses):
        self.parts = parts
        self.warehouses = warehouses
        self.stock = {p['Part']: random.randint(5000, 20000) for p in parts}

    def consume(self, prod_records, current_date):
        movements = []
        shortages = False
        
        # simplified BOM consumption for speed
        for record in prod_records:
            qty = record['Quantity Produced'] + record['Scrap']
            if qty <= 0: continue
            
            # Consume 1-3 random parts
            consumed_parts = random.sample(self.parts, random.randint(1, 3))
            for p in consumed_parts:
                part_name = p['Part']
                needed = qty * random.randint(1, 5)
                if self.stock[part_name] < needed:
                    shortages = True
                    actual = self.stock[part_name]
                else:
                    actual = needed
                self.stock[part_name] -= actual

        # Replenishment
        for p in self.parts:
            part_name = p['Part']
            if self.stock[part_name] < p['Safety Stock']:
                self.stock[part_name] += random.randint(5000, 15000)
                
            # Log Snapshot
            wh = random.choice([w for w in self.warehouses if w['Type'] == "Raw Material"])
            movements.append({
                "Date": current_date.strftime("%Y-%m-%d"),
                "Part": part_name,
                "Stock": self.stock[part_name],
                "Safety Stock": p['Safety Stock'],
                "Warehouse": wh['Warehouse'],
                "Supplier": p['Supplier'],
                "Cost": p['Cost'],
                "Lead Time": p['Lead Time']
            })
            
        return movements, shortages
