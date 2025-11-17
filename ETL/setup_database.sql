-- PostgreSQL Setup Script for ETL Project
-- Run this file in pgAdmin Query Tool or via command line

-- Step 1: Create database (run as postgres user)
-- Note: If database already exists, you'll get an error - that's okay, skip to Step 2
CREATE DATABASE etl_db
    WITH 
    ENCODING = 'UTF8'
    LC_COLLATE = 'English_United States.1252'
    LC_CTYPE = 'English_United States.1252'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

-- Step 2: Create user (run as postgres user)
-- Note: Change the password to something secure!
CREATE USER etl_user WITH PASSWORD 'etl_password_123';

-- Step 3: Grant permissions
GRANT ALL PRIVILEGES ON DATABASE etl_db TO etl_user;

-- Step 4: Connect to etl_db database
-- In pgAdmin: Select etl_db from database dropdown at top
-- In psql: Run: \c etl_db

-- Step 5: Grant schema permissions (must be connected to etl_db)
GRANT ALL ON SCHEMA public TO etl_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO etl_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO etl_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO etl_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO etl_user;

-- Verification query - run this to check if user and database exist
SELECT 
    'Database created' as status,
    datname as database_name
FROM pg_database 
WHERE datname = 'etl_db'
UNION ALL
SELECT 
    'User created' as status,
    usename as user_name
FROM pg_user 
WHERE usename = 'etl_user';
