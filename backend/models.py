# backend/models.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Table
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

    location = relationship("Location", back_populates="firs")
    officer = relationship("Officer", back_populates="firs")
    victims = relationship("Victim", back_populates="fir", cascade="all, delete-orphan")
    
    accused_relationships = relationship("FIRAccused", back_populates="fir", cascade="all, delete-orphan")

class Accused(Base):
    __tablename__ = "accused"
    
    accused_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String, nullable=False)
    occupation = Column(String, nullable=False)
    address = Column(String, nullable=False)
    risk_score = Column(Float, nullable=False, default=0.0)

    fir_relationships = relationship("FIRAccused", back_populates="accused", cascade="all, delete-orphan")

class Victim(Base):
    __tablename__ = "victims"
    
    victim_id = Column(Integer, primary_key=True, autoincrement=True)
    fir_id = Column(Integer, ForeignKey("firs.fir_id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String, nullable=False)

    fir = relationship("FIR", back_populates="victims")

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
