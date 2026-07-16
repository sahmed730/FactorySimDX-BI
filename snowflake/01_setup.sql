-- ==========================================
-- MeidenSmart AI - Environment Setup
-- ==========================================

USE ROLE SYSADMIN;

-- Create Warehouse
CREATE OR REPLACE WAREHOUSE MEIDEN_WH
  WITH WAREHOUSE_SIZE = 'X-SMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE;

-- Create Database
CREATE OR REPLACE DATABASE MEIDENSMART_DB;

-- Create Medallion Schemas
CREATE OR REPLACE SCHEMA MEIDENSMART_DB.BRONZE;   -- Raw Ingestion
CREATE OR REPLACE SCHEMA MEIDENSMART_DB.SILVER;   -- Cleansed & Conformed
CREATE OR REPLACE SCHEMA MEIDENSMART_DB.GOLD;     -- Aggregated Business Views

-- Create Internal Stage for CSV Uploads
USE SCHEMA MEIDENSMART_DB.BRONZE;
CREATE OR REPLACE STAGE raw_data_stage
  FILE_FORMAT = (TYPE = 'CSV' FIELD_OPTIONALLY_ENCLOSED_BY = '"' SKIP_HEADER = 1);
