import os
import snowflake.connector
import logging

logging.basicConfig(level=logging.INFO)

# Set these environment variables or replace with credentials for local testing
SNOWFLAKE_USER = os.getenv('SNOWFLAKE_USER', 'YOUR_USERNAME')
SNOWFLAKE_PASSWORD = os.getenv('SNOWFLAKE_PASSWORD', 'YOUR_PASSWORD')
SNOWFLAKE_ACCOUNT = os.getenv('SNOWFLAKE_ACCOUNT', 'YOUR_ACCOUNT_IDENTIFIER')
DATABASE = 'MEIDENSMART_DB'
SCHEMA = 'BRONZE'
WAREHOUSE = 'MEIDEN_WH'
OUTPUT_DIR = '../output'

def upload_to_snowflake():
    try:
        conn = snowflake.connector.connect(
            user=SNOWFLAKE_USER,
            password=SNOWFLAKE_PASSWORD,
            account=SNOWFLAKE_ACCOUNT,
            warehouse=WAREHOUSE,
            database=DATABASE,
            schema=SCHEMA
        )
        cursor = conn.cursor()
        logging.info("Connected to Snowflake.")
        
        # 1. Upload CSVs to Internal Stage
        files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.csv') and 'live' not in f]
        for file in files:
            filepath = os.path.join(OUTPUT_DIR, file).replace('\\', '/')
            logging.info(f"Uploading {file} to internal stage...")
            cursor.execute(f"PUT file://{filepath} @raw_data_stage AUTO_COMPRESS=TRUE OVERWRITE=TRUE")
            
        # 2. Copy Data into Bronze Tables
        table_mapping = {
            "dim_factory.csv": "DIM_FACTORY",
            "dim_machine.csv": "DIM_MACHINE",
            "dim_product.csv": "DIM_PRODUCT",
            "dim_production_line.csv": "DIM_PRODUCTION_LINE",
            "dim_employee.csv": "DIM_EMPLOYEE",
            "dim_supplier.csv": "DIM_SUPPLIER",
            "dim_customer.csv": "DIM_CUSTOMER",
            "dim_warehouse.csv": "DIM_WAREHOUSE",
            "dim_part.csv": "DIM_PART",
            "fact_sensor.csv": "FACT_SENSOR",
            "fact_erp_production.csv": "FACT_ERP_PRODUCTION",
            "fact_maintenance.csv": "FACT_MAINTENANCE",
            "fact_quality.csv": "FACT_QUALITY",
            "fact_inventory.csv": "FACT_INVENTORY",
            "fact_energy.csv": "FACT_ENERGY",
            "fact_shipments.csv": "FACT_SHIPMENTS"
        }
        
        for file, table in table_mapping.items():
            if file in files:
                logging.info(f"Copying data into {table}...")
                cursor.execute(f"""
                    COPY INTO {table}
                    FROM @raw_data_stage/{file}.gz
                    FILE_FORMAT = (TYPE = 'CSV' SKIP_HEADER = 1 FIELD_OPTIONALLY_ENCLOSED_BY = '"')
                    ON_ERROR = 'CONTINUE'
                """)
                
        logging.info("ETL Batch Ingestion Complete!")
        
    except Exception as e:
        logging.error(f"Snowflake ETL Failed: {e}")
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    upload_to_snowflake()
