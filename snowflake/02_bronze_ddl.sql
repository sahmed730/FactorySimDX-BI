-- ==========================================
-- MeidenSmart AI - Bronze Layer (Raw Data)
-- ==========================================
USE DATABASE MEIDENSMART_DB;
USE SCHEMA BRONZE;

-- 1. Dimensions
CREATE OR REPLACE TABLE DIM_FACTORY (
    Factory VARCHAR PRIMARY KEY, 
    Type VARCHAR, 
    Location VARCHAR
);

CREATE OR REPLACE TABLE DIM_PRODUCTION_LINE (
    Production_Line VARCHAR PRIMARY KEY, 
    Factory VARCHAR,
    FOREIGN KEY (Factory) REFERENCES DIM_FACTORY(Factory)
);

CREATE OR REPLACE TABLE DIM_MACHINE (
    Machine VARCHAR PRIMARY KEY, 
    Production_Line VARCHAR, 
    Factory VARCHAR, 
    Type VARCHAR, 
    normal_temp FLOAT, 
    max_rpm FLOAT, 
    power_kw FLOAT, 
    vibration_base FLOAT, 
    reliability FLOAT,
    FOREIGN KEY (Production_Line) REFERENCES DIM_PRODUCTION_LINE(Production_Line),
    FOREIGN KEY (Factory) REFERENCES DIM_FACTORY(Factory)
);

CREATE OR REPLACE TABLE DIM_PRODUCT (
    Product VARCHAR PRIMARY KEY, 
    Factory_Type VARCHAR
);

CREATE OR REPLACE TABLE DIM_EMPLOYEE (
    Employee VARCHAR PRIMARY KEY, 
    Department VARCHAR, 
    Role VARCHAR, 
    Factory VARCHAR,
    FOREIGN KEY (Factory) REFERENCES DIM_FACTORY(Factory)
);

CREATE OR REPLACE TABLE DIM_SUPPLIER (
    Supplier VARCHAR PRIMARY KEY, 
    Delivery_Time INT, 
    Quality_Score FLOAT
);

CREATE OR REPLACE TABLE DIM_CUSTOMER (
    Customer VARCHAR PRIMARY KEY, 
    Type VARCHAR
);

CREATE OR REPLACE TABLE DIM_WAREHOUSE (
    Warehouse VARCHAR PRIMARY KEY, 
    Factory VARCHAR, 
    Type VARCHAR,
    FOREIGN KEY (Factory) REFERENCES DIM_FACTORY(Factory)
);

CREATE OR REPLACE TABLE DIM_PART (
    Part VARCHAR PRIMARY KEY, 
    Supplier VARCHAR, 
    Cost FLOAT, 
    Lead_Time INT, 
    Safety_Stock INT,
    FOREIGN KEY (Supplier) REFERENCES DIM_SUPPLIER(Supplier)
);

-- 2. Facts
CREATE OR REPLACE TABLE FACT_SENSOR (
    Timestamp TIMESTAMP_NTZ, 
    Factory VARCHAR, 
    Production_Line VARCHAR, 
    Machine VARCHAR,
    Temperature FLOAT, Vibration FLOAT, Voltage FLOAT, Current FLOAT, Power_Consumption FLOAT,
    Pressure FLOAT, RPM FLOAT, Oil_Level FLOAT, Humidity FLOAT, Noise FLOAT,
    Running_Status VARCHAR, Error_Code VARCHAR, Mode VARCHAR,
    FOREIGN KEY (Factory) REFERENCES DIM_FACTORY(Factory),
    FOREIGN KEY (Production_Line) REFERENCES DIM_PRODUCTION_LINE(Production_Line),
    FOREIGN KEY (Machine) REFERENCES DIM_MACHINE(Machine)
);

CREATE OR REPLACE TABLE FACT_ERP_PRODUCTION (
    Production_Order VARCHAR PRIMARY KEY, 
    Product VARCHAR, 
    Quantity_Planned INT, Quantity_Produced INT,
    Scrap INT, Operator VARCHAR, Shift VARCHAR, Start_Time TIMESTAMP_NTZ, End_Time TIMESTAMP_NTZ,
    __factory VARCHAR, __product_type VARCHAR,
    FOREIGN KEY (Product) REFERENCES DIM_PRODUCT(Product),
    FOREIGN KEY (Operator) REFERENCES DIM_EMPLOYEE(Employee)
);

CREATE OR REPLACE TABLE FACT_MAINTENANCE (
    Date DATE, 
    Machine VARCHAR, 
    Failure VARCHAR, Root_Cause VARCHAR, Severity VARCHAR,
    Technician VARCHAR, Downtime FLOAT, Repair_Time FLOAT, Cost FLOAT,
    FOREIGN KEY (Machine) REFERENCES DIM_MACHINE(Machine),
    FOREIGN KEY (Technician) REFERENCES DIM_EMPLOYEE(Employee)
);

CREATE OR REPLACE TABLE FACT_QUALITY (
    Inspection_ID VARCHAR PRIMARY KEY,
    Date DATE, 
    Product VARCHAR, 
    Inspection VARCHAR, Defect_Type VARCHAR, Pass INT, Fail INT, Inspector VARCHAR,
    FOREIGN KEY (Product) REFERENCES DIM_PRODUCT(Product),
    FOREIGN KEY (Inspector) REFERENCES DIM_EMPLOYEE(Employee)
);

CREATE OR REPLACE TABLE FACT_INVENTORY (
    Date DATE, 
    Part VARCHAR, Stock INT, Safety_Stock INT, Warehouse VARCHAR, Supplier VARCHAR, Cost FLOAT, Lead_Time INT,
    FOREIGN KEY (Part) REFERENCES DIM_PART(Part),
    FOREIGN KEY (Warehouse) REFERENCES DIM_WAREHOUSE(Warehouse),
    FOREIGN KEY (Supplier) REFERENCES DIM_SUPPLIER(Supplier)
);

CREATE OR REPLACE TABLE FACT_ENERGY (
    Date DATE, 
    Machine VARCHAR, Energy FLOAT, Cost FLOAT, Carbon_Emission FLOAT, Peak_Usage FLOAT,
    FOREIGN KEY (Machine) REFERENCES DIM_MACHINE(Machine)
);

CREATE OR REPLACE TABLE FACT_SHIPMENTS (
    Shipment_ID VARCHAR PRIMARY KEY, 
    Production_Order VARCHAR, Customer VARCHAR, Product VARCHAR, Quantity INT,
    Dispatch_Date DATE, Expected_Delivery_Date DATE, Delayed BOOLEAN, Delay_Reason VARCHAR,
    FOREIGN KEY (Production_Order) REFERENCES FACT_ERP_PRODUCTION(Production_Order),
    FOREIGN KEY (Customer) REFERENCES DIM_CUSTOMER(Customer),
    FOREIGN KEY (Product) REFERENCES DIM_PRODUCT(Product)
);
