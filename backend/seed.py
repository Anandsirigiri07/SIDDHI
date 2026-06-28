# backend/seed.py
import os
import secrets
import sys
import random
from datetime import datetime, timedelta
from faker import Faker
import bcrypt
from sqlalchemy import text
from sqlalchemy.orm import Session

# Load .env file manually if exists
for env_dir in [os.path.dirname(__file__), os.path.join(os.path.dirname(__file__), "..")]:
    env_path = os.path.join(env_dir, ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        os.environ[k.strip()] = v.strip()
        except Exception as e:
            print(f"Error loading .env from {env_path}: {e}")

# Add the project root to path to run from within siddhi/ or siddhi/backend/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database import engine, SessionLocal
from backend.models import (
    User, Location, Officer, Accused, FIR, FIRAccused, Victim,
    State, District, UnitType, Unit, Rank, Designation, Employee,
    CaseCategory, GravityOffence, CrimeHead, CrimeSubHead, Court,
    CaseStatusMaster, OccupationMaster, ReligionMaster, CasteMaster,
    ComplainantDetails, ChargesheetDetails, ArrestSurrender, Act, Section,
    ActSectionAssociation, CrimeHeadActSection
)
from backend.config.crime_weights import CRIME_SEVERITY

fake = Faker('en_IN') # Indian localized names/addresses

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def init_db_from_schema():
    # Remove old SQLite file if it exists to refresh schema cleanly
    from backend.database import DATABASE_URL
    if DATABASE_URL.startswith("sqlite:///"):
        db_file = DATABASE_URL.replace("sqlite:///", "")
    else:
        db_file = "siddhi.db"
    
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
            print(f"Deleted old SQLite file '{db_file}' to refresh schema.")
        except Exception as e:
            print(f"Could not remove database file '{db_file}': {e}")
            
    print("Initializing database schema from schema.sql...")
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, "r") as f:
        schema_sql = f.read()

    # Get raw DBAPI connection to execute multiple statements
    raw_conn = engine.raw_connection()
    try:
        cursor = raw_conn.cursor()
        # executescript is SQLite specific
        if hasattr(raw_conn, 'executescript'):
            raw_conn.executescript(schema_sql)
        else:
            # PostgreSQL or standard SQL engine connection
            statements = schema_sql.split(";")
            for statement in statements:
                if statement.strip():
                    cursor.execute(statement)
            raw_conn.commit()
        print("Schema loaded successfully.")
    except Exception as e:
        print(f"Error executing schema.sql: {e}")
        raw_conn.rollback()
        raise e
    finally:
        raw_conn.close()

def seed_data():
    db: Session = SessionLocal()
    try:
        # 1. Seed Demo Users (opt-in only: set SEED_DEMO_USERS=true)
        if os.getenv("SEED_DEMO_USERS", "false").strip().lower() in ("1", "true", "yes"):
            print("Seeding users...")
            demo_password = os.getenv("DEMO_USER_PASSWORD", "password123")
            demo_users = [
                {"username": "investigator", "password": demo_password, "role": "Investigator", "name": "Inspector Suresh Kumar"},
                {"username": "analyst", "password": demo_password, "role": "Analyst", "name": "Dr. Ananya Sen (Crime Analyst)"},
                {"username": "supervisor", "password": demo_password, "role": "Supervisor", "name": "ACP Rajesh Patil"},
                {"username": "policymaker", "password": demo_password, "role": "Policymaker", "name": "DGP K. R. Rao"}
            ]
            for du in demo_users:
                existing = db.query(User).filter_by(username=du["username"]).first()
                if not existing:
                    u = User(
                        username=du["username"],
                        password_hash=hash_password(du["password"]),
                        role=du["role"],
                        name=du["name"]
                    )
                    db.add(u)
            db.commit()

        # 2. Seed Lookups and Master Tables
        print("Seeding lookups and master tables...")
        
        # State
        karnataka = State(StateName="Karnataka", NationalityID=1, Active=True)
        db.add(karnataka)
        db.flush()

        # District
        bengaluru_east = District(DistrictName="Bengaluru East", StateID=karnataka.StateID, Active=True)
        bengaluru_south = District(DistrictName="Bengaluru South", StateID=karnataka.StateID, Active=True)
        bengaluru_north = District(DistrictName="Bengaluru North", StateID=karnataka.StateID, Active=True)
        bengaluru_central = District(DistrictName="Bengaluru Central", StateID=karnataka.StateID, Active=True)
        db.add(bengaluru_east)
        db.add(bengaluru_south)
        db.add(bengaluru_north)
        db.add(bengaluru_central)
        db.flush()

        # UnitType
        ut_station = UnitType(UnitTypeName="Police Station", CityDistState="City")
        db.add(ut_station)
        db.flush()

        # CaseCategory
        cat_fir = CaseCategory(LookupValue="FIR")
        cat_udr = CaseCategory(LookupValue="UDR")
        cat_zero = CaseCategory(LookupValue="Zero FIR")
        cat_par = CaseCategory(LookupValue="PAR")
        db.add(cat_fir)
        db.add(cat_udr)
        db.add(cat_zero)
        db.add(cat_par)
        db.flush()

        # GravityOffence
        gravity_heinous = GravityOffence(LookupValue="Heinous")
        gravity_non_heinous = GravityOffence(LookupValue="Non-Heinous")
        db.add(gravity_heinous)
        db.add(gravity_non_heinous)
        db.flush()

        # Ranks
        rank_constable = Rank(RankName="Police Constable", Hierarchy=10, Active=True)
        rank_psi = Rank(RankName="Police Sub-Inspector", Hierarchy=5, Active=True)
        rank_inspector = Rank(RankName="Inspector of Police", Hierarchy=3, Active=True)
        rank_acp = Rank(RankName="Assistant Commissioner of Police", Hierarchy=1, Active=True)
        db.add(rank_constable)
        db.add(rank_psi)
        db.add(rank_inspector)
        db.add(rank_acp)
        db.flush()

        # Designations
        des_sho = Designation(DesignationName="Station House Officer (SHO)", Active=True, SortOrder=1)
        des_io = Designation(DesignationName="Investigating Officer (IO)", Active=True, SortOrder=2)
        db.add(des_sho)
        db.add(des_io)
        db.flush()

        # Crime Heads and Sub Heads
        ch_body = CrimeHead(CrimeGroupName="Crimes Against Body", Active=True)
        ch_property = CrimeHead(CrimeGroupName="Crimes Against Property", Active=True)
        ch_public = CrimeHead(CrimeGroupName="Crimes Against Public Order", Active=True)
        ch_cyber = CrimeHead(CrimeGroupName="Cyber Crimes", Active=True)
        ch_women = CrimeHead(CrimeGroupName="Crimes Against Women", Active=True)
        db.add(ch_body)
        db.add(ch_property)
        db.add(ch_public)
        db.add(ch_cyber)
        db.add(ch_women)
        db.flush()

        sub_heads = {
            "chain_snatching": (ch_property.CrimeHeadID, "Chain Snatching", 1),
            "burglary": (ch_property.CrimeHeadID, "Burglary", 2),
            "robbery": (ch_property.CrimeHeadID, "Robbery", 3),
            "vehicle_theft": (ch_property.CrimeHeadID, "Vehicle Theft", 4),
            "assault": (ch_body.CrimeHeadID, "Assault", 5),
            "murder": (ch_body.CrimeHeadID, "Murder", 6),
            "drug_offense": (ch_public.CrimeHeadID, "Narcotic Drug Offense", 7),
            "rioting": (ch_public.CrimeHeadID, "Rioting", 8),
            "cybercrime": (ch_cyber.CrimeHeadID, "Cyber Crime", 9),
            "fraud": (ch_property.CrimeHeadID, "Financial Fraud", 10),
            "women_crime": (ch_women.CrimeHeadID, "Crimes Against Women", 11)
        }
        crime_subheads_map = {}
        for key, (hid, name, seq) in sub_heads.items():
            sh = CrimeSubHead(CrimeHeadID=hid, CrimeHeadName=name, SeqID=seq)
            db.add(sh)
            crime_subheads_map[key] = sh
        db.flush()

        # Courts
        court_1 = Court(CourtName="1st ACMM Court, Bengaluru", DistrictID=bengaluru_central.DistrictID, StateID=karnataka.StateID, Active=True)
        court_2 = Court(CourtName="2nd ACMM Court, Bengaluru East", DistrictID=bengaluru_east.DistrictID, StateID=karnataka.StateID, Active=True)
        db.add(court_1)
        db.add(court_2)
        db.flush()

        # Case Statuses
        status_draft = CaseStatusMaster(CaseStatusName="Draft")
        status_open = CaseStatusMaster(CaseStatusName="Open")
        status_investigating = CaseStatusMaster(CaseStatusName="Under Investigation")
        status_chargesheeted = CaseStatusMaster(CaseStatusName="Chargesheet Filed")
        status_closed = CaseStatusMaster(CaseStatusName="Closed")
        db.add(status_draft)
        db.add(status_open)
        db.add(status_investigating)
        db.add(status_chargesheeted)
        db.add(status_closed)
        db.flush()

        # Occupation, Religion, Caste Masters
        occupations_list = ["Laborer", "Driver", "Delivery Executive", "Unemployed", "Security Guard", "Mechanic", "Local Merchant", "Real Estate Broker"]
        occ_map = {}
        for occ in occupations_list:
            o = OccupationMaster(OccupationName=occ)
            db.add(o)
            occ_map[occ] = o
        
        religions_list = ["Hindu", "Muslim", "Christian", "Sikh", "Jain", "Buddhist"]
        rel_objs = [ReligionMaster(ReligionName=r) for r in religions_list]
        for r in rel_objs:
            db.add(r)
        
        castes_list = ["General", "OBC", "SC", "ST"]
        caste_objs = [CasteMaster(caste_master_name=c) for c in castes_list]
        for c in caste_objs:
            db.add(c)
        db.flush()

        # Seed Acts and Sections
        ipc_act = Act(ActCode="IPC", ActDescription="Indian Penal Code, 1860", ShortName="IPC", Active=True)
        ndps_act = Act(ActCode="NDPS", ActDescription="Narcotic Drugs and Psychotropic Substances Act, 1985", ShortName="NDPS", Active=True)
        ita_act = Act(ActCode="ITA", ActDescription="Information Technology Act, 2000", ShortName="ITA", Active=True)
        db.add(ipc_act)
        db.add(ndps_act)
        db.add(ita_act)
        db.flush()

        sections_list = [
            ("IPC", "379", "Theft"),
            ("IPC", "356", "Assault or criminal force in attempt to commit theft of property worn by a person"),
            ("IPC", "380", "Theft in dwelling house, etc."),
            ("IPC", "392", "Punishment for robbery"),
            ("IPC", "457", "Lurking house-trespass or house-breaking by night in order to commit offence punishable with imprisonment"),
            ("IPC", "302", "Punishment for murder"),
            ("IPC", "324", "Voluntarily causing hurt by dangerous weapons or means"),
            ("NDPS", "20", "Punishment for contravention in relation to cannabis plant and cannabis"),
            ("ITA", "66D", "Punishment for cheating by personation by using computer resource"),
            ("IPC", "420", "Cheating and dishonestly inducing delivery of property"),
            ("IPC", "354", "Assault or criminal force to woman with intent to outrage her modesty"),
            ("IPC", "147", "Punishment for rioting"),
        ]
        sec_map = {}
        for act_code, code, desc in sections_list:
            sec = Section(ActCode=act_code, SectionCode=code, SectionDescription=desc, Active=True)
            db.add(sec)
            sec_map[f"{act_code}-{code}"] = sec
        db.flush()

        # Link Crime Heads to Acts and Sections
        ch_act_sec = [
            (sub_heads["chain_snatching"][0], "IPC", "356"),
            (sub_heads["chain_snatching"][0], "IPC", "379"),
            (sub_heads["burglary"][0], "IPC", "380"),
            (sub_heads["burglary"][0], "IPC", "457"),
            (sub_heads["robbery"][0], "IPC", "392"),
            (sub_heads["murder"][0], "IPC", "302"),
            (sub_heads["assault"][0], "IPC", "324"),
            (sub_heads["drug_offense"][0], "NDPS", "20"),
            (sub_heads["cybercrime"][0], "ITA", "66D"),
            (sub_heads["fraud"][0], "IPC", "420"),
            (sub_heads["women_crime"][0], "IPC", "354"),
            (sub_heads["rioting"][0], "IPC", "147"),
        ]
        for ch_id, act_code, sec_code in ch_act_sec:
            link = CrimeHeadActSection(CrimeHeadID=ch_id, ActCode=act_code, SectionCode=sec_code)
            db.add(link)
        db.flush()

        # 3. Seed Locations (10 unique entries)
        print("Seeding locations...")
        locations_data = [
            {"name": "Indiranagar 100ft Rd", "lat": 12.9719, "lng": 77.6412, "district": "Bengaluru East", "station_area": "Indiranagar Police Station", "dist_obj": bengaluru_east},
            {"name": "Whitefield ITPL Area", "lat": 12.9698, "lng": 77.7499, "district": "Bengaluru East", "station_area": "Whitefield Police Station", "dist_obj": bengaluru_east},
            {"name": "Koramangala 5th Block", "lat": 12.9352, "lng": 77.6244, "district": "Bengaluru South", "station_area": "Koramangala Police Station", "dist_obj": bengaluru_south},
            {"name": "Jayanagar 4th Block", "lat": 12.9308, "lng": 77.5833, "district": "Bengaluru South", "station_area": "Jayanagar Police Station", "dist_obj": bengaluru_south},
            {"name": "HSR Layout Sector 2", "lat": 12.9103, "lng": 77.6450, "district": "Bengaluru South", "station_area": "HSR Layout Police Station", "dist_obj": bengaluru_south},
            {"name": "Malleshwaram 15th Cross", "lat": 12.9982, "lng": 77.5684, "district": "Bengaluru North", "station_area": "Malleshwaram Police Station", "dist_obj": bengaluru_north},
            {"name": "Yelahanka New Town", "lat": 13.1007, "lng": 77.5963, "district": "Bengaluru North", "station_area": "Yelahanka Police Station", "dist_obj": bengaluru_north},
            {"name": "Electronic City Phase 1", "lat": 12.8452, "lng": 77.6754, "district": "Bengaluru South", "station_area": "Electronic City Police Station", "dist_obj": bengaluru_south},
            {"name": "MG Road Metro Junction", "lat": 12.9738, "lng": 77.6119, "district": "Bengaluru Central", "station_area": "Cubbon Park Police Station", "dist_obj": bengaluru_central},
            {"name": "Hebbal Flyover Junction", "lat": 13.0359, "lng": 77.5970, "district": "Bengaluru North", "station_area": "Hebbal Police Station", "dist_obj": bengaluru_north}
        ]
        locations = []
        units_map = {}
        for loc in locations_data:
            existing = db.query(Location).filter_by(name=loc["name"]).first()
            if not existing:
                l = Location(name=loc["name"], lat=loc["lat"], lng=loc["lng"], district=loc["district"], station_area=loc["station_area"])
                db.add(l)
                db.flush()
                locations.append(l)
            else:
                locations.append(existing)
            
            # Create Unit representing the police station
            unit_name = loc["station_area"]
            existing_unit = db.query(Unit).filter_by(UnitName=unit_name).first()
            if not existing_unit:
                unit = Unit(
                    UnitName=unit_name,
                    TypeID=ut_station.UnitTypeID,
                    StateID=karnataka.StateID,
                    DistrictID=loc["dist_obj"].DistrictID,
                    Active=True
                )
                db.add(unit)
                db.flush()
                units_map[unit_name] = unit
            else:
                units_map[unit_name] = existing_unit
        db.commit()

        # 4. Seed Officers / Employees
        print("Seeding officers and employees...")
        officer_ranks = ["Police Sub-Inspector", "Inspector of Police", "Assistant Commissioner of Police"]
        officers = []
        employees = []
        for idx, loc in enumerate(locations):
            name = f"Officer {fake.first_name_male()} {fake.last_name()}"
            rank_name = officer_ranks[idx % len(officer_ranks)]
            station = loc.station_area
            
            existing = db.query(Officer).filter_by(name=name).first()
            if not existing:
                o = Officer(name=name, rank=rank_name, station=station)
                db.add(o)
                db.flush()
                officers.append(o)
            else:
                officers.append(existing)

            # Match rank model
            rank_obj = db.query(Rank).filter_by(RankName=rank_name).first() or rank_psi
            unit_obj = units_map[station]
            
            emp = Employee(
                DistrictID=unit_obj.DistrictID,
                UnitID=unit_obj.UnitID,
                RankID=rank_obj.RankID,
                DesignationID=des_io.DesignationID,
                KGID=f"KGID2026{idx+1000:04d}",
                FirstName=name,
                EmployeeDOB=datetime(1975 + (idx % 15), 1 + (idx % 11), 1 + (idx % 25)),
                GenderID=1,
                BloodGroupID=1,
                AppointmentDate=datetime(2005 + (idx % 10), 1, 15)
            )
            db.add(emp)
            db.flush()
            employees.append(emp)
        db.commit()

        # 5. Seed Accused (75 unique)
        print("Seeding accused...")
        accused_list = []
        for i in range(75):
            name = f"{fake.first_name_male()} {fake.last_name()}"
            age = random.randint(19, 55)
            gender_name = "Male" if random.random() < 0.95 else "Female"
            occupation = random.choice(occupations_list)
            address = f"{fake.building_number()}, {fake.street_name()}, {random.choice(locations_data)['name']}, Bengaluru"
            a = Accused(
                name=name,
                age=age,
                gender=gender_name,
                occupation=occupation,
                address=address,
                risk_score=0.0,
                
                AccusedMasterID=i+1,
                AccusedName=name,
                AgeYear=age,
                GenderID=1 if gender_name == "Male" else 2,
                PersonID=f"A{random.randint(1, 4)}"
            )
            db.add(a)
            db.flush()
            a.AccusedMasterID = a.accused_id
            accused_list.append(a)
        db.commit()

        # Create distinct gangs
        gangs = []
        for g in range(6):
            gang_size = random.randint(3, 5)
            gang_members = random.sample(accused_list, gang_size)
            gangs.append(gang_members)

        # 6. Generate 5800 FIRs (Jan 2023 -> June 7, 2026)
        print("Generating 5800 FIR / CaseMaster records...")
        crime_types = [
            "burglary", "vehicle_theft", "robbery", "chain_snatching",
            "cybercrime", "assault", "fraud", "women_crime", "drug_offense",
            "murder", "rioting"
        ]
        crime_weights = [
            0.15, 0.15, 0.08, 0.07,
            0.12, 0.18, 0.10, 0.07, 0.04,
            0.02, 0.02
        ]
        statuses = ["Open", "Under Investigation", "Chargesheet Filed", "Closed"]
        
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2026, 6, 7) # Current Date
        total_days = (end_date - start_date).days

        firs_seeded = 0
        while firs_seeded < 5800:
            random_days = random.randint(0, total_days)
            fir_datetime = start_date + timedelta(days=random_days)
            
            # Apply seasonal and festival/weekend spikes
            multiplier = 1.0
            if fir_datetime.weekday() >= 4: # Weekend spike
                multiplier *= 1.4
                
            month = fir_datetime.month
            if month in [3, 4, 5]: # Summer spike
                multiplier *= 1.3
            elif month in [11, 12]: # Winter spike
                multiplier *= 1.2
            elif month in [7, 8]: # Monsoon dip
                multiplier *= 0.7
                
            day_of_year = fir_datetime.timetuple().tm_yday
            if 283 <= day_of_year <= 293: # Dussehra
                multiplier *= 1.8
            elif 309 <= day_of_year <= 319: # Diwali
                multiplier *= 1.8
            elif day_of_year >= 362 or day_of_year <= 3: # New Year
                multiplier *= 2.0
                
            if random.random() > (multiplier / 2.0):
                continue # Skip to maintain spatiotemporal distribution
            
            crime_key = random.choices(crime_types, weights=crime_weights)[0]
            location = random.choice(locations)
            
            # Officer workload imbalance (20% of officers handle 50% of cases)
            if random.random() < 0.5:
                officer = random.choice(officers[:2])
            else:
                officer = random.choice(officers[2:])
                
            emp = random.choice(employees)
            sh_obj = crime_subheads_map[crime_key]
            
            desc = f"Incident of {crime_key.replace('_', ' ')} reported at {location.name}. " \
                   f"The reporting officer {officer.name} proceeded to the spot for investigation. " \
                   f"Complainant reported crime events by suspects. " \
                   f"Witnesses statement recorded."

            fir_num = f"FIR-{fir_datetime.year}-{firs_seeded+1:05d}"
            crime_no = f"10443{emp.DistrictID:02d}{emp.UnitID:02d}{fir_datetime.year}{firs_seeded+1:05d}"
            case_no = f"{fir_datetime.year}{firs_seeded+1:05d}"
            
            status_name = random.choice(statuses)
            status_obj = db.query(CaseStatusMaster).filter_by(CaseStatusName=status_name).first()
            assigned_court = court_1 if random.random() < 0.7 else court_2

            fir = FIR(
                fir_number=fir_num,
                date=fir_datetime.strftime("%Y-%m-%d"),
                crime_type=crime_key,
                description=desc,
                status=status_name,
                location_id=location.location_id,
                officer_id=officer.officer_id,
                
                # New CaseMaster Columns
                CrimeNo=crime_no,
                CaseNo=case_no,
                CrimeRegisteredDate=fir_datetime.date(),
                PolicePersonID=emp.EmployeeID,
                PoliceStationID=emp.UnitID,
                CaseCategoryID=cat_fir.CaseCategoryID,
                GravityOffenceID=gravity_heinous.GravityOffenceID if crime_key in ["murder", "robbery", "women_crime"] else gravity_non_heinous.GravityOffenceID,
                CrimeMajorHeadID=sh_obj.CrimeHeadID,
                CrimeMinorHeadID=sh_obj.CrimeSubHeadID,
                CaseStatusID=status_obj.CaseStatusID if status_obj else status_investigating.CaseStatusID,
                CourtID=assigned_court.CourtID,
                IncidentFromDate=fir_datetime,
                latitude=location.lat,
                longitude=location.lng,
                BriefFacts=desc,
                is_deleted=False,
                version_no=1
            )
            db.add(fir)
            db.flush() # get fir.fir_id

            fir.CaseMasterID = fir.fir_id

            # Seed ComplainantDetails
            comp = ComplainantDetails(
                CaseMasterID=fir.fir_id,
                ComplainantName=fake.name(),
                AgeYear=random.randint(22, 65),
                OccupationID=occ_map[random.choice(occupations_list)].OccupationID,
                ReligionID=1,
                CasteID=1,
                GenderID=random.choice([1, 2])
            )
            db.add(comp)

            # Seed victims (1-2)
            for v_idx in range(random.randint(1, 2)):
                vic_name = fake.name()
                vic_age = random.randint(18, 70)
                vic_gender = random.choice(["Male", "Female"])
                vic = Victim(
                    fir_id=fir.fir_id,
                    name=vic_name,
                    age=vic_age,
                    gender=vic_gender,
                    
                    VictimMasterID=v_idx+1,
                    CaseMasterID=fir.fir_id,
                    VictimName=vic_name,
                    AgeYear=vic_age,
                    GenderID=1 if vic_gender == "Male" else 2,
                    VictimPolice="0"
                )
                db.add(vic)

            # Map accused.
            prob = random.random()
            assigned_accused = []
            if prob < 0.05:
                # Select a gang (from persistent pool)
                gang = random.choice(gangs)
                assigned_accused = list(gang)
            elif prob < 0.20:
                # Single/Multiple persistent accused
                assigned_accused = random.sample(accused_list, random.randint(1, 2))
            else:
                # 80% chance: unique first-time accused
                fresh_name = f"{fake.first_name_male()} {fake.last_name()}"
                fresh_age = random.randint(18, 55)
                fresh_gender = "Male" if random.random() < 0.9 else "Female"
                fresh_occ = random.choice(occupations_list)
                fresh_addr = fake.address().replace("\n", ", ")
                fresh_acc = Accused(
                    name=fresh_name,
                    age=fresh_age,
                    gender=fresh_gender,
                    occupation=fresh_occ,
                    address=fresh_addr,
                    risk_score=0.0,
                    AccusedName=fresh_name,
                    AgeYear=fresh_age,
                    GenderID=1 if fresh_gender == "Male" else 2,
                    PersonID=f"KP-{random.randint(100000, 999999)}"
                )
                db.add(fresh_acc)
                db.flush()
                assigned_accused = [fresh_acc]

            for idx, acc in enumerate(assigned_accused):
                role = "Principal" if idx == 0 else random.choice(["Co-accused", "Conspirator", "Suspect"])
                fa = FIRAccused(
                    fir_id=fir.fir_id,
                    accused_id=acc.accused_id,
                    role=role
                )
                db.add(fa)
                
                acc.CaseMasterID = fir.fir_id
                db.add(acc)
                
                # Seed ArrestSurrender if status is Closed or Chargesheet Filed
                if status_name in ["Closed", "Chargesheet Filed"] and random.random() < 0.8:
                    arr = ArrestSurrender(
                        CaseMasterID=fir.fir_id,
                        ArrestSurrenderTypeID=1,
                        ArrestSurrenderDate=(fir_datetime + timedelta(days=random.randint(2, 30))).date(),
                        ArrestSurrenderStateId=karnataka.StateID,
                        ArrestSurrenderDistrictId=emp.DistrictID,
                        PoliceStationID=emp.UnitID,
                        IOID=emp.EmployeeID,
                        CourtID=assigned_court.CourtID,
                        AccusedMasterID=acc.accused_id,
                        IsAccused=True,
                        IsComplainantAccused=False
                    )
                    db.add(arr)

            # Seed Acts and Sections
            if crime_key == "chain_snatching":
                db.add(ActSectionAssociation(CaseMasterID=fir.fir_id, ActID="IPC", SectionID="356", ActOrderID=1, SectionOrderID=1))
                db.add(ActSectionAssociation(CaseMasterID=fir.fir_id, ActID="IPC", SectionID="379", ActOrderID=1, SectionOrderID=2))
            elif crime_key == "burglary":
                db.add(ActSectionAssociation(CaseMasterID=fir.fir_id, ActID="IPC", SectionID="380", ActOrderID=1, SectionOrderID=1))
                db.add(ActSectionAssociation(CaseMasterID=fir.fir_id, ActID="IPC", SectionID="457", ActOrderID=1, SectionOrderID=2))
            elif crime_key == "robbery":
                db.add(ActSectionAssociation(CaseMasterID=fir.fir_id, ActID="IPC", SectionID="392", ActOrderID=1, SectionOrderID=1))
            elif crime_key == "murder":
                db.add(ActSectionAssociation(CaseMasterID=fir.fir_id, ActID="IPC", SectionID="302", ActOrderID=1, SectionOrderID=1))
            elif crime_key == "assault":
                db.add(ActSectionAssociation(CaseMasterID=fir.fir_id, ActID="IPC", SectionID="324", ActOrderID=1, SectionOrderID=1))
            elif crime_key == "drug_offense":
                db.add(ActSectionAssociation(CaseMasterID=fir.fir_id, ActID="NDPS", SectionID="20", ActOrderID=1, SectionOrderID=1))
            elif crime_key == "cybercrime":
                db.add(ActSectionAssociation(CaseMasterID=fir.fir_id, ActID="ITA", SectionID="66D", ActOrderID=1, SectionOrderID=1))
            elif crime_key == "fraud":
                db.add(ActSectionAssociation(CaseMasterID=fir.fir_id, ActID="IPC", SectionID="420", ActOrderID=1, SectionOrderID=1))
            elif crime_key == "women_crime":
                db.add(ActSectionAssociation(CaseMasterID=fir.fir_id, ActID="IPC", SectionID="354", ActOrderID=1, SectionOrderID=1))
            elif crime_key == "rioting":
                db.add(ActSectionAssociation(CaseMasterID=fir.fir_id, ActID="IPC", SectionID="147", ActOrderID=1, SectionOrderID=1))

            # Seed ChargesheetDetails if status is Chargesheet Filed
            if status_name == "Chargesheet Filed":
                is_heinous = crime_key in ["murder", "robbery", "women_crime"]
                delay_days = 30
                if is_heinous:
                    delay_days += 45
                delay_days += (emp.EmployeeID % 5) * 15
                delay_days += (assigned_court.CourtID % 3) * 20
                delay_days += random.randint(-5, 5)
                cs = ChargesheetDetails(
                    CaseMasterID=fir.fir_id,
                    csdate=fir_datetime + timedelta(days=max(5, delay_days)),
                    cstype="A",
                    PolicePersonID=emp.EmployeeID
                )
                db.add(cs)

            firs_seeded += 1

        # 7. INJECT 7-DAY SPIKE IN WHITEFIELD TO TRIGGER EARLY WARNING
        print("Injecting 7-day crime spike in Whitefield...")
        whitefield_loc = db.query(Location).filter_by(name="Whitefield ITPL Area").first()
        whitefield_officer = db.query(Officer).first()
        whitefield_emp = db.query(Employee).first()
        
        for i in range(10):
            fir_date = datetime(2026, 6, random.randint(1, 7))
            crime_key = random.choice(["chain_snatching", "burglary"])
            fir_num = f"FIR-2026-SPIKE{i+1:02d}"
            desc = f"Spike Crime Alert: Incident of {crime_key.replace('_', ' ')} near Whitefield ITPL Area. " \
                   f"Victim targeted during late night hours. Investigation taken up immediately."
            
            sh_obj = crime_subheads_map[crime_key]
            status_obj = db.query(CaseStatusMaster).filter_by(CaseStatusName="Open").first()

            fir = FIR(
                fir_number=fir_num,
                date=fir_date.strftime("%Y-%m-%d"),
                crime_type=crime_key,
                description=desc,
                status="Open",
                location_id=whitefield_loc.location_id,
                officer_id=whitefield_officer.officer_id,
                
                # New CaseMaster Columns
                CrimeNo=f"10443{whitefield_emp.DistrictID:02d}{whitefield_emp.UnitID:02d}2026SPIKE{i+1:02d}",
                CaseNo=f"2026SPIKE{i+1:02d}",
                CrimeRegisteredDate=fir_date.date(),
                PolicePersonID=whitefield_emp.EmployeeID,
                PoliceStationID=whitefield_emp.UnitID,
                CaseCategoryID=cat_fir.CaseCategoryID,
                GravityOffenceID=gravity_non_heinous.GravityOffenceID,
                CrimeMajorHeadID=sh_obj.CrimeHeadID,
                CrimeMinorHeadID=sh_obj.CrimeSubHeadID,
                CaseStatusID=status_obj.CaseStatusID if status_obj else status_open.CaseStatusID,
                CourtID=court_1.CourtID,
                IncidentFromDate=fir_date,
                latitude=whitefield_loc.lat,
                longitude=whitefield_loc.lng,
                BriefFacts=desc,
                is_deleted=False,
                version_no=1
            )
            db.add(fir)
            db.flush()
            
            fir.CaseMasterID = fir.fir_id

            # Seed victims (1)
            vic = Victim(
                fir_id=fir.fir_id,
                name=fake.name(),
                age=random.randint(20, 60),
                gender=random.choice(["Male", "Female"]),
                CaseMasterID=fir.fir_id,
                VictimName=fake.name(),
                AgeYear=random.randint(20, 60),
                GenderID=1,
                VictimPolice="0"
            )
            db.add(vic)

            # Assign some gang members to these spikes to strengthen connections
            active_gang = gangs[i % 2]
            for idx, acc in enumerate(active_gang):
                role = "Principal" if idx == 0 else "Co-accused"
                fa = FIRAccused(fir_id=fir.fir_id, accused_id=acc.accused_id, role=role)
                db.add(fa)

        # 8. Inject specific Rajesh Kumar accused & crime network to satisfy tests
        print("Injecting Rajesh Kumar specific accused record & criminal network...")
        rajesh = Accused(
            name="Rajesh Kumar",
            age=31,
            gender="Male",
            occupation="Driver",
            address="12, 5th Cross, Indiranagar, Bengaluru",
            risk_score=0.0,
            
            AccusedMasterID=999,
            AccusedName="Rajesh Kumar",
            AgeYear=31,
            GenderID=1,
            PersonID="A1"
        )
        db.add(rajesh)
        db.flush()
        rajesh.AccusedMasterID = rajesh.accused_id

        indiranagar_loc = db.query(Location).filter(Location.name.like("%Indiranagar%")).first()
        whitefield_loc = db.query(Location).filter(Location.name.like("%Whitefield%")).first()
        koramangala_loc = db.query(Location).filter(Location.name.like("%Koramangala%")).first()
        
        # Grab co-accused
        co_accused_1 = accused_list[0]
        co_accused_2 = accused_list[1]
        co_accused_3 = accused_list[2]
        
        rajesh_cases = [
            {
                "fir_number": "FIR-2025-09901",
                "date": "2025-05-12",
                "crime_type": "chain_snatching",
                "description": "Chain snatching incident involving Rajesh Kumar and accomplice near Indiranagar.",
                "location_id": indiranagar_loc.location_id,
                "co_accused": [co_accused_1]
            },
            {
                "fir_number": "FIR-2025-09902",
                "date": "2025-08-20",
                "crime_type": "burglary",
                "description": "House burglary reported at Whitefield. Rajesh Kumar and co-accused seen escaping in a vehicle.",
                "location_id": whitefield_loc.location_id,
                "co_accused": [co_accused_2, co_accused_3]
            },
            {
                "fir_number": "FIR-2026-09903",
                "date": "2026-02-14",
                "crime_type": "robbery",
                "description": "Highway robbery reported on Koramangala road. Accused Rajesh Kumar and associate intercepted the victim.",
                "location_id": koramangala_loc.location_id,
                "co_accused": [co_accused_1, co_accused_3]
            }
        ]
        
        status_inv_obj = db.query(CaseStatusMaster).filter_by(CaseStatusName="Under Investigation").first()
        for i, case_data in enumerate(rajesh_cases):
            sh_obj = crime_subheads_map[case_data["crime_type"]]
            emp = employees[i % len(employees)]
            loc_obj = db.query(Location).filter_by(location_id=case_data["location_id"]).first()
            
            fir = FIR(
                fir_number=case_data["fir_number"],
                date=case_data["date"],
                crime_type=case_data["crime_type"],
                description=case_data["description"],
                status="Under Investigation",
                location_id=case_data["location_id"],
                officer_id=officers[0].officer_id,
                
                # CaseMaster fields
                CrimeNo=f"10443{emp.DistrictID:02d}{emp.UnitID:02d}2025RAJESH{i:02d}",
                CaseNo=f"2025RAJESH{i:02d}",
                CrimeRegisteredDate=datetime.strptime(case_data["date"], "%Y-%m-%d").date(),
                PolicePersonID=emp.EmployeeID,
                PoliceStationID=emp.UnitID,
                CaseCategoryID=cat_fir.CaseCategoryID,
                GravityOffenceID=gravity_heinous.GravityOffenceID if case_data["crime_type"] in ["robbery"] else gravity_non_heinous.GravityOffenceID,
                CrimeMajorHeadID=sh_obj.CrimeHeadID,
                CrimeMinorHeadID=sh_obj.CrimeSubHeadID,
                CaseStatusID=status_inv_obj.CaseStatusID if status_inv_obj else status_investigating.CaseStatusID,
                CourtID=court_1.CourtID,
                IncidentFromDate=datetime.strptime(case_data["date"], "%Y-%m-%d"),
                latitude=loc_obj.lat if loc_obj else 12.97,
                longitude=loc_obj.lng if loc_obj else 77.6,
                BriefFacts=case_data["description"],
                is_deleted=False,
                version_no=1
            )
            db.add(fir)
            db.flush()
            
            fir.CaseMasterID = fir.fir_id

            # Seed victims (1)
            vic = Victim(
                fir_id=fir.fir_id,
                name=fake.name(),
                age=random.randint(22, 50),
                gender=random.choice(["Male", "Female"]),
                CaseMasterID=fir.fir_id,
                VictimName=fake.name(),
                AgeYear=random.randint(22, 50),
                GenderID=1,
                VictimPolice="0"
            )
            db.add(vic)
            
            # Map Rajesh (Principal)
            fa_rajesh = FIRAccused(fir_id=fir.fir_id, accused_id=rajesh.accused_id, role="Principal")
            db.add(fa_rajesh)
            
            # Map co-accused
            for ca in case_data["co_accused"]:
                fa_ca = FIRAccused(fir_id=fir.fir_id, accused_id=ca.accused_id, role="Co-accused")
                db.add(fa_ca)
                
        db.commit()

        # 9. UPDATE ACCUSED RISK SCORES
        print("Calculating and updating accused risk scores...")
        all_accused = db.query(Accused).all()
        for acc in all_accused:
            records = db.query(FIR).join(FIRAccused).filter(FIRAccused.accused_id == acc.accused_id).all()
            if not records:
                acc.risk_score = 0.0
            else:
                crime_count = len(records)
                severity_sum = sum(CRIME_SEVERITY.get(r.crime_type, 1) for r in records)
                acc.risk_score = round(float(crime_count * 1.5 + severity_sum * 0.5), 2)
            db.add(acc)
        db.commit()

        print("Database seeding completed successfully.")
        
        # Verify counts
        print("Verification statistics:")
        print(f"Users: {db.query(User).count()}")
        print(f"Locations: {db.query(Location).count()}")
        print(f"Officers: {db.query(Officer).count()}")
        print(f"Employees: {db.query(Employee).count()}")
        print(f"Accused: {db.query(Accused).count()}")
        print(f"FIRs: {db.query(FIR).count()}")
        print(f"Victims: {db.query(Victim).count()}")

    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    init_db_from_schema()
    seed_data()
