-- schema.sql
-- SIDDHI V2 Database Schema
-- Unified for Backwards-Compatibility and Karnataka Police FIR Schema alignment

-- Users table for Authentication and Role-Based Access Control (RBAC)
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT CHECK(role IN ('Investigator', 'Analyst', 'Supervisor', 'Policymaker')) NOT NULL,
    name TEXT NOT NULL
);

-- Administrative boundaries
CREATE TABLE IF NOT EXISTS State (
    StateID INTEGER PRIMARY KEY AUTOINCREMENT,
    StateName VARCHAR(100) NOT NULL,
    NationalityID INTEGER,
    Active BIT DEFAULT 1
);

CREATE TABLE IF NOT EXISTS District (
    DistrictID INTEGER PRIMARY KEY AUTOINCREMENT,
    DistrictName VARCHAR(100) NOT NULL,
    StateID INTEGER NOT NULL,
    Active BIT DEFAULT 1,
    FOREIGN KEY(StateID) REFERENCES State(StateID)
);

CREATE TABLE IF NOT EXISTS UnitType (
    UnitTypeID INTEGER PRIMARY KEY AUTOINCREMENT,
    UnitTypeName VARCHAR(100) NOT NULL,
    CityDistState VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS Unit (
    UnitID INTEGER PRIMARY KEY AUTOINCREMENT,
    UnitName VARCHAR(150) NOT NULL,
    TypeID INTEGER NOT NULL,
    ParentUnit INTEGER,
    StateID INTEGER NOT NULL,
    DistrictID INTEGER NOT NULL,
    Active BIT DEFAULT 1,
    FOREIGN KEY(TypeID) REFERENCES UnitType(UnitTypeID),
    FOREIGN KEY(StateID) REFERENCES State(StateID),
    FOREIGN KEY(DistrictID) REFERENCES District(DistrictID)
);

CREATE TABLE IF NOT EXISTS Rank (
    RankID INTEGER PRIMARY KEY AUTOINCREMENT,
    RankName VARCHAR(100) NOT NULL,
    Hierarchy INTEGER NOT NULL,
    Active BIT DEFAULT 1
);

CREATE TABLE IF NOT EXISTS Designation (
    DesignationID INTEGER PRIMARY KEY AUTOINCREMENT,
    DesignationName VARCHAR(100) NOT NULL,
    Active BIT DEFAULT 1,
    SortOrder INTEGER
);

CREATE TABLE IF NOT EXISTS Employee (
    EmployeeID INTEGER PRIMARY KEY AUTOINCREMENT,
    DistrictID INTEGER NOT NULL,
    UnitID INTEGER NOT NULL,
    RankID INTEGER NOT NULL,
    DesignationID INTEGER NOT NULL,
    KGID VARCHAR(50) UNIQUE NOT NULL, -- Karnataka Government ID
    FirstName VARCHAR(100) NOT NULL,
    EmployeeDOB DATE,
    GenderID INTEGER,
    BloodGroupID INTEGER,
    PhysicallyChallenged BIT DEFAULT 0,
    AppointmentDate DATE,
    FOREIGN KEY(DistrictID) REFERENCES District(DistrictID),
    FOREIGN KEY(UnitID) REFERENCES Unit(UnitID),
    FOREIGN KEY(RankID) REFERENCES Rank(RankID),
    FOREIGN KEY(DesignationID) REFERENCES Designation(DesignationID)
);

-- Crime Categories & Classifications
CREATE TABLE IF NOT EXISTS CaseCategory (
    CaseCategoryID INTEGER PRIMARY KEY AUTOINCREMENT,
    LookupValue VARCHAR(50) NOT NULL -- FIR, UDR, Zero FIR, PAR
);

CREATE TABLE IF NOT EXISTS GravityOffence (
    GravityOffenceID INTEGER PRIMARY KEY AUTOINCREMENT,
    LookupValue VARCHAR(50) NOT NULL -- Heinous, Non-Heinous
);

CREATE TABLE IF NOT EXISTS CrimeHead (
    CrimeHeadID INTEGER PRIMARY KEY AUTOINCREMENT,
    CrimeGroupName VARCHAR(150) NOT NULL,
    Active BIT DEFAULT 1
);

CREATE TABLE IF NOT EXISTS CrimeSubHead (
    CrimeSubHeadID INTEGER PRIMARY KEY AUTOINCREMENT,
    CrimeHeadID INTEGER NOT NULL,
    CrimeHeadName VARCHAR(150) NOT NULL,
    SeqID INTEGER,
    FOREIGN KEY(CrimeHeadID) REFERENCES CrimeHead(CrimeHeadID)
);

CREATE TABLE IF NOT EXISTS Court (
    CourtID INTEGER PRIMARY KEY AUTOINCREMENT,
    CourtName VARCHAR(150) NOT NULL,
    DistrictID INTEGER NOT NULL,
    StateID INTEGER NOT NULL,
    Active BIT DEFAULT 1,
    FOREIGN KEY(DistrictID) REFERENCES District(DistrictID),
    FOREIGN KEY(StateID) REFERENCES State(StateID)
);

CREATE TABLE IF NOT EXISTS CaseStatusMaster (
    CaseStatusID INTEGER PRIMARY KEY AUTOINCREMENT,
    CaseStatusName VARCHAR(100) NOT NULL
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

-- First Information Reports / CaseMaster (corresponds to firs)
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
    
    -- New Karnataka Police CaseMaster Fields
    CrimeNo VARCHAR(50),
    CaseNo VARCHAR(50),
    CrimeRegisteredDate DATE,
    PolicePersonID INTEGER,
    PoliceStationID INTEGER,
    CaseCategoryID INTEGER,
    GravityOffenceID INTEGER,
    CrimeMajorHeadID INTEGER,
    CrimeMinorHeadID INTEGER,
    CaseStatusID INTEGER,
    CourtID INTEGER,
    IncidentFromDate DATETIME,
    IncidentToDate DATETIME,
    InfoReceivedPSDate DATETIME,
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6),
    BriefFacts TEXT,
    is_deleted BIT DEFAULT 0,
    version_no INTEGER DEFAULT 1,
    
    FOREIGN KEY(location_id) REFERENCES locations(location_id) ON DELETE RESTRICT,
    FOREIGN KEY(officer_id) REFERENCES officers(officer_id) ON DELETE RESTRICT,
    FOREIGN KEY(PolicePersonID) REFERENCES Employee(EmployeeID),
    FOREIGN KEY(PoliceStationID) REFERENCES Unit(UnitID),
    FOREIGN KEY(CaseCategoryID) REFERENCES CaseCategory(CaseCategoryID),
    FOREIGN KEY(GravityOffenceID) REFERENCES GravityOffence(GravityOffenceID),
    FOREIGN KEY(CrimeMajorHeadID) REFERENCES CrimeHead(CrimeHeadID),
    FOREIGN KEY(CrimeMinorHeadID) REFERENCES CrimeSubHead(CrimeSubHeadID),
    FOREIGN KEY(CaseStatusID) REFERENCES CaseStatusMaster(CaseStatusID),
    FOREIGN KEY(CourtID) REFERENCES Court(CourtID)
);

-- Complainant, Victim, Accused lookup masters
CREATE TABLE IF NOT EXISTS OccupationMaster (
    OccupationID INTEGER PRIMARY KEY AUTOINCREMENT,
    OccupationName VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS ReligionMaster (
    ReligionID INTEGER PRIMARY KEY AUTOINCREMENT,
    ReligionName VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS CasteMaster (
    caste_master_id INTEGER PRIMARY KEY AUTOINCREMENT,
    caste_master_name VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS ComplainantDetails (
    ComplainantID INTEGER PRIMARY KEY AUTOINCREMENT,
    CaseMasterID INTEGER NOT NULL,
    ComplainantName VARCHAR(150) NOT NULL,
    AgeYear INTEGER,
    OccupationID INTEGER,
    ReligionID INTEGER,
    CasteID INTEGER,
    GenderID INTEGER,
    FOREIGN KEY(CaseMasterID) REFERENCES firs(fir_id) ON DELETE CASCADE,
    FOREIGN KEY(OccupationID) REFERENCES OccupationMaster(OccupationID),
    FOREIGN KEY(ReligionID) REFERENCES ReligionMaster(ReligionID),
    FOREIGN KEY(CasteID) REFERENCES CasteMaster(caste_master_id)
);

-- Crime Victims
CREATE TABLE IF NOT EXISTS victims (
    victim_id INTEGER PRIMARY KEY AUTOINCREMENT,
    fir_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    age INTEGER NOT NULL,
    gender TEXT NOT NULL,
    
    -- New Karnataka Police Victim Fields
    VictimMasterID INTEGER,
    CaseMasterID INTEGER,
    VictimName VARCHAR(150),
    AgeYear INTEGER,
    GenderID INTEGER,
    VictimPolice VARCHAR(1) DEFAULT '0',
    
    FOREIGN KEY(fir_id) REFERENCES firs(fir_id) ON DELETE CASCADE,
    FOREIGN KEY(CaseMasterID) REFERENCES firs(fir_id) ON DELETE CASCADE
);

-- Accused individuals details
CREATE TABLE IF NOT EXISTS accused (
    accused_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    age INTEGER NOT NULL,
    gender TEXT NOT NULL,
    occupation TEXT NOT NULL,
    address TEXT NOT NULL,
    risk_score REAL NOT NULL DEFAULT 0.0,
    
    -- New Karnataka Police Accused Fields
    AccusedMasterID INTEGER,
    CaseMasterID INTEGER,
    AccusedName VARCHAR(150),
    AgeYear INTEGER,
    GenderID INTEGER,
    PersonID VARCHAR(50),
    
    FOREIGN KEY(CaseMasterID) REFERENCES firs(fir_id) ON DELETE CASCADE
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

-- Chargesheet & Arrest details
CREATE TABLE IF NOT EXISTS ChargesheetDetails (
    CSID INTEGER PRIMARY KEY AUTOINCREMENT,
    CaseMasterID INTEGER UNIQUE NOT NULL,
    csdate DATETIME NOT NULL,
    cstype CHAR(1) NOT NULL, -- A->Chargesheet, B->False Case, C->Undetected
    PolicePersonID INTEGER NOT NULL,
    FOREIGN KEY(CaseMasterID) REFERENCES firs(fir_id) ON DELETE CASCADE,
    FOREIGN KEY(PolicePersonID) REFERENCES Employee(EmployeeID)
);

CREATE TABLE IF NOT EXISTS ArrestSurrender (
    ArrestSurrenderID INTEGER PRIMARY KEY AUTOINCREMENT,
    CaseMasterID INTEGER NOT NULL,
    ArrestSurrenderTypeID INTEGER NOT NULL,
    ArrestSurrenderDate DATE NOT NULL,
    ArrestSurrenderStateId INTEGER NOT NULL,
    ArrestSurrenderDistrictId INTEGER NOT NULL,
    PoliceStationID INTEGER NOT NULL,
    IOID INTEGER NOT NULL,
    CourtID INTEGER NOT NULL,
    AccusedMasterID INTEGER NOT NULL,
    IsAccused BIT DEFAULT 1,
    IsComplainantAccused BIT DEFAULT 0,
    FOREIGN KEY(CaseMasterID) REFERENCES firs(fir_id) ON DELETE CASCADE,
    FOREIGN KEY(ArrestSurrenderStateId) REFERENCES State(StateID),
    FOREIGN KEY(ArrestSurrenderDistrictId) REFERENCES District(DistrictID),
    FOREIGN KEY(PoliceStationID) REFERENCES Unit(UnitID),
    FOREIGN KEY(IOID) REFERENCES Employee(EmployeeID),
    FOREIGN KEY(CourtID) REFERENCES Court(CourtID),
    FOREIGN KEY(AccusedMasterID) REFERENCES accused(accused_id) ON DELETE CASCADE
);

-- Acts & Sections mapping
CREATE TABLE IF NOT EXISTS Act (
    ActCode VARCHAR(50) PRIMARY KEY,
    ActDescription VARCHAR(250) NOT NULL,
    ShortName VARCHAR(100),
    Active BIT DEFAULT 1
);

CREATE TABLE IF NOT EXISTS Section (
    ActCode VARCHAR(50) NOT NULL,
    SectionCode VARCHAR(50) NOT NULL,
    SectionDescription TEXT,
    Active BIT DEFAULT 1,
    PRIMARY KEY(ActCode, SectionCode),
    FOREIGN KEY(ActCode) REFERENCES Act(ActCode) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS ActSectionAssociation (
    CaseMasterID INTEGER NOT NULL,
    ActID VARCHAR(50) NOT NULL,
    SectionID VARCHAR(50) NOT NULL,
    ActOrderID INTEGER,
    SectionOrderID INTEGER,
    PRIMARY KEY(CaseMasterID, ActID, SectionID),
    FOREIGN KEY(CaseMasterID) REFERENCES firs(fir_id) ON DELETE CASCADE,
    FOREIGN KEY(ActID, SectionID) REFERENCES Section(ActCode, SectionCode) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS CrimeHeadActSection (
    CrimeHeadID INTEGER NOT NULL,
    ActCode VARCHAR(50) NOT NULL,
    SectionCode VARCHAR(50) NOT NULL,
    PRIMARY KEY(CrimeHeadID, ActCode, SectionCode),
    FOREIGN KEY(CrimeHeadID) REFERENCES CrimeHead(CrimeHeadID) ON DELETE CASCADE,
    FOREIGN KEY(ActCode, SectionCode) REFERENCES Section(ActCode, SectionCode) ON DELETE CASCADE
);

-- Vector Search embeddings (preserves fir_embeddings, now links to firs)
CREATE TABLE IF NOT EXISTS fir_embeddings (
    fir_id INTEGER PRIMARY KEY,
    embedding BLOB NOT NULL,
    FOREIGN KEY(fir_id) REFERENCES firs(fir_id) ON DELETE CASCADE
);

-- Operations and Security Audit Logs
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

-- Gemini cache
CREATE TABLE IF NOT EXISTS gemini_cache (
    cache_key TEXT PRIMARY KEY,
    prompt TEXT,
    system_instruction TEXT,
    is_json INTEGER,
    response_text TEXT,
    timestamp TEXT
);

-- Database Indexes for high performance
CREATE INDEX IF NOT EXISTS idx_firs_crime_type ON firs(crime_type);
CREATE INDEX IF NOT EXISTS idx_firs_date ON firs(date);
CREATE INDEX IF NOT EXISTS idx_locations_lat_lng ON locations(lat, lng);
CREATE INDEX IF NOT EXISTS idx_fir_accused_accused_id ON fir_accused(accused_id);
CREATE INDEX IF NOT EXISTS idx_fir_accused_fir_id ON fir_accused(fir_id);
CREATE INDEX IF NOT EXISTS idx_victims_fir_id ON victims(fir_id);
CREATE INDEX IF NOT EXISTS idx_firs_crimeno ON firs(CrimeNo);
CREATE INDEX IF NOT EXISTS idx_firs_coords ON firs(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_accused_name ON accused(AccusedName);
CREATE INDEX IF NOT EXISTS idx_actsec_case ON ActSectionAssociation(CaseMasterID);

-- Phase 3 Analytical Feature Store and Modeling Tables
CREATE TABLE IF NOT EXISTS feature_store (
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    feature_name TEXT NOT NULL,
    feature_value REAL NOT NULL,
    timestamp TEXT NOT NULL,
    pipeline_version TEXT NOT NULL,
    feature_version INTEGER NOT NULL,
    generated_at TEXT NOT NULL,
    generated_by TEXT NOT NULL,
    is_target INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY(entity_type, entity_id, feature_name, timestamp)
);

CREATE TABLE IF NOT EXISTS centrality_metrics (
    node_id TEXT PRIMARY KEY,
    pagerank REAL NOT NULL,
    betweenness REAL NOT NULL,
    degree REAL NOT NULL,
    closeness REAL NOT NULL,
    bridge_score REAL NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS community_analysis (
    node_id TEXT PRIMARY KEY,
    community_id INTEGER NOT NULL,
    community_size INTEGER NOT NULL,
    modularity REAL NOT NULL,
    component_id INTEGER NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS hotspot_clusters (
    cluster_id INTEGER PRIMARY KEY,
    cluster_size INTEGER NOT NULL,
    crime_density REAL NOT NULL,
    centroid_lat REAL NOT NULL,
    centroid_lng REAL NOT NULL,
    cluster_risk REAL NOT NULL,
    repeat_offender_density REAL NOT NULL,
    severity_density REAL NOT NULL,
    emerging_hotspot_score REAL NOT NULL,
    historical_baseline REAL NOT NULL,
    weekly_change REAL NOT NULL,
    future_cluster_size INTEGER,
    weekly_growth INTEGER,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_feature_store_lookup ON feature_store(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_feature_store_name ON feature_store(feature_name);
CREATE INDEX IF NOT EXISTS idx_community_analysis_id ON community_analysis(community_id);
CREATE INDEX IF NOT EXISTS idx_centrality_metrics_val ON centrality_metrics(pagerank, betweenness);
