-- schema.sql
-- SIDDHI Database Schema

-- Users table for Authentication and Role-Based Access Control (RBAC)
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT CHECK(role IN ('Investigator', 'Analyst', 'Supervisor', 'Policymaker')) NOT NULL,
    name TEXT NOT NULL
);

-- Locations details (coordinates and administrative areas)
CREATE TABLE IF NOT EXISTS locations (
    location_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    lat REAL NOT NULL,
    lng REAL NOT NULL,
    district TEXT NOT NULL,
    station_area TEXT NOT NULL
);

-- Officers details
CREATE TABLE IF NOT EXISTS officers (
    officer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    rank TEXT NOT NULL,
    station TEXT NOT NULL
);

-- First Information Reports (FIRs)
CREATE TABLE IF NOT EXISTS firs (
    fir_id INTEGER PRIMARY KEY AUTOINCREMENT,
    fir_number TEXT UNIQUE NOT NULL,
    date TEXT NOT NULL, -- ISO 8601 Date (YYYY-MM-DD)
    crime_type TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('Draft', 'Open', 'Under Investigation', 'Chargesheet Filed', 'Closed')),
    document_reference TEXT,
    location_id INTEGER NOT NULL,
    officer_id INTEGER NOT NULL,
    FOREIGN KEY(location_id) REFERENCES locations(location_id) ON DELETE RESTRICT,
    FOREIGN KEY(officer_id) REFERENCES officers(officer_id) ON DELETE RESTRICT
);

-- Accused individuals details
CREATE TABLE IF NOT EXISTS accused (
    accused_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    age INTEGER NOT NULL,
    gender TEXT NOT NULL,
    occupation TEXT NOT NULL,
    address TEXT NOT NULL,
    risk_score REAL NOT NULL DEFAULT 0.0
);

-- Relationship mapping between FIRs and Accused (Repeat offender connections)
CREATE TABLE IF NOT EXISTS fir_accused (
    fir_id INTEGER NOT NULL,
    accused_id INTEGER NOT NULL,
    role TEXT NOT NULL, -- 'Principal', 'Co-accused', 'Conspirator', 'Suspect'
    PRIMARY KEY(fir_id, accused_id),
    FOREIGN KEY(fir_id) REFERENCES firs(fir_id) ON DELETE CASCADE,
    FOREIGN KEY(accused_id) REFERENCES accused(accused_id) ON DELETE CASCADE
);

-- Crime Victims
CREATE TABLE IF NOT EXISTS victims (
    victim_id INTEGER PRIMARY KEY AUTOINCREMENT,
    fir_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    age INTEGER NOT NULL,
    gender TEXT NOT NULL,
    FOREIGN KEY(fir_id) REFERENCES firs(fir_id) ON DELETE CASCADE
);

-- Operations and Security Audit Logs (Hardened for detailed analysis)
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    user_id INTEGER,
    username TEXT NOT NULL,
    role TEXT NOT NULL,
    query TEXT NOT NULL,
    intent TEXT NOT NULL,
    entities TEXT NOT NULL, -- JSON string
    generated_sql TEXT NOT NULL,
    rows_returned INTEGER NOT NULL,
    summary TEXT NOT NULL,
    execution_time REAL NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE SET NULL
);

-- Database Indexes for high performance
CREATE INDEX IF NOT EXISTS idx_firs_crime_type ON firs(crime_type);
CREATE INDEX IF NOT EXISTS idx_firs_date ON firs(date);
CREATE INDEX IF NOT EXISTS idx_locations_lat_lng ON locations(lat, lng);
CREATE INDEX IF NOT EXISTS idx_fir_accused_accused_id ON fir_accused(accused_id);
CREATE INDEX IF NOT EXISTS idx_fir_accused_fir_id ON fir_accused(fir_id);
CREATE INDEX IF NOT EXISTS idx_victims_fir_id ON victims(fir_id);
