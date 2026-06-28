# backend/models.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Table, LargeBinary, Date, DateTime, Boolean
from sqlalchemy.orm import relationship
from backend.database import Base

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False) # 'Investigator', 'Analyst', 'Supervisor', 'Policymaker'
    name = Column(String, nullable=False)

    audit_logs = relationship("AuditLog", back_populates="user")

# --- Administrative Divisions ---

class State(Base):
    __tablename__ = "State"
    StateID = Column(Integer, primary_key=True, autoincrement=True)
    StateName = Column(String(100), nullable=False)
    NationalityID = Column(Integer, nullable=True)
    Active = Column(Boolean, default=True)

class District(Base):
    __tablename__ = "District"
    DistrictID = Column(Integer, primary_key=True, autoincrement=True)
    DistrictName = Column(String(100), nullable=False)
    StateID = Column(Integer, ForeignKey("State.StateID"), nullable=False)
    Active = Column(Boolean, default=True)

class UnitType(Base):
    __tablename__ = "UnitType"
    UnitTypeID = Column(Integer, primary_key=True, autoincrement=True)
    UnitTypeName = Column(String(100), nullable=False)
    CityDistState = Column(String(50), nullable=True)

class Unit(Base):
    __tablename__ = "Unit"
    UnitID = Column(Integer, primary_key=True, autoincrement=True)
    UnitName = Column(String(150), nullable=False)
    TypeID = Column(Integer, ForeignKey("UnitType.UnitTypeID"), nullable=False)
    ParentUnit = Column(Integer, nullable=True)
    StateID = Column(Integer, ForeignKey("State.StateID"), nullable=False)
    DistrictID = Column(Integer, ForeignKey("District.DistrictID"), nullable=False)
    Active = Column(Boolean, default=True)

class Rank(Base):
    __tablename__ = "Rank"
    RankID = Column(Integer, primary_key=True, autoincrement=True)
    RankName = Column(String(100), nullable=False)
    Hierarchy = Column(Integer, nullable=False)
    Active = Column(Boolean, default=True)

class Designation(Base):
    __tablename__ = "Designation"
    DesignationID = Column(Integer, primary_key=True, autoincrement=True)
    DesignationName = Column(String(100), nullable=False)
    Active = Column(Boolean, default=True)
    SortOrder = Column(Integer, nullable=True)

class Employee(Base):
    __tablename__ = "Employee"
    EmployeeID = Column(Integer, primary_key=True, autoincrement=True)
    DistrictID = Column(Integer, ForeignKey("District.DistrictID"), nullable=False)
    UnitID = Column(Integer, ForeignKey("Unit.UnitID"), nullable=False)
    RankID = Column(Integer, ForeignKey("Rank.RankID"), nullable=False)
    DesignationID = Column(Integer, ForeignKey("Designation.DesignationID"), nullable=False)
    KGID = Column(String(50), unique=True, nullable=False)
    FirstName = Column(String(100), nullable=False)
    EmployeeDOB = Column(Date, nullable=True)
    GenderID = Column(Integer, nullable=True)
    BloodGroupID = Column(Integer, nullable=True)
    PhysicallyChallenged = Column(Boolean, default=False)
    AppointmentDate = Column(Date, nullable=True)

# --- Classifications & Master Lookups ---

class CaseCategory(Base):
    __tablename__ = "CaseCategory"
    CaseCategoryID = Column(Integer, primary_key=True, autoincrement=True)
    LookupValue = Column(String(50), nullable=False)

class GravityOffence(Base):
    __tablename__ = "GravityOffence"
    GravityOffenceID = Column(Integer, primary_key=True, autoincrement=True)
    LookupValue = Column(String(50), nullable=False)

class CrimeHead(Base):
    __tablename__ = "CrimeHead"
    CrimeHeadID = Column(Integer, primary_key=True, autoincrement=True)
    CrimeGroupName = Column(String(150), nullable=False)
    Active = Column(Boolean, default=True)

class CrimeSubHead(Base):
    __tablename__ = "CrimeSubHead"
    CrimeSubHeadID = Column(Integer, primary_key=True, autoincrement=True)
    CrimeHeadID = Column(Integer, ForeignKey("CrimeHead.CrimeHeadID"), nullable=False)
    CrimeHeadName = Column(String(150), nullable=False)
    SeqID = Column(Integer, nullable=True)

class Court(Base):
    __tablename__ = "Court"
    CourtID = Column(Integer, primary_key=True, autoincrement=True)
    CourtName = Column(String(150), nullable=False)
    DistrictID = Column(Integer, ForeignKey("District.DistrictID"), nullable=False)
    StateID = Column(Integer, ForeignKey("State.StateID"), nullable=False)
    Active = Column(Boolean, default=True)

class CaseStatusMaster(Base):
    __tablename__ = "CaseStatusMaster"
    CaseStatusID = Column(Integer, primary_key=True, autoincrement=True)
    CaseStatusName = Column(String(100), nullable=False)

# --- Primary Tables (extended for Karnataka FIR Schema) ---

class Location(Base):
    __tablename__ = "locations"
    
    location_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    district = Column(String, nullable=False)
    station_area = Column(String, nullable=False)

    firs = relationship("FIR", back_populates="location")

class Officer(Base):
    __tablename__ = "officers"
    
    officer_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    rank = Column(String, nullable=False)
    station = Column(String, nullable=False)

    firs = relationship("FIR", back_populates="officer")

class FIRAccused(Base):
    __tablename__ = "fir_accused"
    
    fir_id = Column(Integer, ForeignKey("firs.fir_id", ondelete="CASCADE"), primary_key=True)
    accused_id = Column(Integer, ForeignKey("accused.accused_id", ondelete="CASCADE"), primary_key=True)
    role = Column(String, nullable=False) # 'Principal', 'Co-accused', 'Conspirator', 'Suspect'

    fir = relationship("FIR", back_populates="accused_relationships")
    accused = relationship("Accused", back_populates="fir_relationships")

class FIR(Base):
    __tablename__ = "firs"
    
    fir_id = Column(Integer, primary_key=True, autoincrement=True)
    fir_number = Column(String, unique=True, nullable=False)
    date = Column(String, nullable=False) # ISO 8601
    crime_type = Column(String, nullable=False)
    description = Column(String, nullable=False)
    status = Column(String, nullable=False)
    document_reference = Column(String, nullable=True)

    location_id = Column(Integer, ForeignKey("locations.location_id"))
    officer_id = Column(Integer, ForeignKey("officers.officer_id"))

    # New CaseMaster / Karnataka Police Fields --
    CrimeNo = Column(String(50), nullable=True)
    CaseNo = Column(String(50), nullable=True)
    CrimeRegisteredDate = Column(Date, nullable=True)
    PolicePersonID = Column(Integer, ForeignKey("Employee.EmployeeID"), nullable=True)
    PoliceStationID = Column(Integer, ForeignKey("Unit.UnitID"), nullable=True)
    CaseCategoryID = Column(Integer, ForeignKey("CaseCategory.CaseCategoryID"), nullable=True)
    GravityOffenceID = Column(Integer, ForeignKey("GravityOffence.GravityOffenceID"), nullable=True)
    CrimeMajorHeadID = Column(Integer, ForeignKey("CrimeHead.CrimeHeadID"), nullable=True)
    CrimeMinorHeadID = Column(Integer, ForeignKey("CrimeSubHead.CrimeSubHeadID"), nullable=True)
    CaseStatusID = Column(Integer, ForeignKey("CaseStatusMaster.CaseStatusID"), nullable=True)
    CourtID = Column(Integer, ForeignKey("Court.CourtID"), nullable=True)
    IncidentFromDate = Column(DateTime, nullable=True)
    IncidentToDate = Column(DateTime, nullable=True)
    InfoReceivedPSDate = Column(DateTime, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    BriefFacts = Column(String, nullable=True)
    is_deleted = Column(Boolean, default=False)
    version_no = Column(Integer, default=1)

    location = relationship("Location", back_populates="firs")
    officer = relationship("Officer", back_populates="firs")
    victims = relationship("Victim", back_populates="fir", cascade="all, delete-orphan", foreign_keys="[Victim.fir_id]")
    embedding_rel = relationship("FIREmbedding", back_populates="fir", uselist=False, cascade="all, delete-orphan")
    accused_relationships = relationship("FIRAccused", back_populates="fir", cascade="all, delete-orphan")

# Alias CaseMaster to FIR class for conceptual alignment
CaseMaster = FIR

# --- Complainant, Victim, Accused and Relationships ---

class OccupationMaster(Base):
    __tablename__ = "OccupationMaster"
    OccupationID = Column(Integer, primary_key=True, autoincrement=True)
    OccupationName = Column(String(100), nullable=False)

class ReligionMaster(Base):
    __tablename__ = "ReligionMaster"
    ReligionID = Column(Integer, primary_key=True, autoincrement=True)
    ReligionName = Column(String(100), nullable=False)

class CasteMaster(Base):
    __tablename__ = "CasteMaster"
    caste_master_id = Column(Integer, primary_key=True, autoincrement=True)
    caste_master_name = Column(String(100), nullable=False)

class ComplainantDetails(Base):
    __tablename__ = "ComplainantDetails"
    ComplainantID = Column(Integer, primary_key=True, autoincrement=True)
    CaseMasterID = Column(Integer, ForeignKey("firs.fir_id", ondelete="CASCADE"), nullable=False)
    ComplainantName = Column(String(150), nullable=False)
    AgeYear = Column(Integer, nullable=True)
    OccupationID = Column(Integer, ForeignKey("OccupationMaster.OccupationID"), nullable=True)
    ReligionID = Column(Integer, ForeignKey("ReligionMaster.ReligionID"), nullable=True)
    CasteID = Column(Integer, ForeignKey("CasteMaster.caste_master_id"), nullable=True)
    GenderID = Column(Integer, nullable=True)

class Accused(Base):
    __tablename__ = "accused"
    
    accused_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String, nullable=False)
    occupation = Column(String, nullable=False)
    address = Column(String, nullable=False)
    risk_score = Column(Float, nullable=False, default=0.0)

    # New Accused Fields --
    AccusedMasterID = Column(Integer, nullable=True)
    CaseMasterID = Column(Integer, ForeignKey("firs.fir_id", ondelete="CASCADE"), nullable=True)
    AccusedName = Column(String(150), nullable=True)
    AgeYear = Column(Integer, nullable=True)
    GenderID = Column(Integer, nullable=True)
    PersonID = Column(String(50), nullable=True)

    fir_relationships = relationship("FIRAccused", back_populates="accused", cascade="all, delete-orphan")

class Victim(Base):
    __tablename__ = "victims"
    
    victim_id = Column(Integer, primary_key=True, autoincrement=True)
    fir_id = Column(Integer, ForeignKey("firs.fir_id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String, nullable=False)

    # New Victim Fields --
    VictimMasterID = Column(Integer, nullable=True)
    CaseMasterID = Column(Integer, ForeignKey("firs.fir_id", ondelete="CASCADE"), nullable=True)
    VictimName = Column(String(150), nullable=True)
    AgeYear = Column(Integer, nullable=True)
    GenderID = Column(Integer, nullable=True)
    VictimPolice = Column(String(1), default="0")

    fir = relationship("FIR", back_populates="victims", foreign_keys="[Victim.fir_id]")

# --- Legal Acts and Sections mapping ---

class Act(Base):
    __tablename__ = "Act"
    ActCode = Column(String(50), primary_key=True)
    ActDescription = Column(String(250), nullable=False)
    ShortName = Column(String(100), nullable=True)
    Active = Column(Boolean, default=True)

class Section(Base):
    __tablename__ = "Section"
    ActCode = Column(String(50), ForeignKey("Act.ActCode", ondelete="CASCADE"), primary_key=True)
    SectionCode = Column(String(50), primary_key=True)
    SectionDescription = Column(String, nullable=True)
    Active = Column(Boolean, default=True)

class ActSectionAssociation(Base):
    __tablename__ = "ActSectionAssociation"
    CaseMasterID = Column(Integer, ForeignKey("firs.fir_id", ondelete="CASCADE"), primary_key=True)
    ActID = Column(String(50), primary_key=True)
    SectionID = Column(String(50), primary_key=True)
    ActOrderID = Column(Integer, nullable=True)
    SectionOrderID = Column(Integer, nullable=True)

class CrimeHeadActSection(Base):
    __tablename__ = "CrimeHeadActSection"
    CrimeHeadID = Column(Integer, ForeignKey("CrimeHead.CrimeHeadID", ondelete="CASCADE"), primary_key=True)
    ActCode = Column(String(50), primary_key=True)
    SectionCode = Column(String(50), primary_key=True)

# --- Case Processing: Chargesheets, Arrests ---

class ChargesheetDetails(Base):
    __tablename__ = "ChargesheetDetails"
    CSID = Column(Integer, primary_key=True, autoincrement=True)
    CaseMasterID = Column(Integer, ForeignKey("firs.fir_id", ondelete="CASCADE"), unique=True, nullable=False)
    csdate = Column(DateTime, nullable=False)
    cstype = Column(String(1), nullable=False) # A, B, C
    PolicePersonID = Column(Integer, ForeignKey("Employee.EmployeeID"), nullable=False)

class ArrestSurrender(Base):
    __tablename__ = "ArrestSurrender"
    ArrestSurrenderID = Column(Integer, primary_key=True, autoincrement=True)
    CaseMasterID = Column(Integer, ForeignKey("firs.fir_id", ondelete="CASCADE"), nullable=False)
    ArrestSurrenderTypeID = Column(Integer, nullable=False)
    ArrestSurrenderDate = Column(Date, nullable=False)
    ArrestSurrenderStateId = Column(Integer, ForeignKey("State.StateID"), nullable=False)
    ArrestSurrenderDistrictId = Column(Integer, ForeignKey("District.DistrictID"), nullable=False)
    PoliceStationID = Column(Integer, ForeignKey("Unit.UnitID"), nullable=False)
    IOID = Column(Integer, ForeignKey("Employee.EmployeeID"), nullable=False)
    CourtID = Column(Integer, ForeignKey("Court.CourtID"), nullable=False)
    AccusedMasterID = Column(Integer, ForeignKey("accused.accused_id", ondelete="CASCADE"), nullable=False)
    IsAccused = Column(Boolean, default=True)
    IsComplainantAccused = Column(Boolean, default=False)

# --- Caching and Audits ---

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    log_id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    username = Column(String, nullable=False)
    role = Column(String, nullable=False)
    query = Column(String, nullable=False)
    intent = Column(String, nullable=False)
    entities = Column(String, nullable=False) # JSON String
    generated_sql = Column(String, nullable=False)
    rows_returned = Column(Integer, nullable=False)
    summary = Column(String, nullable=False)
    execution_time = Column(Float, nullable=False)

    user = relationship("User", back_populates="audit_logs")

class FIREmbedding(Base):
    __tablename__ = "fir_embeddings"
    
    fir_id = Column(Integer, ForeignKey("firs.fir_id", ondelete="CASCADE"), primary_key=True)
    embedding = Column(LargeBinary, nullable=False)
    
    fir = relationship("FIR", back_populates="embedding_rel")

# Phase 3 Analytical Feature Mapping Models
class FeatureStore(Base):
    __tablename__ = "feature_store"
    
    entity_type = Column(String, primary_key=True)
    entity_id = Column(String, primary_key=True)
    feature_name = Column(String, primary_key=True)
    feature_value = Column(Float, nullable=False)
    timestamp = Column(String, primary_key=True)
    pipeline_version = Column(String, nullable=False)
    feature_version = Column(Integer, nullable=False)
    generated_at = Column(String, nullable=False)
    generated_by = Column(String, nullable=False)
    is_target = Column(Integer, nullable=False, default=0)

class CentralityMetrics(Base):
    __tablename__ = "centrality_metrics"
    
    node_id = Column(String, primary_key=True)
    pagerank = Column(Float, nullable=False)
    betweenness = Column(Float, nullable=False)
    degree = Column(Float, nullable=False)
    closeness = Column(Float, nullable=False)
    bridge_score = Column(Float, nullable=False)
    updated_at = Column(String, nullable=False)

class CommunityAnalysis(Base):
    __tablename__ = "community_analysis"
    
    node_id = Column(String, primary_key=True)
    community_id = Column(Integer, nullable=False)
    community_size = Column(Integer, nullable=False)
    modularity = Column(Float, nullable=False)
    component_id = Column(Integer, nullable=False)
    updated_at = Column(String, nullable=False)

class HotspotCluster(Base):
    __tablename__ = "hotspot_clusters"
    
    cluster_id = Column(Integer, primary_key=True)
    cluster_size = Column(Integer, nullable=False)
    crime_density = Column(Float, nullable=False)
    centroid_lat = Column(Float, nullable=False)
    centroid_lng = Column(Float, nullable=False)
    cluster_risk = Column(Float, nullable=False)
    repeat_offender_density = Column(Float, nullable=False)
    severity_density = Column(Float, nullable=False)
    emerging_hotspot_score = Column(Float, nullable=False)
    historical_baseline = Column(Float, nullable=False)
    weekly_change = Column(Float, nullable=False)
    future_cluster_size = Column(Integer, nullable=True)
    weekly_growth = Column(Integer, nullable=True)
    updated_at = Column(String, nullable=False)
