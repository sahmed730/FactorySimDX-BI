-- ==========================================
-- MeidenSmart AI - Gold Layer (Aggregated Business Views for BI/ML)
-- ==========================================
USE DATABASE MEIDENSMART_DB;
USE SCHEMA GOLD;

-- 1. OEE (Overall Equipment Effectiveness) - Daily Machine Aggregation
-- Availability = (Planned Time - Downtime) / Planned Time
-- Performance = Actual Output / Planned Output
-- Quality = Good Units / Total Units
CREATE OR REPLACE VIEW GOLD_OEE_DAILY AS
WITH Machine_Downtime AS (
    SELECT Machine_ID, Maintenance_Date, SUM(Downtime_Hours) as Total_Downtime
    FROM MEIDENSMART_DB.SILVER.SILVER_MAINTENANCE_CLEANSED
    GROUP BY Machine_ID, Maintenance_Date
),
Daily_Production AS (
    SELECT 
        DATE(Start_Time) AS Prod_Date,
        p.Product_ID,
        SUM(p.Quantity_Planned) AS Planned_Qty,
        SUM(p.Quantity_Produced) AS Actual_Qty,
        SUM(p.Good_Quantity) AS Good_Qty,
        SUM(p.Scrap) AS Scrap_Qty
    FROM MEIDENSMART_DB.SILVER.SILVER_PRODUCTION_ENRICHED p
    GROUP BY DATE(Start_Time), p.Product_ID
)
SELECT 
    d.Prod_Date AS Date,
    'M-00001' AS Machine_ID, -- Abstracted for simplicity
    d.Planned_Qty,
    d.Actual_Qty,
    d.Good_Qty,
    COALESCE(md.Total_Downtime, 0) AS Downtime_Hours,
    -- Simplified OEE calculation heuristics
    ROUND(GREATEST(0, (24 - COALESCE(md.Total_Downtime, 0)) / 24), 2) AS Availability_Pct,
    ROUND(LEAST(1, IFF(d.Planned_Qty=0, 0, d.Actual_Qty / d.Planned_Qty)), 2) AS Performance_Pct,
    ROUND(IFF(d.Actual_Qty=0, 0, d.Good_Qty / d.Actual_Qty), 2) AS Quality_Pct,
    ROUND(
        GREATEST(0, (24 - COALESCE(md.Total_Downtime, 0)) / 24) * 
        LEAST(1, IFF(d.Planned_Qty=0, 0, d.Actual_Qty / d.Planned_Qty)) * 
        IFF(d.Actual_Qty=0, 0, d.Good_Qty / d.Actual_Qty), 4
    ) AS OEE_Score
FROM Daily_Production d
LEFT JOIN Machine_Downtime md ON d.Prod_Date = md.Maintenance_Date;

-- 2. Predictive Maintenance Feature Set (For Data Science / ML)
-- Rolling averages of sensors combined with failure labels
CREATE OR REPLACE VIEW GOLD_ML_PREDICTIVE_MAINTENANCE AS
WITH Daily_Sensors AS (
    SELECT 
        Machine_ID,
        Event_Date,
        AVG(Temp_Celsius) AS Avg_Temp,
        MAX(Temp_Celsius) AS Max_Temp,
        AVG(Vibration_Hz) AS Avg_Vibration,
        MAX(Vibration_Hz) AS Max_Vibration,
        AVG(Power_kW) AS Avg_Power
    FROM MEIDENSMART_DB.SILVER.SILVER_SENSOR_CLEANSED
    GROUP BY Machine_ID, Event_Date
)
SELECT 
    s.Machine_ID,
    s.Event_Date,
    s.Avg_Temp,
    s.Max_Temp,
    s.Avg_Vibration,
    s.Max_Vibration,
    s.Avg_Power,
    IFF(m.Failure_Mode IS NOT NULL, 1, 0) AS Target_Failure_Occurred,
    m.Failure_Mode,
    m.Severity
FROM Daily_Sensors s
LEFT JOIN MEIDENSMART_DB.SILVER.SILVER_MAINTENANCE_CLEANSED m 
    ON s.Machine_ID = m.Machine_ID AND s.Event_Date = m.Maintenance_Date;

-- 3. Executive Factory KPI Dashboard View
CREATE OR REPLACE VIEW GOLD_EXECUTIVE_FACTORY_KPI AS
SELECT 
    p.Factory_ID,
    p.Event_Date,
    COUNT(DISTINCT p.Machine_ID) AS Active_Machines,
    SUM(p.Power_kW) AS Total_Power_Consumed_kW,
    SUM(IFF(p.Running_Status = 'Warning', 1, 0)) AS Total_Warnings,
    SUM(IFF(p.Error_Code IS NOT NULL, 1, 0)) AS Total_Errors
FROM MEIDENSMART_DB.SILVER.SILVER_SENSOR_CLEANSED p
GROUP BY p.Factory_ID, p.Event_Date;
