import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date, timedelta
import random
import time

from app.main import app
from app.database import Base, get_db
from app.models import ConstraintType

# Test Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_stress.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

def test_stress_simulation():
    # 40 professors
    professors = []
    for i in range(40):
        p = client.post("/api/professors", json={"name": f"Prof {i}", "code": f"P{i:02d}"}).json()
        professors.append(p)
        
    # 6 locations
    locations = []
    for i in range(6):
        l = client.post("/api/locations", json={"name": f"Loc {i}"}).json()
        locations.append(l)
        
    # 60 day schedule
    start_date = date(2026, 4, 1)
    end_date = start_date + timedelta(days=59)
    setting = client.post("/api/settings", json={
        "start_date": str(start_date),
        "end_date": str(end_date),
        "locations_per_day": 6,
        "count_sundays": True
    }).json()
    
    # Random constraints for 30% of professors
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    for i in range(int(0.3 * 40)):
        p = professors[i]
        c_type = random.choice([ConstraintType.DAY_UNAVAILABLE, ConstraintType.LOCATION_RESTRICTED, ConstraintType.MAX_WEEKLY])
        if c_type == ConstraintType.DAY_UNAVAILABLE:
            client.post("/api/constraints", json={
                "professor_id": p["id"],
                "type": c_type,
                "value": {"dayOfWeek": random.choice(days_of_week)}
            })
        elif c_type == ConstraintType.LOCATION_RESTRICTED:
            client.post("/api/constraints", json={
                "professor_id": p["id"],
                "type": c_type,
                "value": {"location_id": random.choice(locations)["id"]}
            })
        elif c_type == ConstraintType.MAX_WEEKLY:
            client.post("/api/constraints", json={
                "professor_id": p["id"],
                "type": c_type,
                "value": {"limit": random.randint(3, 5)}
            })

    start_time = time.time()
    response = client.post(f"/api/generate-roster?setting_id={setting['id']}")
    end_time = time.time()
    
    assert response.status_code == 200
    duration = end_time - start_time
    print(f"Stress test solve time: {duration:.2f}s")
    assert duration < 5.0
    
    roster = client.get("/api/roster").json()
    # 60 days * 6 locations = 360 slots
    assert len(roster) == 360
    
    # Verify no duplicate assignments (same prof same day)
    prof_days = {}
    for entry in roster:
        key = (entry["professor_id"], entry["date"])
        assert key not in prof_days
        prof_days[key] = entry["location_id"]

def test_impossible_constraints():
    # All professors unavailable Monday
    p1 = client.post("/api/professors", json={"name": "P1", "code": "P1"}).json()
    p2 = client.post("/api/professors", json={"name": "P2", "code": "P2"}).json()
    l1 = client.post("/api/locations", json={"name": "L1"}).json()
    
    for p in [p1, p2]:
        client.post("/api/constraints", json={
            "professor_id": p["id"],
            "type": ConstraintType.DAY_UNAVAILABLE,
            "value": {"dayOfWeek": "Monday"}
        })
        
    # Monday to Monday (1 day)
    start_date = date(2026, 3, 2) # Monday
    setting = client.post("/api/settings", json={
        "start_date": str(start_date),
        "end_date": str(start_date),
        "locations_per_day": 1,
        "count_sundays": True
    }).json()
    
    response = client.post(f"/api/generate-roster?setting_id={setting['id']}")
    assert response.status_code == 400
    assert "No schedule can be found" in response.json()["detail"]

def test_too_few_professors():
    # 2 professors for 5 locations
    p1 = client.post("/api/professors", json={"name": "P1", "code": "P1"}).json()
    p2 = client.post("/api/professors", json={"name": "P2", "code": "P2"}).json()
    for i in range(5):
        client.post("/api/locations", json={"name": f"L{i}"})
        
    setting = client.post("/api/settings", json={
        "start_date": "2026-03-01",
        "end_date": "2026-03-01",
        "locations_per_day": 5,
        "count_sundays": True
    }).json()
    
    response = client.post(f"/api/generate-roster?setting_id={setting['id']}")
    assert response.status_code == 400
    # Solver enforces max 1 location per day per prof. 
    # 2 profs can only cover 2 locations. 5 are needed.

def test_delete_professor_after_generation():
    p1 = client.post("/api/professors", json={"name": "P1", "code": "P1"}).json()
    p2 = client.post("/api/professors", json={"name": "P2", "code": "P2"}).json()
    l1 = client.post("/api/locations", json={"name": "L1"}).json()
    setting = client.post("/api/settings", json={
        "start_date": "2026-03-01",
        "end_date": "2026-03-02",
        "locations_per_day": 1,
        "count_sundays": True
    }).json()
    
    client.post(f"/api/generate-roster?setting_id={setting['id']}")
    roster_before = client.get("/api/roster").json()
    assert len(roster_before) == 2
    
    # Delete P1
    client.delete(f"/api/professors/{p1['id']}")
    
    roster_after = client.get("/api/roster").json()
    # Check if assignments for P1 are gone (cascade delete in models.py)
    # Actually, RosterAssignment has professor_id as ForeignKey with cascade delete?
    # models.py: assignments = relationship("RosterAssignment", back_populates="professor", cascade="all, delete-orphan")
    # And Column(String, ForeignKey("professors.id"), nullable=False)
    
    # We need to see if assignments for P1 are removed.
    for entry in roster_after:
        assert entry["professor_id"] != p1["id"]
    
    # Total assignments should be less if P1 had some.
    # Note: The UI might need to re-generate the roster, but the DB should be consistent.
