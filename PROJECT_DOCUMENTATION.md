# FactorySimDX - Comprehensive Project Documentation

## 1. Project Overview
**FactorySimDX** is a state-of-the-art Enterprise IoT and Data Lake simulation platform. Inspired by the advanced manufacturing environments of **MEIDENSHA CORPORATION**, it provides a full-stack data pipeline from raw sensor generation to real-time BI visualization.

The project solves the challenge of visualizing high-frequency factory data by utilizing a local PostgreSQL database combined with Power BI's DirectQuery mode, achieving real-time dashboarding without costly cloud infrastructure or UI interruptions.

---

## 2. Core Architecture

The architecture is divided into three main pillars:

### A. The Data Generation Engine (Python)
Located in `src/factory_sim_dx/`, the engine simulates an entire enterprise:
- **IoT Sensors:** Generates high-frequency data for Temperature, Vibration, and Power Consumption across 100+ machines.
- **AI Predictive Maintenance:** Calculates a real-time `Risk_Score` (0-100%) based on multivariate anomalies in the sensor data.
- **Enterprise Data:** Generates structured Snowflake-ready batch data for Inventory, Logistics, Production, and Quality Control.

### B. The Real-Time Pipeline (PostgreSQL)
- **Script:** `live_iot_stream.py`
- **Function:** Runs an infinite loop, generating 100 machine snapshots every 5 seconds.
- **Database:** It connects directly to a locally hosted PostgreSQL instance (Port 5433) using SQLAlchemy.
- **Methodology:** It truncates and appends data to the `fact_sensor_live` table atomically. This ensures Power BI always has the latest "rolling window" of data without growing the database infinitely or suffering from file-locking crashes.

### C. The Command Center (PyQt5)
- **Script:** `desktop_app.py`
- **Function:** A sleek, dark-themed GUI that acts as the control room for the factory.
- **Features:** 
  - Triggers batch historical data generation.
  - Uploads historical data to Snowflake Bronze tables.
  - **Disturbance Controls:** Allows users to manually inject anomalies (e.g., forcing a machine to overheat or vibrate violently) to test the AI Predictive Risk models in real-time.

---

## 3. Power BI Integration (DirectQuery)

The dashboard is built in Power BI Desktop using **DirectQuery** to achieve native real-time auto-refresh.

### Setup Instructions:
1. Open Power BI Desktop.
2. Select **Get Data** -> **PostgreSQL database**.
3. **Server:** `localhost:5433`
4. **Database:** `mdata`
5. **Data Connectivity mode:** `DirectQuery` (Crucial for real-time updates).
6. **Credentials:** Username `postgres` (No password required).
7. Load the `fact_sensor_live` table.

### Enabling Auto-Refresh:
To make the dashboard animate in real-time:
1. Click the blank canvas in the Power BI report.
2. Go to the **Format Page** pane.
3. Turn on **Page refresh**.
4. Set the refresh interval to **5 Seconds**.

---

## 4. Snowflake Enterprise Data Lake (Batch)
While real-time IoT data flows to PostgreSQL, historical and dimensional data (e.g., Factory Locations, Machine Specs, Maintenance Logs) are sent to **Snowflake**.

- **Bronze Layer:** Raw data dumped directly from the CSV generator.
- **Silver Layer:** Cleansed and normalized data (e.g., removing nulls, standardizing dates).
- **Gold Layer:** Aggregated business-level views (e.g., `gold_factory_efficiency`, `gold_maintenance_costs`) ready for executive dashboarding.

### Configuration
Users can configure their Snowflake credentials directly within the Desktop Command Center UI by clicking the `Snowflake Config` button.

---

## 5. Directory Structure
* `desktop_app.py`: Main UI application.
* `live_iot_stream.py`: Real-time sensor generation and Postgres writer.
* `src/`: Core simulation logic and data generators.
* `docs/`: Database schemas, DBML files, and architecture diagrams.
* `pgsql/`: Standalone PostgreSQL database binaries and data directory.
* `snowflake/`: SQL scripts for creating Bronze, Silver, and Gold layers in the Data Cloud.
* `output/`: Local storage for batch-generated CSV files before cloud upload.
