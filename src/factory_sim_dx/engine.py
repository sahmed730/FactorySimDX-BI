import pandas as pd
import logging
import os
import random
from faker import Faker
from datetime import datetime, timedelta

from src.factory_sim_dx.generators.iot_sensor import IoTSensorGenerator
from src.factory_sim_dx.generators.maintenance import MaintenanceGenerator
from src.factory_sim_dx.generators.production import ProductionGenerator
from src.factory_sim_dx.generators.inventory import InventoryGenerator
from src.factory_sim_dx.generators.quality import QualityGenerator
from src.factory_sim_dx.generators.energy import EnergyGenerator
from src.factory_sim_dx.generators.logistics import LogisticsGenerator

class SimulationEngine:
    def __init__(self, config):
        self.config = config
        self.faker = Faker()
        self.start_date = datetime.strptime(config['simulation']['start_date'], "%Y-%m-%d")
        self.years = config['simulation']['years']
        
        # Dimension lists
        self.factories = []
        self.production_lines = []
        self.machines = []
        self.products = []
        self.employees = []
        self.suppliers = []
        self.customers = []
        self.warehouses = []
        self.parts = []

    def setup(self):
        logging.info("Setting up sophisticated digital twin environment based on MD specs...")
        self._generate_master_data()
        
    def _generate_master_data(self):
        # 1. Factories
        for idx, f in enumerate(self.config['enterprise']['factories']):
            self.factories.append({
                "Factory": f['name'],
                "Type": f['type'],
                "Location": self.faker.city()
            })
            
        # 2. Production Lines
        for f in self.factories:
            for i in range(1, 6): # 5 lines per factory
                self.production_lines.append({
                    "Production Line": f"Line {i} - {f['Factory']}",
                    "Factory": f['Factory']
                })
                
        # 3. Machines
        machine_types = self.config['machine_types']
        machine_idx = 1
        for line in self.production_lines:
            for _ in range(5): # 5 machines per line
                m_type = self.faker.random_element(elements=machine_types)
                self.machines.append({
                    "Machine": f"M-{machine_idx:05d}",
                    "Production Line": line['Production Line'],
                    "Factory": line['Factory'],
                    "Type": m_type['name'],
                    "normal_temp": m_type['normal_temp'],
                    "max_rpm": m_type['max_rpm'],
                    "power_kw": m_type['power_kw'],
                    "vibration_base": m_type['vibration_base'],
                    "reliability": m_type['reliability']
                })
                machine_idx += 1
                
        # 4. Products
        for p in self.config['products']:
            self.products.append({"Product": p['name'], "Factory Type": p['factory_type']})
            
        # 5. Employees
        departments = ["Production", "Quality", "Maintenance", "Engineering", "Data Team", "HR", "Finance", "Procurement"]
        for _ in range(1500):
            self.employees.append({
                "Employee": self.faker.name(),
                "Department": random.choice(departments),
                "Role": random.choice(["Senior Operator", "Operator", "Technician", "Inspector", "Manager"]),
                "Factory": random.choice(self.factories)['Factory']
            })
            
        # 6. Suppliers
        for p in self.config['parts']:
            if not any(s['Supplier'] == p['supplier'] for s in self.suppliers):
                self.suppliers.append({"Supplier": p['supplier'], "Delivery Time": random.randint(3, 14), "Quality Score": round(random.uniform(85, 100), 2)})
                
        # 7. Customers
        customer_types = ["Power Utilities", "Manufacturing Companies", "Government Projects", "Railways", "Renewable Energy Developers"]
        for _ in range(80):
            self.customers.append({"Customer": self.faker.company(), "Type": random.choice(customer_types)})
            
        # 8. Warehouses
        for f in self.factories:
            self.warehouses.append({"Warehouse": f"{f['Factory']} RM Warehouse", "Factory": f['Factory'], "Type": "Raw Material"})
            self.warehouses.append({"Warehouse": f"{f['Factory']} FG Warehouse", "Factory": f['Factory'], "Type": "Finished Goods"})
            
        # 9. Parts
        for p in self.config['parts']:
            self.parts.append({
                "Part": p['name'],
                "Supplier": p['supplier'],
                "Cost": p['cost_per_unit'],
                "Lead Time": p['lead_time_days'],
                "Safety Stock": random.randint(1000, 5000)
            })

        # Save Master Data
        pd.DataFrame(self.factories).to_csv("output/dim_factory.csv", index=False)
        pd.DataFrame(self.production_lines).to_csv("output/dim_production_line.csv", index=False)
        pd.DataFrame(self.machines).to_csv("output/dim_machine.csv", index=False)
        pd.DataFrame(self.products).to_csv("output/dim_product.csv", index=False)
        pd.DataFrame(self.employees).to_csv("output/dim_employee.csv", index=False)
        pd.DataFrame(self.suppliers).to_csv("output/dim_supplier.csv", index=False)
        pd.DataFrame(self.customers).to_csv("output/dim_customer.csv", index=False)
        pd.DataFrame(self.warehouses).to_csv("output/dim_warehouse.csv", index=False)
        pd.DataFrame(self.parts).to_csv("output/dim_part.csv", index=False)
        logging.info("Generated Master Data (9 Dimension Tables).")

    def run(self, progress_callback=None):
        logging.info("Generating enterprise transaction data based on MD structures...")
        
        iot_gen = IoTSensorGenerator(self.machines, self.config)
        maint_gen = MaintenanceGenerator(self.machines, self.employees)
        prod_gen = ProductionGenerator(self.factories, self.machines, self.products, self.employees)
        inv_gen = InventoryGenerator(self.parts, self.warehouses)
        qual_gen = QualityGenerator(self.employees)
        energy_gen = EnergyGenerator(self.machines)
        logistics_gen = LogisticsGenerator(self.customers)

        current_date = self.start_date
        end_date = self.start_date + timedelta(days=365 * self.years)
        
        iot_records, maint_records, prod_records = [], [], []
        inv_records, qual_records, energy_records, ship_records = [], [], [], []
        
        days_simulated = 0
        total_days = 365 * self.years
        
        while current_date < end_date:
            daily_iot, failures = iot_gen.generate_daily(current_date)
            iot_records.extend(daily_iot)
            
            daily_maint = maint_gen.generate_from_failures(failures, current_date)
            maint_records.extend(daily_maint)
            
            daily_prod = prod_gen.generate_daily(current_date, failures)
            prod_records.extend(daily_prod)
            
            daily_inv, shortages = inv_gen.consume(daily_prod, current_date)
            inv_records.extend(daily_inv)
            
            daily_qual = qual_gen.generate_inspections(daily_prod, failures, current_date)
            qual_records.extend(daily_qual)
            
            daily_energy = energy_gen.generate_daily(daily_iot, current_date)
            energy_records.extend(daily_energy)
            
            daily_ship = logistics_gen.generate_shipments(daily_prod, shortages, current_date)
            ship_records.extend(daily_ship)
            
            current_date += timedelta(days=1)
            days_simulated += 1
            
            if progress_callback: progress_callback(days_simulated, total_days)
            if days_simulated % 30 == 0:
                self._flush(iot_records, "output/fact_sensor.csv", append=(days_simulated > 30))
                iot_records = []

        if iot_records: self._flush(iot_records, "output/fact_sensor.csv", append=(days_simulated > 30))
            
        pd.DataFrame(maint_records).to_csv("output/fact_maintenance.csv", index=False)
        pd.DataFrame(prod_records).to_csv("output/fact_erp_production.csv", index=False)
        pd.DataFrame(inv_records).to_csv("output/fact_inventory.csv", index=False)
        pd.DataFrame(qual_records).to_csv("output/fact_quality.csv", index=False)
        pd.DataFrame(energy_records).to_csv("output/fact_energy.csv", index=False)
        pd.DataFrame(ship_records).to_csv("output/fact_shipments.csv", index=False)

    def _flush(self, records, filepath, append=True):
        df = pd.DataFrame(records)
        if not os.path.isfile(filepath) or not append: df.to_csv(filepath, index=False)
        else: df.to_csv(filepath, mode='a', header=False, index=False)
