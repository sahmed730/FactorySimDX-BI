import random
import uuid
from datetime import timedelta

class LogisticsGenerator:
    def __init__(self, customers):
        self.customers = customers

    def generate_shipments(self, prod_records, shortages, current_date):
        shipments = []
        for record in prod_records:
            # Match new key
            if record['Quantity Produced'] <= 0:
                continue
                
            base_delivery_days = random.randint(1, 5)
            delay_days = random.randint(3, 10) if shortages else 0
            
            delivery_date = current_date + timedelta(days=base_delivery_days + delay_days)
            
            shipments.append({
                "Shipment ID": str(uuid.uuid4()),
                "Production Order": record['Production Order'],
                "Customer": random.choice(self.customers)['Customer'] if self.customers else "Unknown",
                "Product": record['Product'],
                "Quantity": record['Quantity Produced'],
                "Dispatch Date": current_date.strftime("%Y-%m-%d"),
                "Expected Delivery Date": delivery_date.strftime("%Y-%m-%d"),
                "Delayed": shortages,
                "Delay Reason": "Inventory Shortage" if shortages else "None"
            })
            
        return shipments
