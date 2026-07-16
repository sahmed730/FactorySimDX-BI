-- ==========================================
-- MeidenSmart AI - Silver Layer (Cleansed & Conformed)
-- ==========================================
USE DATABASE MEIDENSMART_DB;
USE SCHEMA SILVER;

-- 1. Cleansed Sensor Data
-- Cleans up raw telemetry, normalizes names, filters out invalid readings
CREATE OR REPLACE VIEW SILVER_SENSOR_CLEANSED AS
SELECT 
    TRY_TO_TIMESTAMP(Timestamp) AS Event_Time,
    DATE(TRY_TO_TIMESTAMP(Timestamp)) AS Event_Date,
    UPPER(Factory) AS Factory_ID,
    UPPER(Production_Line) AS Line_ID,
    UPPER(Machine) AS Machine_ID,
    CAST(Temperature AS DECIMAL(10,2)) AS Temp_Celsius,
    CAST(Vibration AS DECIMAL(10,2)) AS Vibration_Hz,
    CAST(Power_Consumption AS DECIMAL(10,2)) AS Power_kW,
    CAST(RPM AS DECIMAL(10,2)) AS Spindle_RPM,
    Running_Status,
    Mode,
    CASE WHEN Error_Code = 'None' THEN NULL ELSE Error_Code END AS Error_Code
FROM MEIDENSMART_DB.BRONZE.FACT_SENSOR
WHERE Timestamp IS NOT NULL;

-- 2. Conformed Production Logs
-- Merges ERP production logs with Product dimension for enriched analytics
CREATE OR REPLACE VIEW SILVER_PRODUCTION_ENRICHED AS
SELECT 
    p.Production_Order,
    p.Product AS Product_ID,
    d.Factory_Type AS Product_Category,
    p.Quantity_Planned,
    p.Quantity_Produced,
    p.Scrap,
    (p.Quantity_Produced - p.Scrap) AS Good_Quantity,
    p.Operator,
    p.Shift,
    p.Start_Time,
    p.End_Time,
    TIMESTAMPDIFF('minute', p.Start_Time, p.End_Time) AS Duration_Minutes
FROM MEIDENSMART_DB.BRONZE.FACT_ERP_PRODUCTION p
LEFT JOIN MEIDENSMART_DB.BRONZE.DIM_PRODUCT d ON p.Product = d.Product;

-- 3. Cleansed Maintenance Logs
CREATE OR REPLACE VIEW SILVER_MAINTENANCE_CLEANSED AS
SELECT 
    Date AS Maintenance_Date,
    Machine AS Machine_ID,
    Failure AS Failure_Mode,
    Root_Cause,
    Severity,
    Technician,
    Downtime AS Downtime_Hours,
    Cost AS Maintenance_Cost_USD
FROM MEIDENSMART_DB.BRONZE.FACT_MAINTENANCE
WHERE Downtime > 0;

-- 4. Quality Inspection Enrichment
CREATE OR REPLACE VIEW SILVER_QUALITY_ENRICHED AS
SELECT 
    q.Inspection_ID,
    q.Date AS Inspection_Date,
    q.Product AS Product_ID,
    q.Defect_Type,
    q.Pass,
    q.Fail,
    (q.Pass + q.Fail) AS Total_Inspected,
    CASE WHEN (q.Pass + q.Fail) > 0 THEN (q.Fail / (q.Pass + q.Fail)) ELSE 0 END AS Defect_Rate
FROM MEIDENSMART_DB.BRONZE.FACT_QUALITY q;
