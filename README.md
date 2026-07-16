# FactorySimDX - Enterprise IoT Simulation

> *Inspired by **MEIDEN ENGINEERING CORPORATION***

FactorySimDX is a highly advanced Enterprise Data Lake and Factory IoT simulation platform. Designed to monitor and manage factory performance, this project integrates **Python**, **PostgreSQL**, and **Power BI** to make complex manufacturing data accessible, real-time, and user-friendly.

**Key Features:**
- 🏭 **Batch Historical Data:** Automatically generates years of historical factory data.
- 📡 **Live IoT Sensor Stream:** Streams continuous, real-time telemetry into a local PostgreSQL database.
- 🤖 **AI Predictive Maintenance:** Detects anomalies and calculates machine failure risks on the fly.
- 📊 **Power BI Integration:** Visualizes the entire pipeline in a sleek, real-time command dashboard.

## Prerequisites

This project uses `uv` for lightning-fast Python dependency management.
If you haven't installed `uv`, install it via PowerShell:
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## How to Run

There are two main components to the simulation: the **Live Streamer** and the **Desktop Command Center**.

### 1. Start the Live IoT Data Stream
The backend streamer generates constant live telemetry data (temperature, vibration, power consumption) for your simulated factory machines. It runs constantly in the background.

Open a terminal (PowerShell or Command Prompt) and run:
```bash
uv run python live_iot_stream.py
```
*Leave this terminal window open.* It will continue simulating 100 rows of live sensor data every 5 seconds.

### 2. Start the Desktop Command Center
The UI allows you to visualize the live data, inject anomalies/disturbances, view the database schema, and upload your datasets to Snowflake.

Open a **new** terminal window and run:
```bash
uv run python desktop_app.py
```

---

## Navigating the Desktop App

The application has three main tabs:

### 1. Batch Data Generator
- **Generate Enterprise Data:** Clicking this will simulate years of historical data (e.g., Factories, Machines, Maintenance Logs, Inventory, etc.) and save them locally to the `output/` folder.
- **Wipe & Upload to Snowflake:** After you generate data, click this button to automatically wipe your existing Snowflake Bronze tables and bulk-upload the fresh data. 
    - *Note: This requires a saved Snowflake connection (see below).*

### 2. Live IoT Stream Dashboard
- **Live Graphing:** Watch the real-time sensor data outputted by `live_iot_stream.py`. 
- **AI Failure Risk:** View the predictive risk of failure for individual machines.
- **Disturbance Control:** Click "Hide/Show Disturbance Controls" to inject anomalies (e.g., forcing a machine's temperature to 180°C). The AI will immediately detect this and raise the risk probability.

### 3. Data Catalog (Bronze)
- Displays an interactive Entity-Relationship Diagram (ERD) of the Snowflake schema. Click on nodes to view columns and relationships.

---

## Configuring Snowflake

To allow the Desktop App to upload your data directly to Snowflake:
1. Open the Desktop App.
2. Click the **"☁️ Snowflake Config"** button in the top right corner.
3. Enter your Snowflake credentials:
    - **Username:** Your SSO username (e.g., `SAHMED730`)
    - **Password:** Your password
    - **Account Identifier:** Your Snowflake account (e.g., `NFXCTSB-PB52626`)
    - **Database/Schema/Warehouse:** Typically `MEIDENSMART_DB`, `BRONZE`, and `COMPUTE_WH`.
4. Click **Save & Connect**. This will open a browser window for SSO authentication. Once authenticated, the connection will be saved.
5. If you ever need to change accounts, click the config button again and click **Remove Account**.