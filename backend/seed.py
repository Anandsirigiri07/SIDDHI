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
from backend.models import User, Location, Officer, Accused, FIR, FIRAccused, Victim
from backend.config.crime_weights import CRIME_SEVERITY

fake = Faker('en_IN') # Indian localized names/addresses

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def init_db_from_schema():
    # Remove old SQLite file if it exists to refresh schema cleanly
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
            demo_password = os.getenv("DEMO_USER_PASSWORD")
            if not demo_password:
                demo_password = secrets.token_urlsafe(12)
                print(f"Generated demo user password (shown once, not stored): {demo_password}")
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
        else:
            print("Skipping demo users. Set SEED_DEMO_USERS=true to create them (local development only).")

        # 2. Seed Locations
        print("Seeding locations...")
        locations_data = [
            {"name": "Indiranagar 100ft Rd", "lat": 12.9719, "lng": 77.6412, "district": "Bengaluru East", "station_area": "Indiranagar Police Station"},
            {"name": "Whitefield ITPL Area", "lat": 12.9698, "lng": 77.7499, "district": "Bengaluru East", "station_area": "Whitefield Police Station"},
            {"name": "Koramangala 5th Block", "lat": 12.9352, "lng": 77.6244, "district": "Bengaluru South", "station_area": "Koramangala Police Station"},
            {"name": "Jayanagar 4th Block", "lat": 12.9308, "lng": 77.5833, "district": "Bengaluru South", "station_area": "Jayanagar Police Station"},
            {"name": "HSR Layout Sector 2", "lat": 12.9103, "lng": 77.6450, "district": "Bengaluru South", "station_area": "HSR Layout Police Station"},
            {"name": "Malleshwaram 15th Cross", "lat": 12.9982, "lng": 77.5684, "district": "Bengaluru North", "station_area": "Malleshwaram Police Station"},
            {"name": "Yelahanka New Town", "lat": 13.1007, "lng": 77.5963, "district": "Bengaluru North", "station_area": "Yelahanka Police Station"},
            {"name": "Electronic City Phase 1", "lat": 12.8452, "lng": 77.6754, "district": "Bengaluru South", "station_area": "Electronic City Police Station"},
            {"name": "MG Road Metro Junction", "lat": 12.9738, "lng": 77.6119, "district": "Bengaluru Central", "station_area": "Cubbon Park Police Station"},
            {"name": "Hebbal Flyover Junction", "lat": 13.0359, "lng": 77.5970, "district": "Bengaluru North", "station_area": "Hebbal Police Station"}
        ]
        locations = []
        for loc in locations_data:
            existing = db.query(Location).filter_by(name=loc["name"]).first()
            if not existing:
                l = Location(**loc)
                db.add(l)
                locations.append(l)
            else:
                locations.append(existing)
        db.commit()

        # 3. Seed Officers
        print("Seeding officers...")
        officer_ranks = ["Police Sub-Inspector", "Inspector of Police", "Assistant Commissioner of Police"]
        officers = []
        for idx, loc in enumerate(locations):
            name = f"Officer {fake.first_name_male()} {fake.last_name()}"
            rank = officer_ranks[idx % len(officer_ranks)]
            station = loc.station_area
            existing = db.query(Officer).filter_by(name=name).first()
            if not existing:
                o = Officer(name=name, rank=rank, station=station)
                db.add(o)
                officers.append(o)
            else:
                officers.append(existing)
        db.commit()

        # 4. Seed Accused (75 unique)
        print("Seeding accused...")
        accused_list = []
        occupations = ["Laborer", "Driver", "Delivery Executive", "Unemployed", "Security Guard", "Mechanic", "Local Merchant", "Real Estate Broker"]
        for i in range(75):
            name = f"{fake.first_name_male()} {fake.last_name()}"
            age = random.randint(19, 55)
            gender = "Male" if random.random() < 0.95 else "Female"
            occupation = random.choice(occupations)
            address = f"{fake.building_number()}, {fake.street_name()}, {random.choice(locations_data)['name']}, Bengaluru"
            a = Accused(name=name, age=age, gender=gender, occupation=occupation, address=address, risk_score=0.0)
            db.add(a)
            accused_list.append(a)
        db.commit()

        # Create distinct "Gangs" or co-offender groupings to form rich criminal networks
        # Let's say we have 6 gangs that tend to commit crimes together.
        gangs = []
        for g in range(6):
            gang_size = random.randint(3, 5)
            gang_members = random.sample(accused_list, gang_size)
            gangs.append(gang_members)

        # 5. Generate 500 FIRs (Jan 2023 -> June 7, 2026)
        print("Generating 500 FIR records...")
        crime_types = list(CRIME_SEVERITY.keys())
        statuses = ["Open", "Under Investigation", "Chargesheet Filed", "Closed"]
        
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2026, 6, 7) # Current Date
        total_days = (end_date - start_date).days

        # Let's create specific seasonal variations. Spikes in March-May (summer) and Nov-Dec.
        # We will distribute 490 crimes over the date range first
        firs_seeded = 0
        while firs_seeded < 490:
            random_days = random.randint(0, total_days)
            fir_datetime = start_date + timedelta(days=random_days)
            
            # Apply seasonal weighting
            month = fir_datetime.month
            weight = 1.0
            if month in [3, 4, 5]: # Summer spike
                weight = 1.3
            elif month in [11, 12]: # Winter spike
                weight = 1.2
            elif month in [7, 8]: # Monsoon dip
                weight = 0.7
                
            if random.random() > weight:
                continue # Skip to maintain weights
            
            crime_type = random.choice(crime_types)
            location = random.choice(locations)
            officer = random.choice(officers)
            
            # Formulate description
            desc = f"Incident of {crime_type.replace('_', ' ')} reported at {location.name}. " \
                   f"The reporting officer {officer.name} proceeded to the spot for investigation. " \
                   f"Complainant reported theft/damage/assault by unidentified individuals. " \
                   f"Witnesses statement recorded."

            fir_num = f"FIR-{fir_datetime.year}-{firs_seeded+1:05d}"
            fir = FIR(
                fir_number=fir_num,
                date=fir_datetime.strftime("%Y-%m-%d"),
                crime_type=crime_type,
                description=desc,
                status=random.choice(statuses),
                location_id=location.location_id,
                officer_id=officer.officer_id
            )
            db.add(fir)
            db.flush() # flush to get fir_id

            # Seed victims (1-2)
            for _ in range(random.randint(1, 2)):
                vic = Victim(
                    fir_id=fir.fir_id,
                    name=fake.name(),
                    age=random.randint(18, 70),
                    gender=random.choice(["Male", "Female"])
                )
                db.add(vic)

            # Map accused.
            # 30% chance it's committed by a gang.
            # 50% chance it's a random single accused.
            # 20% chance it's 2-3 random accused.
            prob = random.random()
            assigned_accused = []
            if prob < 0.3:
                # Select a gang
                gang = random.choice(gangs)
                assigned_accused = list(gang)
            elif prob < 0.8:
                # Single random accused
                assigned_accused = [random.choice(accused_list)]
            else:
                # 2-3 random accused
                assigned_accused = random.sample(accused_list, random.randint(2, 3))

            for idx, acc in enumerate(assigned_accused):
                role = "Principal" if idx == 0 else random.choice(["Co-accused", "Conspirator", "Suspect"])
                fa = FIRAccused(
                    fir_id=fir.fir_id,
                    accused_id=acc.accused_id,
                    role=role
                )
                db.add(fa)

            firs_seeded += 1

        # 6. INJECT 7-DAY SPIKE IN WHITEFIELD TO TRIGGER EARLY WARNING
        # Current Date: June 7, 2026. Last 7 days: June 1 -> June 7.
        # We will inject 10 burglaries/chain snatchings in Whitefield ITPL Area during this week.
        print("Injecting 7-day crime spike in Whitefield...")
        whitefield_loc = db.query(Location).filter_by(name="Whitefield ITPL Area").first()
        whitefield_officer = db.query(Officer).first()
        
        for i in range(10):
            fir_date = datetime(2026, 6, random.randint(1, 7))
            crime_type = random.choice(["chain_snatching", "burglary"])
            fir_num = f"FIR-2026-SPIKE{i+1:02d}"
            desc = f"Spike Crime Alert: Incident of {crime_type.replace('_', ' ')} near Whitefield ITPL Area. " \
                   f"Victim targeted during late night hours. Investigation taken up immediately."
            
            fir = FIR(
                fir_number=fir_num,
                date=fir_date.strftime("%Y-%m-%d"),
                crime_type=crime_type,
                description=desc,
                status="Open",
                location_id=whitefield_loc.location_id,
                officer_id=whitefield_officer.officer_id
            )
            db.add(fir)
            db.flush()

            # Add victims
            vic = Victim(fir_id=fir.fir_id, name=fake.name(), age=random.randint(20, 60), gender=random.choice(["Male", "Female"]))
            db.add(vic)

            # Assign some of our gang members to these spikes to strengthen connections
            # Gang 0 and Gang 1 active in Whitefield spike
            active_gang = gangs[i % 2]
            for idx, acc in enumerate(active_gang):
                role = "Principal" if idx == 0 else "Co-accused"
                fa = FIRAccused(fir_id=fir.fir_id, accused_id=acc.accused_id, role=role)
                db.add(fa)

        db.commit()

        # Inject specific Rajesh Kumar accused & crime network to satisfy requirements
        print("Injecting Rajesh Kumar specific accused record & criminal network...")
        rajesh = Accused(
            name="Rajesh Kumar",
            age=31,
            gender="Male",
            occupation="Driver",
            address="12, 5th Cross, Indiranagar, Bengaluru",
            risk_score=0.0
        )
        db.add(rajesh)
        db.flush()

        indiranagar_loc = db.query(Location).filter(Location.name.like("%Indiranagar%")).first()
        whitefield_loc = db.query(Location).filter(Location.name.like("%Whitefield%")).first()
        koramangala_loc = db.query(Location).filter(Location.name.like("%Koramangala%")).first()
        
        # Grab co-accused from already seeded accused
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
        
        for case_data in rajesh_cases:
            fir = FIR(
                fir_number=case_data["fir_number"],
                date=case_data["date"],
                crime_type=case_data["crime_type"],
                description=case_data["description"],
                status="Under Investigation",
                location_id=case_data["location_id"],
                officer_id=officers[0].officer_id
            )
            db.add(fir)
            db.flush()
            
            # Seed victims (1)
            vic = Victim(fir_id=fir.fir_id, name=fake.name(), age=random.randint(22, 50), gender=random.choice(["Male", "Female"]))
            db.add(vic)
            
            # Map Rajesh (Principal)
            fa_rajesh = FIRAccused(fir_id=fir.fir_id, accused_id=rajesh.accused_id, role="Principal")
            db.add(fa_rajesh)
            
            # Map co-accused
            for ca in case_data["co_accused"]:
                fa_ca = FIRAccused(fir_id=fir.fir_id, accused_id=ca.accused_id, role="Co-accused")
                db.add(fa_ca)
                
        db.commit()


        # 7. UPDATE ACCUSED RISK SCORES
        # Risk score is based on number of crimes committed times severity
        print("Calculating and updating accused risk scores...")
        all_accused = db.query(Accused).all()
        for acc in all_accused:
            # Join fir_accused and firs
            records = db.query(FIR).join(FIRAccused).filter(FIRAccused.accused_id == acc.accused_id).all()
            if not records:
                acc.risk_score = 0.0
            else:
                crime_count = len(records)
                # Sum weights
                severity_sum = sum(CRIME_SEVERITY.get(r.crime_type, 1) for r in records)
                # Simple score for base display, can be customized
                acc.risk_score = round(float(crime_count * 1.5 + severity_sum * 0.5), 2)
            db.add(acc)
        db.commit()

        print("Database seeding completed successfully.")
        
        # Verify counts
        print("Verification statistics:")
        print(f"Users: {db.query(User).count()}")
        print(f"Locations: {db.query(Location).count()}")
        print(f"Officers: {db.query(Officer).count()}")
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
